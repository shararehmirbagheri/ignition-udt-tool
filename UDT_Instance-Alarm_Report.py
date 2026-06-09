# IMPORTS
import re
import time
import system

# CONFIGURATION
provider = "default"               # provider name (used as [default])

# Ask the user for the UDT name at runtime
try:
    udt_name = system.gui.inputBox("Enter the UDT name to search for:", "")
except Exception:
    try:
        udt_name = system.gui.prompt("Enter the UDT name to search for:", "")
    except Exception:
        udt_name = ""

if not udt_name:
    raise SystemExit("No UDT name entered.")


def sanitize_filename(value):
    """Create a safe CSV filename from the UDT name the user entered."""
    text = str(value or "").strip()
    text = text.replace("\\", "_")
    text = text.replace("/", "_")
    text = text.replace(":", "_")
    text = text.replace("*", "_")
    text = text.replace("?", "_")
    text = text.replace('"', "_")
    text = text.replace("<", "_")
    text = text.replace(">", "_")
    text = text.replace("|", "_")
    text = text.replace(" ", "_")
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "UDT"


output_path = "C:/Logs/%s_Alarm.csv" % sanitize_filename(udt_name)

results = []
scanned_count = 0
start_time = time.time()
MAX_RUNTIME_SECONDS = 60
HEARTBEAT_SECONDS = 5
MAX_ALARM_RECORDS = 1000
PATH_BATCH_SIZE = 15
last_heartbeat = start_time


def log_progress(message):
    """Print a heartbeat message so the user knows the script is still running."""
    print("[progress] %s" % message)


def check_timeout(stage):
    if time.time() - start_time > MAX_RUNTIME_SECONDS:
        raise SystemExit("Timeout: script exceeded 1 minute during %s." % stage)


def safe_get(obj, key, default=""):
    """Read a property safely from either a Python dict or a Jython/Java map object."""
    try:
        return obj[key]
    except Exception:
        try:
            return getattr(obj, key)
        except Exception:
            try:
                return obj.get(key)
            except Exception:
                return default


def get_alarm_summary(alarm):
    """Return the alarm summary object when available."""
    summary = safe_get(alarm, 'alarmSummary', None)
    if isinstance(summary, dict):
        return summary
    if hasattr(summary, 'get'):
        try:
            return dict(summary)
        except Exception:
            return {}
    return {}


def alarm_identity(alarm):
    """Return a stable identifier so the same alarm is not counted twice."""
    for key in ('id', 'eventId', 'uuid', 'source', 'displayPath'):
        value = safe_get(alarm, key, '')
        if value:
            return str(value)
    summary = get_alarm_summary(alarm)
    for key in ('id', 'eventId', 'uuid', 'source', 'displayPath'):
        value = safe_get(summary, key, '')
        if value:
            return str(value)
    return str(id(alarm))


def friendly_priority(value):
    """Convert numeric or text priority values into friendly CSV labels."""
    text = str(value).strip()
    if not text:
        return ""

    priority_map = {
        "0": "Diagnostic",
        "1": "Low",
        "2": "Medium",
        "3": "High",
        "4": "Critical",
        "5": "Shelved",
        "diagnostic": "Diagnostic",
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical",
        "shelved": "Shelved",
    }

    return priority_map.get(text.lower(), text)


def friendly_state(value):
    """Return a readable state label matching the ASH2_alarms export format."""
    text = str(value).strip()
    if not text:
        return ""

    state_map = {
        "activeacked": "Active, Acknowledged",
        "activeunacked": "Active, Unacknowledged",
        "active acknowledged": "Active, Acknowledged",
        "active unacknowledged": "Active, Unacknowledged",
        "shelved": "Shelved",
        "cleared": "Cleared",
        "clear": "Cleared",
    }

    mapped = state_map.get(text.lower().replace("_", " "))
    if mapped:
        return mapped

    if "active" in text.lower() and "ack" in text.lower():
        if "unack" in text.lower():
            return "Active, Unacknowledged"
        return "Active, Acknowledged"

    return text


def format_active_time(value):
    """Format alarm active time like 06/09/2026 07:55:43."""
    if not value:
        return ""
    try:
        return system.date.format(value, "MM/dd/yyyy HH:mm:ss")
    except Exception:
        return str(value).strip()


def display_path(value):
    """Return a clean display path without provider wrappers."""
    text = str(value or "").strip().replace("\\", "/")
    text = text.replace("[default]", "").lstrip("/")
    text = re.sub(r'^prov:[^:/]+:/?', '', text, flags=re.IGNORECASE)
    text = text.replace("/tag:", "/").replace("tag:", "")
    text = re.sub(r':?/alm:[^/]+$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'/+', '/', text)
    return text.strip("/")


def normalize_type_name(value):
    """Normalize typeId values so matching is stable."""
    value = str(value).strip()
    value = value.replace("[default]_types_/", "")
    value = value.replace("[default]/", "")
    value = value.replace("[default]", "")
    value = value.lstrip("/")
    return value


def normalize_tag_path(value):
    """Normalize tag/alarm paths so matching works across provider formats."""
    text = str(value or "").strip()
    text = text.replace("\\", "/")

    # Strip Ignition alarm suffix, e.g. :/alm:Failure
    text = re.sub(r':?/alm:[^/]+$', '', text, flags=re.IGNORECASE)

    # Remove provider wrappers such as prov:default:/tag:
    text = re.sub(r'^prov:[^:/]+:/?', '', text, flags=re.IGNORECASE)
    text = text.replace("prov:default:", "")
    text = text.replace("[default]", "")
    text = text.replace("[default]_types_/", "")
    text = text.replace("[default]/", "")

    # Normalize tag/alm prefixes used in alarm source paths.
    text = text.replace("/tag:", "/")
    text = text.replace("/alm:", "/")
    text = text.replace("tag:", "")
    text = text.replace("alm:", "")

    text = re.sub(r'\[.*?\]_types_/', '', text)
    text = re.sub(r'\[.*?\]/', '', text)
    text = re.sub(r'/+', '/', text)
    text = text.lstrip("/")
    text = text.rstrip("/")
    return text.lower()


def equipment_name(instance_path):
    """Return the short equipment name (last path segment) for the CSV."""
    text = display_path(instance_path)
    parts = [part for part in text.split("/") if part]
    return parts[-1] if parts else str(instance_path)


def build_label(equipment, alarm_label):
    """Build the Label column like 'ASH2_DC2_SWD_B12_BKR_5E Percent Load Hi'."""
    equipment = str(equipment or "").strip()
    alarm_label = str(alarm_label or "").strip()
    if equipment and alarm_label:
        return "%s %s" % (equipment, alarm_label)
    return equipment or alarm_label


def alarm_display_path(instance_path, alarm):
    """Build the Display Path column from the alarm source or display path."""
    summary = get_alarm_summary(alarm)
    for key in ('displayPath', 'sourcePath', 'path', 'tagPath'):
        value = safe_get(alarm, key, '')
        if value:
            return display_path(value)

    for key in ('displayPath', 'sourcePath', 'path', 'tagPath'):
        value = safe_get(summary, key, '')
        if value:
            return display_path(value)

    return display_path(instance_path)


def path_matches(instance_path, alarm_path):
    """Return True when the alarm belongs to the instance or a child tag under it."""
    inst = normalize_tag_path(instance_path)
    alarm = normalize_tag_path(alarm_path)

    if not inst or not alarm:
        return False

    return alarm == inst or alarm.startswith(inst + "/")


def is_alarm_active(alarm):
    """Return True only for genuinely active alarm records."""
    summary = get_alarm_summary(alarm)
    state = str(safe_get(summary, 'state', safe_get(alarm, 'state', safe_get(alarm, 'alarmState', '')))).strip()

    if not state:
        active_flag = safe_get(summary, 'active', safe_get(alarm, 'active', safe_get(alarm, 'isActive', None)))
        if isinstance(active_flag, bool):
            return active_flag
        return False

    state_lower = state.lower()

    if any(word in state_lower for word in ('clear', 'cleared', 'inactive', 'disabled', 'off', 'suppressed')):
        return False

    if state in ("ActiveUnacked", "ActiveAcked", "Shelved", "1", "2", "5"):
        return True

    if 'active' in state_lower or 'unacked' in state_lower or 'acked' in state_lower:
        return 'clear' not in state_lower and 'inactive' not in state_lower

    if state_lower == 'shelved':
        return True

    return False


def get_alarm_source_paths(alarm):
    """Collect real tag source paths from an alarm record."""
    summary = get_alarm_summary(alarm)
    paths = []

    for key in ('sourcePath', 'path', 'tagPath'):
        value = safe_get(alarm, key, '')
        if value:
            paths.append(str(value))

        value = safe_get(summary, key, '')
        if value:
            paths.append(str(value))

    seen = set()
    unique_paths = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    return unique_paths


def filter_active_alarms(alarms):
    """Keep only genuinely active alarms after a gateway query."""
    active = []
    for alarm in alarms or []:
        if is_alarm_active(alarm):
            active.append(alarm)
    return active


def merge_alarm_results(target, alarms):
    """Merge alarms into a dict keyed by stable alarm identity."""
    for alarm in alarms or []:
        target[alarm_identity(alarm)] = alarm


def load_active_alarms(instance_paths):
    """Load alarms using methods that work from the Designer script console.

    Designer does not expose system.alarm.AlarmState, and numeric state=[1,2]
    does not filter on this gateway. We try string states first, then query
    only the known UDT instance paths in small batches.
    """
    merged = {}
    string_states = ["ActiveUnacked", "ActiveAcked"]

    # 1) State-only query using string state names (Shelved omitted - breaks on this gateway).
    try:
        alarms = system.alarm.queryStatus(state=string_states)
        count = len(alarms) if alarms else 0
        log_progress("Alarm query (string states) returned %d records" % count)
        if 0 < count <= MAX_ALARM_RECORDS:
            return filter_active_alarms(alarms)
        if count > MAX_ALARM_RECORDS:
            log_progress("String-state query returned too many records, trying path batches")
    except Exception as e:
        log_progress("Alarm query (string states) failed: %s" % e)

    # 2) Java AlarmState enum (works on some gateways where system.alarm.AlarmState does not).
    try:
        from com.inductiveautomation.ignition.common.alarming import AlarmState
        alarms = system.alarm.queryStatus(state=[
            AlarmState.ActiveUnacked,
            AlarmState.ActiveAcked,
        ])
        count = len(alarms) if alarms else 0
        log_progress("Alarm query (java AlarmState) returned %d records" % count)
        if 0 < count <= MAX_ALARM_RECORDS:
            return filter_active_alarms(alarms)
        if count > MAX_ALARM_RECORDS:
            log_progress("Java-state query returned too many records, trying path batches")
    except Exception as e:
        log_progress("Alarm query (java AlarmState) failed: %s" % e)

    # 3) Path-scoped batches for only the matched UDT instances (safe + targeted).
    log_progress(
        "Querying alarms for %d instances in batches of %d"
        % (len(instance_paths), PATH_BATCH_SIZE)
    )

    total_batches = (len(instance_paths) + PATH_BATCH_SIZE - 1) / PATH_BATCH_SIZE
    batch_index = 0

    for start in range(0, len(instance_paths), PATH_BATCH_SIZE):
        check_timeout("alarm path batch")
        batch_index += 1
        chunk = instance_paths[start:start + PATH_BATCH_SIZE]

        batch_alarms = None
        try:
            batch_alarms = system.alarm.queryStatus(
                path=chunk,
                state=string_states,
            )
        except Exception:
            try:
                batch_alarms = system.alarm.queryStatus(path=chunk)
            except Exception as e:
                log_progress("Path batch %d of %d failed: %s" % (batch_index, total_batches, e))
                continue

        count = len(batch_alarms) if batch_alarms else 0
        log_progress("Path batch %d of %d returned %d records" % (batch_index, total_batches, count))

        if count > MAX_ALARM_RECORDS:
            raise SystemExit(
                "Path batch returned too many alarms (%d). Stopping to protect the system." % count
            )

        merge_alarm_results(merged, batch_alarms)

    return filter_active_alarms(merged.values())


def build_alarm_map(active_alarms):
    """Index active alarms by normalized source path."""
    alarm_map = {}

    for alarm in active_alarms:
        check_timeout("alarm indexing")

        if not is_alarm_active(alarm):
            continue

        alarm_id = alarm_identity(alarm)
        for source_path in get_alarm_source_paths(alarm):
            key = normalize_tag_path(source_path)
            if not key:
                continue
            alarm_map.setdefault(key, {})[alarm_id] = alarm

    return alarm_map


def get_alarms_for_instance(instance_path, alarm_map):
    """Find alarms that belong to one UDT instance."""
    norm_instance = normalize_tag_path(instance_path)
    alarms_for_instance = {}
    seen_alarm_ids = set()

    for key, alarm_bucket in alarm_map.items():
        if not path_matches(norm_instance, key):
            continue
        for alarm_id, alarm in alarm_bucket.items():
            if alarm_id in seen_alarm_ids:
                continue
            seen_alarm_ids.add(alarm_id)
            alarms_for_instance[alarm_id] = alarm

    return alarms_for_instance.values()


def instance_matches_udt(result, match_name):
    """Return True when a browse result is an instance of the requested UDT."""
    type_name = normalize_type_name(safe_get(result, 'typeId', safe_get(result, 'type', '')))
    type_name_lower = type_name.lower()
    leaf_name = type_name_lower.split('/')[-1] if type_name_lower else ""

    if not leaf_name:
        return False

    return match_name == leaf_name or type_name_lower.endswith("/" + match_name)


# RUN
log_progress("Starting SAFE UDT instance scan for '%s'" % udt_name)
log_progress("Only UDT instances are browsed (not every tag in the project)")

match_name = str(udt_name).strip().lower()

# IMPORTANT: tagType=UdtInstance avoids scanning millions of atomic tags.
browse = system.tag.browse("[%s]" % provider, {"tagType": "UdtInstance", "recursive": True})

for result in browse.getResults():
    check_timeout("UDT instance scan")
    scanned_count += 1

    now = time.time()
    if now - last_heartbeat >= HEARTBEAT_SECONDS:
        last_heartbeat = now
        log_progress("Checked %d UDT instances, matched %d so far" % (scanned_count, len(results)))

    full_path = str(safe_get(result, 'fullPath', ''))
    if not full_path:
        continue

    if instance_matches_udt(result, match_name):
        results.append(full_path)

results = sorted(set(results), key=lambda path: display_path(path).lower())

if not results:
    raise SystemExit("No UDT instances found for '%s'." % udt_name)

log_progress("Found %d instances, loading active alarms once" % len(results))

active_alarms = load_active_alarms(results)
alarm_map = build_alarm_map(active_alarms)
log_progress("Indexed %d active alarm paths" % len(alarm_map))

header = ["Label", "Display Path", "State", "Active Time", "Priority"]
rows = []
matched_alarm_count = 0
instances_with_alarms = 0

for index, instance_path in enumerate(results, start=1):
    check_timeout("CSV row build")

    if index == 1 or index % 10 == 0 or index == len(results):
        log_progress("Building rows %d of %d: %s" % (index, len(results), equipment_name(instance_path)))

    equipment = equipment_name(instance_path)
    instance_display = display_path(instance_path)
    alarms_for_instance = get_alarms_for_instance(instance_path, alarm_map)

    active_rows = []
    for alarm in alarms_for_instance:
        summary = get_alarm_summary(alarm)
        alarm_label = str(safe_get(summary, 'label', safe_get(summary, 'name', safe_get(alarm, 'label', safe_get(alarm, 'name', safe_get(alarm, 'alarmName', ''))))))
        priority = friendly_priority(safe_get(summary, 'priority', safe_get(alarm, 'priority', '')))
        state = friendly_state(safe_get(summary, 'state', safe_get(alarm, 'state', safe_get(alarm, 'alarmState', ''))))
        active_time = format_active_time(safe_get(summary, 'activeTime', safe_get(alarm, 'activeTime', safe_get(alarm, 'eventTime', safe_get(alarm, 'timestamp', '')))))

        active_rows.append([
            build_label(equipment, alarm_label),
            alarm_display_path(instance_path, alarm),
            state,
            active_time,
            priority,
        ])
        matched_alarm_count += 1

    if active_rows:
        instances_with_alarms += 1
        rows.extend(active_rows)
    else:
        rows.append([
            equipment,
            instance_display,
            "",
            "",
            "",
        ])

log_progress("Writing %d rows to %s" % (len(rows), output_path))


def csv_escape(value):
    return str(value).replace('"', '""')


lines = [",".join([csv_escape(x) for x in header])]
for row in rows:
    lines.append(",".join([csv_escape(x) for x in row]))

system.file.writeFile(output_path, "\n".join(lines), False)

log_progress("Complete: wrote %d rows in %.1f seconds" % (len(rows), time.time() - start_time))
print("Found %d instances of %s" % (len(results), udt_name))
print("Active alarms loaded from gateway:", len(active_alarms))
print("Instances with active alarms:", instances_with_alarms)
print("Found %d active alarm rows for matching instances" % matched_alarm_count)
print("CSV written to:", output_path)