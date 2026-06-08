"""
The purpose of this script is to audit the UDT synchronization. This script will determine whether a sync was successful based on the following criteria:
1. Alarms before and after
2. Tag data quality before and after
3. Tag values before and after
This script is supposed to be run in the Ignition script console after an EAM synchronization.
"""
# All output files will be written to C:\Users\Public\Documents\
# All before script files will be read from C:\Users\Public\Documents\

# Pull in the equipment list by reading C:\Users\Public\Documents\equipment_list.csv generated in the before script.
    #   Headers: name, path
    #   One row per piece of equipment
# Create three CSV files for the audit:
    #   1. C:\Users\Public\Documents\alarms_after.csv
    #   2. C:\Users\Public\Documents\quality_after.csv
    #   3. C:\Users\Public\Documents\values_after.csv
# For each piece of equipment, do the following:
    # Check alarms:
    #     Recursively export all of the active alarms under the equipment to alarms_after.csv
    #     Open + read C:\Users\Public\Documents\alarms_before.csv generated in the before script
    #     Open + read alarms_after.csv
    #     Compare the alarms in both files.
    #         If there were no new alarms, print a message indicating there were no new alarms.
    #         If new alarms were created from the sync, print those to the script console and to C:\Users\Public\Documents\alarms_audit_log.csv
    # Check tag data quality:
    #     Recursively export all of the tag quality values under the equipment to quality_after.csv
    #     Open + read C:\Users\Public\Documents\quality_before.csv generated in the before script
    #     Open + read quality_after.csv
    #     Compare the quality values in both files.
    #         If there were no new quality issues, print a message indicating there were no new quality issues.
    #         If new quality issues were created from the sync, print those to the script console and to C:\Users\Public\Documents\quality_audit_log.csv
    # Check tag values:
    #     Recursively export all of the tag values under the equipment to values_after.csv
    #     Open + read C:\Users\Public\Documents\values_before.csv generated in the before script
    #     Open + read values_after.csv
    #     Compare the tag values in both files.
    #         If there were no changed tag values, print a message indicating there were no changed tag values.
    #         If tag values changed from the sync, print those to the script console and to C:\Users\Public\Documents\values_audit_log.csv