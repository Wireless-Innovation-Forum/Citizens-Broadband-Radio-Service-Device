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
import threading
from threading import Thread
from CLIUtils.CsvFileParser import CsvFileParser
from CLIUtils.QuestionHandler import QuestionHandler
from CLIUtils.TestDefinition import TestDefinition
from model.Engine import MyEngine
import time
import model.Utils.Consts as consts
from model import flaskServer
from ENodeBController import ENodeBController
from controllers.CLIUtils.enums import TestStatus
import os

class CLIHandler(Thread):
    '''
    classdocs
    '''
    def __init__(self,csvFilePath,confFile,dirPath,loggerHandler,testDefinition):
        '''
        Constructor
        '''
        Thread.__init__(self)
        self.testName           = csvFilePath
        self.confFile           = confFile
        self.dirPath            = dirPath
        self._stop              = threading.Event()
        self.loggerHandler      = loggerHandler
        self.questHandler       = QuestionHandler(self.loggerHandler)
        self.testDefinition     = testDefinition
        self.engine             = MyEngine(self.testDefinition,confFile,dirPath,loggerHandler)
        self.server             = None 
        
    def stop_Thread_Due_To_Exception(self):
        self._stop.set()

    def test_Finish_Message_For_Logs(self, finalResults):
        '''
        report finish test to all logs that inserted to logger observer
        '''
        testStatus = None
        if(finalResults[0]==consts.PASS_MESSAGE):
            testStatus = TestStatus.PASSED
        else:
            testStatus = TestStatus.FAILED
        if(not finalResults[1]):
            return self.loggerHandler.finish_Test(consts.RESULTS_OF_TEST_MESSAGE + self.testName + " is - " + str(testStatus.value), True, testStatus)
        else:
            return self.loggerHandler.finish_Test(consts.RESULTS_OF_TEST_MESSAGE + self.testName + " is - " + str(testStatus.value), True, testStatus,finalResults[1])

    def run(self): 
        ''' 
        the thread checks all the time if its the last step from the csv file or an error validation had accured
        while validate inside the engine
        if the test had been finished successfully it show the question answer session from the last expected json
        '''  
        while(not self.engine.check_Last_Step_In_All_CBRS() and not self._stop.isSet()):
            time.sleep(1)
            if(self.engine.check_Validation_Error()):
                self.stop_Thread_Due_To_Exception()
        if not self._stop.is_set():
            time.sleep(1)
            ## for initialize the xml report
            self.loggerHandler.print_to_Logs_Files(consts.NSTEP_SESSION_WITH_TECHNITIAN,True)
            finalResults = self.questHandler.ShowQuestionsAndGetAnswersFromClient(self.engine.get_Question_Answer_Part())
            self.test_Finish_Message_For_Logs(finalResults)        
            start_another_test(self.confFile,self.dirPath,self.loggerHandler)
        else:
            self.loggerHandler.finish_Test(consts.RESULTS_OF_TEST_MESSAGE +self.testName +  " is - " + consts.FAIL_MESSAGE,True,TestStatus.FAILED)
            start_another_test(self.confFile,self.dirPath,self.loggerHandler)
        
def start_another_test(confFile,dirPath,loggerHandler): 
    '''
    as same as in the startOfProject.py 
    initialize new logger for each test and if requested to the specific folder
    stop the last reports of the test running before the new test
    and running a new instance of the flask server  
    '''    
    inputAnsweres = None
    time.sleep(1)        
    loggerHandler.print_To_Terminal(consts.SET_CSV_FILE_MESSAGE)
    NoInput = True
    while NoInput:     
        inputAnsweres = get_input(loggerHandler)
        if(inputAnsweres=="quit"):
            loggerHandler.print_To_Terminal(consts.GOODBYE_MESSAGE)
            NoInput = False
            pass         
        
        if (inputAnsweres !="quit"):   
            try:
                csvFileParser = CsvFileParser(os.path.normpath(os.path.join(str(dirPath),confFile.getElementsByTagName("testRepoPath")[0].firstChild.data,inputAnsweres)),confFile,dirPath)
                testDefinition = TestDefinition(csvFileParser.initializeTestDefinition(),csvFileParser.find_Number_Of_Cols())
                test_execution(confFile,dirPath,loggerHandler,inputAnsweres,testDefinition)
                NoInput = False
                
            except IOError as e:
                loggerHandler.print_To_Terminal(e.message)
                loggerHandler.print_To_Terminal('Please enter the test name again!')
                NoInput = True

def test_execution(confFile,dirPath,loggerHandler,inputAnsweres,testDefinition):
                
    insertToFolderAnswer = add_Log_Of_Test_To_Specific_Folder(loggerHandler)
    if (insertToFolderAnswer == "yes"):
        loggerHandler.print_To_Terminal(consts.TYPE_NAME_OF_FOLDER)
        insertToFolderAnswer = raw_input()
        try:
            loggerHandler.start_Test(inputAnsweres,insertToFolderAnswer)
        except Exception as E:
            loggerHandler.print_To_Terminal(E.message)
            start_another_test(confFile,dirPath,loggerHandler)
        loggerHandler.print_to_Logs_Files(consts.SELECT_TO_ADD_TEST_MESSAGE + inputAnsweres + consts.SELECT_TO_ADD_FOLDER_MESSAGE + insertToFolderAnswer,True)
    else:
        loggerHandler.start_Test(inputAnsweres)       
        loggerHandler.print_to_Logs_Files(consts.SELECTED_TEST_FROM_USER_MESSAGE + inputAnsweres + " is starting now ",True)
    del insertToFolderAnswer
    cliHandler = CLIHandler(inputAnsweres,confFile,dirPath,loggerHandler,testDefinition)
    cliHandler.start()     
    flaskServer.enodeBController = ENodeBController(cliHandler.engine)
  
        
def get_Element_From_Config_File(confFile, elementName):
    return confFile.getElementsByTagName(elementName)[0].firstChild.data
    
def add_Log_Of_Test_To_Specific_Folder(loggerHandler):
    '''
    the method add the log to the specific folder if requested
    '''
    loggerHandler.print_To_Terminal(consts.ADD_TEST_TO_SPECIFIC_FOLDER_MESSAGE)
    insertToFolderAnswer = raw_input()
    while(insertToFolderAnswer.lower()!="yes" and insertToFolderAnswer.lower()!="no"):
        loggerHandler.print_To_Terminal(consts.ENTER_YES_OR_NO_MESSAGE)
        loggerHandler.print_To_Terminal(consts.ADD_TEST_TO_SPECIFIC_FOLDER_MESSAGE)
        insertToFolderAnswer = raw_input()
    return insertToFolderAnswer
            
def get_input(loggerHandler):
    answer = raw_input()
    while not answer:
        loggerHandler.print_To_Terminal(consts.EMPTY_CSV_FILE_NAME_MESSAGE)
        answer = raw_input()
    return answer
        
def stop_Thread_Due_To_Exception():
    os.sys.exit()        
        
        
            