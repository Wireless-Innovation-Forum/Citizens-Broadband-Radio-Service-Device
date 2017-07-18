from Loggers.LogObserver import Observer
from datetime import datetime
from model.Utils import Consts as consts
from controllers.CLIUtils.enums import StepStatus
import logging
 
 
class CmdLogger(Observer):
    def __init__(self):
        self.currentLoggerName = []
    
    def startTest(self,dir_Path,log_Name,folder_Name=None):
        if(log_Name==consts.CLI_SESSION):
            log_file =  '\Logs\CMDSessions\cmdSession_' + str(datetime.now().strftime("%Y_%m_%d_%H_%M_%S")) +'.log'
            self.addLoggerFile(dir_Path,consts.CLI_SESSION, log_file)
    
    def startStep(self,json_dict,typeOfCalling):
        self.print_To_Terminal("CBSD sent " + str(typeOfCalling) +" " + consts.REQUEST_NODE_NAME)
    
    def finishStep(self,response,typeOfCalling,stepStatus):
        if stepStatus==StepStatus.PASSED:
            self.print_To_Terminal(consts.VALIDATION_PASSED_MESSAGE + str(typeOfCalling) + " " + consts.RESPONSE_NODE_NAME.title())
        else:
            self.print_To_Terminal(response)
        
        
    def finishTest(self,msg,isCmdOutput,testStatus,additionalComments):
        if(isCmdOutput):
            if(additionalComments!=None):
                msg = msg + consts.ADDITIONAL_COMMENTS_MESSAGE + additionalComments
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
        formatter = logging.Formatter('%(levelname)s: %(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        fileHandler = logging.FileHandler(str(dir_Path) + log_file, mode='a')
        fileHandler.setFormatter(formatter)
        log_setup.addHandler(fileHandler)
        log_setup.setLevel(logging.INFO)
        self.currentLoggerName.append(log_setup.name)
 