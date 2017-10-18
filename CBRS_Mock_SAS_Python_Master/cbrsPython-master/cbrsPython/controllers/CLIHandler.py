'''
Created on Apr 24, 2017

@author: iagmon
'''
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
import ssl
from controllers.CLIUtils.enums import TestStatus
from flask import Flask,request,jsonify,g,redirect,url_for,abort
import os
from OpenSSL import SSL, crypto

def verify_cb(conn, cert, errnum, depth, ok):
    # Dummy call back function.
    # loggerHandler.print_to_Logs_Files('Got certificate: {}'.format(cert.get_subject()),True)
    pass
    return ok

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
        self.start()
        
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
            time.sleep(1)## for initialize the xml report
            self.loggerHandler.print_to_Logs_Files(consts.NSTEP_SESSION_WITH_TECHNITIAN,True)
            finalResults = self.questHandler.ShowQuestionsAndGetAnswersFromClient(self.engine.get_Question_Answer_Part())
            self.test_Finish_Message_For_Logs(finalResults)        
            self.start_another_test(self)
        else:
            self.loggerHandler.finish_Test(consts.RESULTS_OF_TEST_MESSAGE +self.testName +  " is - " + consts.FAIL_MESSAGE,True,TestStatus.FAILED)
            self.start_another_test(self)
        
    def start_another_test(self,cliHandler): 
        '''
        as same as in the startOfProject.py 
        initialize new logger for each test and if requested to the specific folder
        stop the last reports of the test running before the new test
        and running a new instance of the flask server  
        '''    
        inputAnsweres = None
        time.sleep(1)        
        self.loggerHandler.print_To_Terminal(consts.SET_CSV_FILE_MESSAGE)
        inputAnsweres=self.get_input()
        if (inputAnsweres !="quit"):
            try:
                csvFileParser = CsvFileParser(str(self.dirPath) + self.confFile.getElementsByTagName("testRepoPath")[0].firstChild.data + inputAnsweres,self.confFile,self.dirPath)
                self.testDefinition = TestDefinition(csvFileParser.initializeTestDefinition(),csvFileParser.find_Number_Of_Cols())
            except IOError as e:
                self.loggerHandler.print_To_Terminal(e.message)
                self.start_another_test(cliHandler)
            #self.loggerHandler.remove_Test_File_Logger()
            insertToFolderAnswer = self.add_Log_Of_Test_To_Specific_Folder()
            if (insertToFolderAnswer == "yes"):
                self.loggerHandler.print_To_Terminal(consts.TYPE_NAME_OF_FOLDER)
                insertToFolderAnswer = raw_input()
                try:
                    self.loggerHandler.start_Test(inputAnsweres,insertToFolderAnswer)
                except Exception as E:
                    self.loggerHandler.print_To_Terminal(E.message)
                    self.start_another_test(cliHandler)
                self.loggerHandler.print_to_Logs_Files(consts.SELECT_TO_ADD_TEST_MESSAGE + inputAnsweres + consts.SELECT_TO_ADD_FOLDER_MESSAGE + insertToFolderAnswer,True)
            else:
                self.loggerHandler.start_Test(inputAnsweres)
                self.loggerHandler.print_to_Logs_Files(consts.SELECTED_TEST_FROM_USER_MESSAGE + inputAnsweres +  " is starting now ",True)
            del insertToFolderAnswer
            cliHandler = CLIHandler(inputAnsweres,self.confFile,self.dirPath,self.loggerHandler,self.testDefinition) 
            flaskServer.enodeBController = ENodeBController(cliHandler.engine)
            ## Saurabh -- Changing socket context. Using PyOpenSSL instead of SSL
        
            # New code begins
            ctx2 = SSL.Context(SSL.TLSv1_2_METHOD)
            ctx2.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb) # Demand a certificate
            ctx2.use_privatekey_file (str(self.dirPath) + cliHandler.get_Element_From_Config_File("keyFilePath"))
            ctx2.use_certificate_file(str(self.dirPath) + cliHandler.get_Element_From_Config_File("pemFilePath"))
            ctx2.load_verify_locations(str(self.dirPath) + cliHandler.get_Element_From_Config_File("caCerts"))
            certStore = ctx2.get_cert_store()
            certStore.set_flags(crypto.X509StoreFlags().IGNORE_CRITICAL)
            # New code ends
            
            flaskServer.runFlaskServer(self.get_Element_From_Config_File("hostIp"),\
                                       self.get_Element_From_Config_File("port"),\
                                       ctx2)     # Changed ctx to ctx2
        if(cliHandler.engine.validationErrorAccuredInEngine):
            cliHandler.stop_Thread_Due_To_Exception()
        if(inputAnsweres=="quit"):
            self.loggerHandler.print_To_Terminal(consts.GOODBYE_MESSAGE)
        
        
    def get_Element_From_Config_File(self,elementName):
        return self.confFile.getElementsByTagName(elementName)[0].firstChild.data
    
    def add_Log_Of_Test_To_Specific_Folder(self):
        '''
        the method add the log to the specific folder if requested
        '''
        self.loggerHandler.print_To_Terminal(consts.ADD_TEST_TO_SPECIFIC_FOLDER_MESSAGE)
        insertToFolderAnswer = raw_input()
        while(insertToFolderAnswer.lower()!="yes" and insertToFolderAnswer.lower()!="no"):
            self.loggerHandler.print_To_Terminal(consts.ENTER_YES_OR_NO_MESSAGE)
            self.loggerHandler.print_To_Terminal(consts.ADD_TEST_TO_SPECIFIC_FOLDER_MESSAGE)
            insertToFolderAnswer = raw_input()
        return insertToFolderAnswer
            
    def get_input(self):
        answer = raw_input()
        while not answer:
            self.loggerHandler.print_To_Terminal(consts.EMPTY_CSV_FILE_NAME_MESSAGE)
            answer = raw_input()
        return answer
        
        
            
