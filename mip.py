#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: mip.py
#
# Copyright (c) 2011 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0

import subprocess, os.path, sys

default_path = "C:\Program Files (x86)\GetData\Mount Image Pro v4\MIP4.exe"

class MountImagePro:
    
    '''Mount images, dismount images, and report on the status of mounted images
    using MIP4.exe. Takes one option - either 'default', meaning to use the default
    path for mip4.exe, or the path to mip4.exe'''
    
    def  __init__(self, path):
        
        self.volumes = None

        if (path is not 'default'):
            self.mip4 = path
        else:
            self.mip4 = default_path

            ''' os.path.exists currently fails on Windows 7 for some reason. This
            test is currently disabled.
            if (os.path.exists(path)):
                self.mip4 = path
            else:
                print "Path does not exist: " + path
                sys.exit()
            '''
            
            
    def mount(self, path):
        
        cur_images = self.status()
        ''' Calls MIP4 to mount an image. Determines the success/failure of
        the mount by checking the difference between the volumes mounted before
        and after the mount call using "mip4 /status". This is expensive and
        not error proof.
        
        If the call succeeds, the newly mounted volumes are stored in
        self.volumes
        '''
        
        # print "Before mount: ", cur_images
        
        while True:
            while (path is None):
                path = raw_input("Enter the full path to the image: ")
                if (os.path.exists(path) is False):
                    print path + "is not a valid path."
                    path = None
            
            p = subprocess.Popen([self.mip4, "mount ", path], bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            stdout, stderr = p.communicate()

            cur2_images = self.status()
            
            # print "After mount: ", cur_images
        
            new_images=list(set(cur2_images)-set(cur_images))
            if len(new_images) == 0:
                print "Mount failed: " + path
                return(False)
            self.volumes = new_images
            return(True)
            
    def unmount(self, volume):
        
        ''' Using MIP4.exe, unmount a single volume. The volume may be the only
        volume in an image, or it may be one of many.
        
        At the moment, we only unmount the drive letter leaving a physical drive
        still mounted. I cannot figure out how to either a) not mount that physical
        drive or b) specify that I want to unmount both. I could use /all, but that
        would unmount everything, including images that were not mounted by
        this utility.'''

        p = subprocess.Popen([self.mip4, "unmount", "/L:" + volume[0][0]], bufsize=1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        # Should call self.status() and check to make sure that volume[0] is no longer present.
        # print p.communicate()[0]
        
    def status(self):
        
        _images = False
        _num_mounted = 0
        _return_val = []
        
        p = subprocess.Popen([self.mip4, "status"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        for line in stdout.splitlines():
            if "List of mounted images" in line:
                _images = True
            elif (_images is True and len(line)> 1):
                mount_point, sep, image_file = line.partition(' ')
                image_file = os.path.normpath(image_file)
                mount_number = mount_point[3]
                mount_point = mount_point[:2]
                _return_val.append((mount_point, mount_number, image_file))
                
        return(_return_val)
