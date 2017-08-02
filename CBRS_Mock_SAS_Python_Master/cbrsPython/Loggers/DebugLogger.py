from Loggers.LogObserver import Observer
from datetime import datetime
import logging
import os
from model.Utils import Consts as consts
import json
from controllers.CLIUtils.enums import StepStatus


class DebugLogger(Observer):
    def __init__(self):
        self.log_Name = None
        
    
    def startTest(self,dir_Path,log_Name,folder_Name=None):
        if(log_Name!= consts.CLI_SESSION):
            log_file =  '\Logs\LogsPerTest\_'+log_Name+"_" + str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) +'.log'        
            self.addLoggerFile(dir_Path,log_Name, log_file)
            self.log_Name = log_Name
    
    def startStep(self,json_dict,typeOfCalling):
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
        self.removeLogger()
    
    def print_to_Logs_Files(self,message,isCmdOutput):   
        log = logging.getLogger(self.log_Name)
        log.info(message)
                
    def print_To_Terminal(self,message):
        pass
    def removeLogger(self):
        logging._removeHandlerRef(self.log_Name)
    
    def addLoggerFile(self,dir_Path, logger_name, log_file):
        log_setup = logging.getLogger(logger_name)
        formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        fileHandler = logging.FileHandler(str(dir_Path) + log_file, mode='a')
        fileHandler.setFormatter(formatter)
        log_setup.addHandler(fileHandler)
        log_setup.setLevel(logging.INFO)