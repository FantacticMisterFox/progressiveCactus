#!/usr/bin/env python

# Progressive Cactus Package
# Copyright (C) 2009-2012 by Glenn Hickey (hickey@soe.ucsc.edu)
# and Benedict Paten (benedictpaten@gmail.com)

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import os
import sys
import xml.etree.ElementTree as ET
import math
import time
import random
import copy
from optparse import OptionParser
from optparse import OptionGroup
import imp
import string
import socket

from sonLib.bioio import system

from seqFile import SeqFile
from cactus.progressive.experimentWrapper import ExperimentWrapper
from cactus.progressive.experimentWrapper import DbElemWrapper
from cactus.progressive.configWrapper import ConfigWrapper
from cactus.shared.common import cactusRootPath


# Wrap up the cactus_progressive interface:
# - intialize the working directory
# - create Experiment file from seqfile and options
# - create Config file from options
# - run cactus_createMultiCactusProject
# - now ready to launch cactus progressive
class ProjectWrapper:
    alignmentDirName = 'progressiveAlignment'
    def __init__(self, options, seqFile, workingDir):
        self.options = options
        self.seqFile = seqFile
        self.workingDir = workingDir
        self.configWrapper = None
        self.expWrapper = None
        self.processConfig()
        self.processExperiment()

    def processConfig(self):
        # read in the default right out of cactus
        if self.options.configFile is not None:
            configPath = self.options.configFile
        else:
            dir = os.path.join(cactusRootPath(), "progressive")
            configPath = os.path.join(dir,
                                      "cactus_progressive_workflow_config.xml")
        configXml = ET.parse(configPath).getroot()
        self.configWrapper = ConfigWrapper(configXml)
        # here we can go through the options and apply some to the config
        self.configWrapper.setBuildHal(True)
        self.configWrapper.setBuildFasta(True)
        if self.options.outputMaf is not None:
            self.configWrapper.setBuildMaf(True)
            self.configWrapper.setJoinMaf(True)
        # this is a little hack to effectively toggle back to the
        # non-progressive version of cactus (as published in Gen. Res. 2011)
        # from the high-level interface. 
        if self.options.legacy is True:
            self.configWrapper.setSubtreeSize(sys.maxint)

    def processExperiment(self):
        expXml = self.seqFile.toXMLElement()
        #create the cactus disk
        cdElem = ET.SubElement(expXml, "cactus_disk")
        database = self.options.database
        assert database == "kyoto_tycoon" or database == "tokyo_cabinet"
        confElem = ET.SubElement(cdElem, "st_kv_database_conf")
        confElem.attrib["type"] = database
        dbElem = ET.SubElement(confElem, database)
        self.expWrapper = ExperimentWrapper(expXml)

        if self.options.database == "kyoto_tycoon":
            self.expWrapper.setDbHost(str(self.options.ktHost))
            self.expWrapper.setDbPort(str(self.options.ktPort))
            if self.options.ktType == 'memory':
                self.expWrapper.setDbInMemory(True)
                self.expWrapper.setDbSnapshot(False)
            elif self.options.ktType == 'snapshot':
                self.expWrapper.setDbInMemory(True)
                self.expWrapper.setDbSnapshot(True)
            else:
                assert self.options.ktType == 'disk'
                self.expWrapper.setDbInMemory(False)
                self.expWrapper.setDbSnapshot(False)
            # sonlib doesn't allow for spaces in attributes in the db conf
            # which renders this options useless
            # if self.options.ktOpts is not None:
            #    self.expWrapper.setDbServerOptions(self.options.ktOpts)
            if self.options.ktCreateTuning is not None:
                self.expWrapper.setDbCreateTuningOptions(
                    self.options.ktCreateTuning)
            if self.options.ktOpenTuning is not None:
                self.expWrapper.setDbReadTuningOptions(
                    self.options.ktOpenTuning)

    def writeXml(self):
        assert os.path.isdir(self.workingDir)
        configPath = os.path.abspath(
            os.path.join(self.workingDir, "config.xml"))
        expPath = os.path.abspath(
            os.path.join(self.workingDir, "expTemplate.xml"))
        self.expWrapper.setConfigPath(configPath)
        self.configWrapper.writeXML(configPath)
        self.expWrapper.writeXML(expPath)

        projPath = os.path.join(self.workingDir,
                                ProjectWrapper.alignmentDirName)
        if os.path.exists(projPath):
            system("rm -rf %s" % projPath)

        system("cactus_createMultiCactusProject.py %s %s" % (expPath, projPath))
        
        
        

        
        
