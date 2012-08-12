#!/usr/bin/env python

# Author: David Kovar [dkovar <at> gmail [dot] com]
# Name: dfirutils.py
#
# Copyright (c) 2011 David Kovar. All rights reserved.
# This software is distributed under the Common Public License 1.0

import win32net
import platform
import getpass

import subprocess, os.path, sys
from time import localtime, strftime

class DFIRConfigs:
    
    '''Read in DFIR configuration file and make information available.
    Currently just returns the various programs and their paths as a dictionary
    using the program's name as the key.'''
    
    # NOTE: Should use config parser.
    
    def  __init__(self, file):
        self.cmds = {}
        
        if (file == None):
            file = "dfir-config.txt"
            
        try:
            F = open(file, 'r')

        except:
            print "Unable to read dfir configuration file: " , file
            sys.exit()
    
        for line in F:
            line = line.rstrip('\n\r')
            line = line.lstrip()
            
            # Skip over comment lines, and lines that might
            if (len(line) > 0 and line[0] != '#'):
                
                prog, sep, path = line.partition('=')
                if (sep is '' or path is ''):
                    print "Error in configuration file: \n\t" + line
                    sys.exit()
            
                prog = prog.strip()
                path = os.path.normpath(path.lstrip())
            
                ''' os.path.isfile and os.path.exists both fail as os.stat fails
                on all the executables. Not sure why. Once I figure it out, these
                tests need to be reenabled.
    
                if (os.path.exists(path) is not True):
                    print "Invalid path: " + path
                    sys.exit()
                '''    
                self.cmds[prog] = path
                # print prog, path

class DFIR:
    
    def  __init__(self):
        self.prog = "skeletool"
        self.task = "generic"
        self.identifier = "generic"
        self.output_folder = "C:\temp"
    

    def write_output(self, output):
    
        file_name = self.prog + "-" + self.task + "-" + self.identifier + strftime("%d-%b-%Y-%H%M%S", localtime())
        file_name = file_name.replace('.', '_')
        file_name = file_name + ".txt"
        output_path = os.path.normpath(os.path.join(self.output_folder, file_name))
                
        try:
            fd = open(output_path, 'w')
                        
        except IOError:
            print "Unable to open output file: " + output_path
            sys.exit()
                    
        fd.write(output)
        fd.close()


def is_user_admin():
    ''' Return the current username if the user is an Administrator, otherwise
    return False '''
    #Get current hostname and username
    sHostname = platform.uname()[1]
    sUsername = getpass.getuser()
    
    #Define account memberships to test as false
    memberAdmin = False
    
    for groups in win32net.NetUserGetLocalGroups(sHostname,sUsername):
        #If membership present, set to true
        if groups == 'Administrators':
            return (sUsername)
    
    return False
