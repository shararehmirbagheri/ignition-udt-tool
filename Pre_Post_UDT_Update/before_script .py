"""
The purpose of this script is to prepare for the UDT synchronization. This script will do the following:
1. Export alarms on equipment
2. Export tag data on equipment
3. Export tag values on equipment
4. Put equipment into maintenance mode
This script is supposed to be run in the Ignition script console before an EAM synchronization.
"""
# All output files will be written to C:\Users\Public\Documents\

# Create a log file of equipment information under a specific UDT. Output it into the console, and into a log file that the "after_script.py" can access.
    #   Export to C:\Users\Public\Documents\equipment_list.csv
    #   Headers: name, path
    #   One row per piece of equipment
    #   The "after_script.py" will read this file to get the equipment list
# Check alarms:
    #     Recursively export all of the active alarms under each equipment to C:\Users\Public\Documents\alarms_before.csv
    #     Open + read alarms_before.csv
    #     Print all active alarms to the script console for reference.
    #         If no active alarms exist, print a message indicating there are no active alarms.
    #         If active alarms exist, print each one to the script console.
# Check tag data quality:
    #     Recursively export all of the tag quality values under each equipment to C:\Users\Public\Documents\quality_before.csv
    #     Open + read quality_before.csv
    #     Print all tag quality values to the script console for reference.
    #         If no quality issues exist, print a message indicating all tags have good quality.
    #         If quality issues exist, print each one to the script console.
# Check tag values:
    #     Recursively export all of the tag values under each equipment to C:\Users\Public\Documents\values_before.csv
    #     Open + read values_before.csv
    #     Print all tag values to the script console for reference.
    #         If no tag values are found, print a message indicating no tag values were found.
    #         If tag values are found, print each one to the script console.
# Put the equipment into maintenance mode for one hour. Equipment list was generated above. Do this after the exports, as maintenance mode will impact alarms.
    # The tag for maintenance mode is {equipment tag path}/Maintenance/MaintenanceMode.value
        # Example: [default]B1/Electrical/Breaker/PHX2_DC1_COD_B1_BKR_1A/Maintenance/MaintenanceMode.value
    # The tag for disable time is {equipment tag path}/Maintenance/Disable_Time.value
        # Example: [default]B1/Electrical/Breaker/PHX2_DC1_COD_B1_BKR_1A/Maintenance/Disable_Time.value
        # Use system time = now to calculate what 1 extra hour looks like
            # Example of time DateTime: Jun 8, 2026, 3:16:32 PM