import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from controllers.CLIUtils.TestDefinition import TestDefinition
import model.Utils.Consts as consts
from xml.dom import minidom
from controllers.CLIHandler import CLIHandler
from controllers.ENodeBController import ENodeBController
from model import flaskServer
from pathlib import Path
from controllers.CLIHandler import CsvFileParser
from Loggers.LoggerObserver import loggerObserver
from Loggers.CmdLogger import CmdLogger
from Loggers.DebugLogger import DebugLogger
from Loggers.XmlLogger import XmlLogger
import ssl

def add_Log_Of_Test_To_Specific_Folder(loggerHandler):
    '''
    the method insure that the question if the test should be added to the folder will be yes or no only
    '''
    loggerHandler.print_To_Terminal(consts.ADD_TEST_TO_SPECIFIC_FOLDER_MESSAGE)
    insertToFolderAnswer = raw_input().lower()
    while(insertToFolderAnswer.lower()!="yes" and insertToFolderAnswer.lower()!="no"):
        loggerHandler.print_To_Terminal(consts.ENTER_YES_OR_NO_MESSAGE)
        loggerHandler.print_To_Terminal(consts.ADD_TEST_TO_SPECIFIC_FOLDER_MESSAGE)
        insertToFolderAnswer = raw_input()
    return insertToFolderAnswer

def get_input():
    '''
    the method insure that the input will not be an empty line
    '''
    answer = raw_input()
    while not answer:
        loggerHandler.print_To_Terminal(consts.EMPTY_CSV_FILE_NAME_MESSAGE)
        answer = raw_input()
    return answer
        

def run_New_Test(dirPath, confFile, loggerHandler): 
    '''
    The method start a new test asking the technician which csv file to load from the test repository 
    create a new log file for the test in allTest folder and create if wanted specific log for the test in specific folder 
    that the technician will choose
    running the flask server using the port and ip taken from the config file   
    '''
    loggerHandler.start_Test(consts.CLI_SESSION)
    loggerHandler.print_To_Terminal(consts.SET_CSV_FILE_MESSAGE)
    inputAnswer = get_input()
    if(inputAnswer!="quit"):
        try: ### initialize the test definition from the csv file 
            csvFileParser = CsvFileParser(str(dirPath) + confFile.getElementsByTagName("testRepoPath")[0].firstChild.data + inputAnswer,confFile,dirPath)
            testDefinition = TestDefinition(csvFileParser.initializeTestDefinition(),csvFileParser.find_Number_Of_Cols())
        except IOError as e:  ### in case there is file not found error try to enter new csv file name
            loggerHandler.print_To_Terminal(e.message)
            run_New_Test(dirPath, confFile, loggerHandler)
        
        insertToFolderAnswer = add_Log_Of_Test_To_Specific_Folder(loggerHandler)
        if (insertToFolderAnswer == "yes"):
            loggerHandler.print_To_Terminal(consts.TYPE_NAME_OF_FOLDER)
            insertToFolderAnswer = raw_input()
            try:
                loggerHandler.start_Test(inputAnswer, insertToFolderAnswer) ### if decided to enter to folder create two logs one in the all test folder ### if decided to enter to folder create two logs one in the all test folder
            except Exception as E:
                loggerHandler.print_To_Terminal(E.message)
                run_New_Test(dirPath, confFile, loggerHandler)
            loggerHandler.print_to_Logs_Files(consts.SELECT_TO_ADD_TEST_MESSAGE+ inputAnswer + consts.SELECT_TO_ADD_FOLDER_MESSAGE 
                                                + insertToFolderAnswer, True)
        else:
            loggerHandler.start_Test(inputAnswer)
            loggerHandler.print_to_Logs_Files(consts.SELECTED_TEST_FROM_USER_MESSAGE + str(inputAnswer), True)
        cliHandler = CLIHandler(inputAnswer, confFile, dirPath, loggerHandler,testDefinition) ### initialize cli session handler
        flaskServer.enodeBController = ENodeBController(cliHandler.engine)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2) # use TLS to avoid POODLE
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.load_verify_locations(str(dirPath) + cliHandler.get_Element_From_Config_File("caCerts"))
        ctx.load_cert_chain(str(dirPath) + cliHandler.get_Element_From_Config_File("pemFilePath"), str(dirPath) + cliHandler.get_Element_From_Config_File("keyFilePath"))## get the certificates for https from config file
        cliHandler.server = flaskServer.runFlaskServer(cliHandler.get_Element_From_Config_File("hostIp"),cliHandler.get_Element_From_Config_File("port"),ctx) ### run flask server using the host name and port  from conf file
        if (cliHandler.engine.check_Validation_Error()):
            cliHandler.stop_Thread_Due_To_Exception()
    if(inputAnswer=="quit"):
        loggerHandler.print_To_Terminal(consts.QUIT_PROGRAM_MESSAGE)
        

def create_Log_Folder():
    
    '''
    the method create logs folder with three folder inside if the folder not created already
    '''
    logsFolderPath = str(dirPath)+"\\Logs"
    if not os.path.exists(logsFolderPath):
            os.makedirs(logsFolderPath)
            os.makedirs(logsFolderPath + "\\SpecificFolderOfTests")
            os.makedirs(logsFolderPath + "\\LogsPerTest")
            os.makedirs(logsFolderPath + "\\CMDSessions")

def initialize_Reports():
    '''
    the method insert the loggers to the logger observer
    '''
    cmdLogger = CmdLogger()
    loggerHandler.register(cmdLogger)
    xmlLogger = XmlLogger()
    loggerHandler.register(xmlLogger)
    
    debugLogger = DebugLogger()
    loggerHandler.register(debugLogger)

current_path = os.path.dirname(os.path.realpath(__file__))
dirPath = Path(__file__).parents[2]
create_Log_Folder()
confFile= minidom.parse(current_path +"\conf.xml") 
loggerHandler = loggerObserver(dirPath)
initialize_Reports()
run_New_Test(dirPath, confFile, loggerHandler)

''' exampleTest.csv'''
'''exampleTestWithRegistration.csv'''
'''grantFailureTest'''