# Copyright 2017 CBSD Project Authors. All Rights Reserved.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from Loggers.LogObserver import Observer
from datetime import datetime
import logging
import os
from model.Utils import Consts as consts
import json
from controllers.CLIUtils.enums import StepStatus
from time import gmtime


class DebugLogger(Observer):
    def __init__(self):
        self.log_Name = None
        self.fileHandler =None        
    
    def startTest(self,dir_Path,log_Name,folder_Name=None):
        if(log_Name!= consts.CLI_SESSION):
            log_file = os.path.join('Logs', 'LogsPerTest', log_Name+"_" + datetime.utcnow().replace(microsecond=0).isoformat() +'Z.log')
            log_file = log_file.replace(':','.')
            self.addLoggerFile(dir_Path,log_Name, log_file)
            self.log_Name = log_Name
    
    def startStep(self,json_dict,typeOfCalling,ipRequestAddress=None):
        self.print_to_Logs_Files(typeOfCalling + " request from CBRS  : " + json.dumps(json_dict, indent=4, sort_keys=True),False)
           
    def finishStep(self,response,typeOfCalling,stepStatus):
        if(stepStatus == StepStatus.PASSED):
            self.print_to_Logs_Files("engine sent successfully, the response to CBRS  : "  + json.dumps(response, indent=4, sort_keys=True),False)
        else:
            self.print_to_Logs_Files(response,False)
        
    def finishTest(self,msg,isCmdOutput,testStatus,additionalComments):
        if(additionalComments!=None):
            msg = msg + " and :" + consts.ADDITIONAL_COMMENTS_MESSAGE  + additionalComments
        self.print_to_Logs_Files(msg, isCmdOutput)
        self.stopLoggerFile()
    
    def print_to_Logs_Files(self,message,isCmdOutput):   
        log = logging.getLogger(self.log_Name)
        log.info(message)
                
    def print_To_Terminal(self,message):
        pass
    
    def removeLogger(self):
        logging._removeHandlerRef(self.log_Name)
    
    def addLoggerFile(self,dir_Path, logger_name, log_file):
        log_setup = logging.getLogger(logger_name)
#        formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        formatter = logging.Formatter('%(asctime)s.%(msecs)03dZ - %(levelname)s - %(message)s', datefmt="%Y-%m-%dT%H:%M:%S")
        formatter.converter = gmtime
        
        self.fileHandler = logging.FileHandler(os.path.join(str(dir_Path), log_file), mode='a')
        self.fileHandler.setFormatter(formatter)
        log_setup.addHandler(self.fileHandler)
        log_setup.setLevel(logging.INFO)
        
    def stopLoggerFile(self):
        log_onGoing = logging.getLogger(self.log_Name)
        log_onGoing.removeHandler(self.fileHandler)
        self.fileHandler.close()        