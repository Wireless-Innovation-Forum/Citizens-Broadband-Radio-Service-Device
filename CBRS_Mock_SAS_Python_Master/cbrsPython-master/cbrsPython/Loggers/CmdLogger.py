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
from model.Utils import Consts as consts
from controllers.CLIUtils.enums import StepStatus
import logging
from time import gmtime
import os
 
class CmdLogger(Observer):
    def __init__(self):
        self.currentLoggerName = []
    
    def startTest(self,dir_Path,log_Name,folder_Name=None):
        if(log_Name==consts.CLI_SESSION):
            log_file = os.path.join('Logs','CMDSessions', 'cmdSession_'+ datetime.utcnow().replace(microsecond=0).isoformat() +'Z.log')

            log_file = log_file.replace(':','.')
            self.addLoggerFile(dir_Path,consts.CLI_SESSION, log_file)
            self.print_To_Terminal(consts.WINNF_TEST_HARNESS_RELEASE_TEXT+consts.TEST_HARNESS_VERSION + " - "+ consts.TEST_HARNESS_DATE)
    
    def startStep(self,json_dict,typeOfCalling,ipRequestAddress=None):
#        self.print_To_Terminal("Time : " +  str(datetime.now().strftime("%d/%m/%Y %H:%M:%S") 
#                                                + " , CBSD sent " + str(typeOfCalling) +" " + consts.REQUEST_NODE_NAME + " from the address : " + str(ipRequestAddress)))
        self.print_To_Terminal( datetime.utcnow().isoformat()+'Z:' \
                                                + " CBSD sent " + str(typeOfCalling) +" " + consts.REQUEST_NODE_NAME + " from the address : " + str(ipRequestAddress))
    
    def finishStep(self,response,typeOfCalling,stepStatus):
        if stepStatus==StepStatus.PASSED:
            self.print_To_Terminal(datetime.utcnow().replace(microsecond=0).isoformat()+'Z: '+consts.VALIDATION_PASSED_MESSAGE + str(typeOfCalling) + " " + consts.RESPONSE_NODE_NAME.title())
        else:
            self.print_To_Terminal(response)
        
        
    def finishTest(self,msg,isCmdOutput,testStatus,additionalComments):
        if(isCmdOutput):
            if(additionalComments!=None):
                msg = msg + " " + consts.ADDITIONAL_COMMENTS_MESSAGE + additionalComments
            self.print_To_Terminal(msg)
        
    def print_To_Terminal(self,message):
        log = logging.getLogger(consts.CLI_SESSION)
        log.info(message)
        print message     
        
    def print_to_Logs_Files(self, message, isCmdOutput):
        if(isCmdOutput):
            self.print_To_Terminal(message)    
        
    def addLoggerFile(self,dir_Path, logger_name, log_file):
        log_setup = logging.getLogger(logger_name)
#        formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        formatter = logging.Formatter('%(asctime)s.%(msecs)03dZ - %(levelname)s - %(message)s', datefmt="%Y-%m-%dT%H:%M:%S")
        formatter.converter = gmtime
        
        fileHandler = logging.FileHandler(os.path.join(str(dir_Path),log_file), mode='a')
        fileHandler.setFormatter(formatter)
        log_setup.addHandler(fileHandler)
        log_setup.setLevel(logging.INFO)
        self.currentLoggerName.append(log_setup.name)
 