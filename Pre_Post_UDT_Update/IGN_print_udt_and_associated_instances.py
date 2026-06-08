# USER INPUT REQUIRED: Set the site name. Example: "ASH3-DC2"
site = "PHX2-DC1"

# USER INPUT REQUIRED: Set the UDT name. Example: "Breaker_PODPrime_AB_v3_1"
udt_name = "Breaker_PODPrime_AB_v3_1"

instance_list = []

udts = system.tag.browse("[Default]", {
    "recursive": True,
    "tagType": "UdtType",
    "name": udt_name
})

if len(udts.getResults()) == 0:
    print("This UDT does not exist at this site")
elif len(udts.getResults()) == 1:
    for udt in udts.getResults():
        udt_string = str(udt['fullPath'])
        udt_full_name = udt_string.split("[default]_types_/")[1]
        print("UDT Definition Found: " + "*" + str(udt_full_name))
        if udt_name.split("_")[-1] == "v3":
            formatted_version_date = system.date.format(system.date.fromMillis(system.tag.readBlocking([udt_string])[0].value['version']), "yyyy-MM-dd HH:mm:ss")
            print(formatted_version_date)
        instances = system.tag.browse("[Default]", {
            "recursive": True,
            "tagType": "UdtInstance",
            "typeId": udt_full_name
        })
        print("Instances:")
        for inst in instances.getResults():
            print(inst['fullPath'])
            instance_list.append(inst['fullPath'])
else:
    print("There were " + str(len(udts.getResults())) + " UDTs found based on the filter above")

if len(udts.getResults()) == 1:
    file_path = "C:\\Users\\Public\\Documents\\{0}-UDTs\\{1}.json".format(site, udt_name)
    tag_path = [str(udts.getResults()[0]['fullPath'])]
    system.tag.exportTags(file_path, tag_path, True, "json")
    if len(instance_list) == 0:
        print("Recommendation: Delete UDT {0} as it has no instances, but make sure it's not a nested UDT first!".format(udt_name))
    else:
        print("There were " + str(len(instance_list)) + " instances found")

print('-'*150)