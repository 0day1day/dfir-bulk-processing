#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: skeletool.py
#
# Copyright (c) 2011 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0

#
# Normal methods
import subprocess, string, os.path, sys
import argparse


# Our own methods
from dfir_utils.dfir_utils import is_user_admin, DFIRConfigs, DFIR
from image_mounting.mip import MountImagePro
from dfir_registry import dfir_registry

'''

skeletool is a script I'm writing to drive the development of a variety
of DF (digital forensics) and IR (Incident Response). My hope is to write,
or gather, a variety of useful modules into one location. Calling this a
framework is probably overstating the organization, but it certainly serves
as a mental framework for my development work.

It is an exercise for the reader to make this more portable by making a
new "Images" method and having the current MIP method inherit from Images. Then
write a TSKMount method to use on Linux. And another subclass for IMDisk.

The subinacl wouldn't be needed on Linux.

Dependencies:

1) Python (currently 2, may go to 3 soon)
2) Mount Image Pro (need a Windows based image mounting tool with a CLI)
3) subinacl (Set permissions on mounted images so we can access entire image)

Notes:

- Sometimes the MIP.mount() call hangs, most often because the MIP.status() call is hanging.
The solution seems to be to start up the MIP GUI before using this tool. In fact,
there doesn't seem to be any harm in leaving the GUI running.

- MIP mounts the image as a device and one or more drives. I can figure out how
to unmount the drives, but not the physical device, at least not without using the GUI.
I've sent an email to the vendor asking for assistance with this.

- python.exe must be set to "Run as Administrator" for the subinacl call to work,
even if the user running the script has admin permissions.

- There are times that subinacl will throw an error on an image that wasn't
exhibiting any problems earlier. The most common one has been reporting that the
disk is read-only. I think this has to do with MIP and caching, but
I don't know for sure. Rebooting solves the problem.

ToDo:

1) Implement exceptions and handling


'''

def process_image(dfir, images, image_path):
    
    status = images.mount(image_path)
    if (status is False):
        return(status)
    
    # Walk through all of the newly mounted volumes
    for volume in images.volumes:
        print "Processing volume: " + volume[0]

        # Pseudocode -
        # dfir.process(volume)
        # Where dfir.process will do stuff based on config file
        dfir_registry.system_metadata(dfir, drive, image_path)        
        ripxp(dfir, drive, image_path)
        
        images.unmount(drive)
        return (True)

def ripxp(dfir, drive, image_path):

    user = is_user_admin()
    if (user is False):
        print "Must be an Administrator to use ripxp functionality."
        exit
        
    # Build the path to the System Volume Information folder
    svi_path = os.path.join(drive[0], '\System Volume Information')
    
    if os.path.exists(svi_path) is True:
        p = subprocess.Popen([config.cmds['subinacl'], "/subdirectories", svi_path, \
            "/setowner=" + user, "/grant=" + user + "=F"], \
            bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        stdout, stderr = p.communicate()
        stdout = stdout.translate(None, '\x00')
        # print "subinacl output: \n" + stdout
        
        for rp_path in os.listdir(svi_path):
            if "_restore" in rp_path:
                rp_path = os.path.join(svi_path, rp_path)
                system_path = os.path.join(drive[0], "\WINDOWS\system32\config\SYSTEM")
                print "Processing: Restore point: " + rp_path + "\nHive:" + system_path

                p = subprocess.Popen([config.cmds['ripxp'], "-r", system_path, "-d", rp_path, \
                    "-p", "usbstor3"], bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                stdout, stderr = p.communicate()
                
                dfir.task = "ripxp"
                dfir.identifier = os.path.basename(image_path)
                dfir.write_output(stdout)
                
                
    else:
        print "No System Volume Information folder on drive: " + drive[0]
            
if __name__ == '__main__':
    
    
    ''' Eventually, this will:
    1) Read a config file that contains image name, case folder pairs (and maybe
       a trailing set of options?)
    2) For each pair:
        a) Create the appropriate subdirectories in the case folder
        b) Mount the image
        c) Set the permissions on the RP directory appropriately
        d) Run RipXP against the RPs.
    
    Down the road, it will do a lot more. Collect and process the MFT, collect
    and process the hives, collect system metadata, etc. Extracted files and
    results for each task would go in a task specific folder in the case folder.
    '''
    
    parser = argparse.ArgumentParser(description='Process an image file for DFIR information')
    parser.add_argument('-l', '--list', action="store", dest="list_file", \
            help='file containing a list of images/drives and their output location')
    parser.add_argument('-i', '--image', action="store", dest="image_file", \
            help='File containing a valid image')
    parser.add_argument('-v', '--volume', action="store", dest="voume_path", \
            help='Path to mounted volume.')
    parser.add_argument('--id', action="store", dest="id", \
            help='Image/volume identifier for output file naming')
    parser.add_argument('-o', '--output', action="store", dest="output_path", \
            help='Output folder to store results')
    parser.add_argument('-c', '--config', action="store", dest="config_file", \
            help='Configuration file if not using default dfir-config.txt')
    

    args = parser.parse_args()
    if (args.list_file is not None):
        if (args.image_file is not None or args.volume_path is not None or args.output_path is not None):
            print "May not specify image file, volume path, or output file when specifying list containing input"
            sys.exit()
    elif (args.image_file is None and args.volume_path is None):
        print "Must specify either an image file or a volume path to analyze."
        sys.exit()
    elif (args.output_path is None):
        print "Must specify an output file"
        sys.exit()

    # Read the config file for skeletool
    config = DFIRConfigs(args.config_file)
    
    # Get a DFIR object for managing our collected information.
    dfir = DFIR()
    
    # Set the program name, used for naming output files.
    dfir.prog = "skeletool"
    
    ''' Up until now, it's been all prep. '''

    # Get an image object, telling it that we want to use Mount Image Pro to do the mounting.
    images = MountImagePro(config.cmds['mip4'])
    
    
    # Check to see if we're doing a collection of images or just one.
    if (args.list_file == None):
        
        # images.id should replace image_path getting passed around as an identifier
        dfir.output_folder = args.output_path
        if (args.id is None):
            images.id = "noID"
        else:
            images.id = args.id

        # process_images should call process_volume.
        # process_volume should contain the call to dfir.dostuff(volume)
        
        if (args.volume_path is not None):
            process_volume(dfir, args.volume_path)
        else:                        
            status = images.mount(image_path)
            if (status is False):
                print "Unable to mount ", image_path
                sys.exit()
                
    
            # Walk through all of the newly mounted drives
            for volume in images.volumes:
                print "Processing volume: " + volume[0]

                dfir_registry.system_metadata(dfir, volume, image_path)        
        ripxp(dfir, drive, image_path)
        
        images.unmount(drive)
        return (True)
            # Pseudo code - mount (image_file)
            # for each volume in image:
            #   process_volume(dfir, volume_path)
            
            process_image(dfir, images, args.image_file)
    
    else:
        
        try:
            fd = open(args.list_file, 'r')

        except:
            print "Unable to file containing image information: " + args.list_file
            sys.exit()
    
        for line in fd:
            line = line.rstrip('\n\r')
            
            # Skip over comment lines, and lines that might
            if (len(line) > 0 and line[0] != '#'):
                
                image_path, sep, output_path = line.partition('\t')
                if (sep is '' or output_path is ''):
                    print "Error in images file: \n\t" + line
                    sys.exit()

                dfir.output_folder = output_path
                process_image(dfir, images, image_path)
