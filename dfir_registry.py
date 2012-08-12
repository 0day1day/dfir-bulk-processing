#!/usr/bin/env python

import string, os
from Registry import Registry

def system_metadata(dfir, drive, image_path):


    software_path = os.path.join(drive[0], "\WINDOWS\system32\config\SOFTWARE")
    print "Processing software hive: " + software_path
    
    reg = Registry.Registry(software_path)
    try:
        key = reg.open("Microsoft\Windows NT\CurrentVersion")

    except Registry.RegistryKeyNotFoundException:
        print "Couldn't find Run key. Exiting..."
        sys.exit(-1)

    output_list = []
    
    for ival in ['ProductName', 'RegisteredOwner']:
        value = key.value(ival)
        # Build a list containing all of the output
        output_list.append(ival + ": " + value.value() + '\n')
        
    dfir.task = "metadata"
    dfir.identifier = os.path.basename(image_path)
    
    # Then join the list together to get a single string, passing it to the
    # output function.
    dfir.write_output(''.join(output_list))
