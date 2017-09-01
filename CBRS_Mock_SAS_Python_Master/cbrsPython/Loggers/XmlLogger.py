from Loggers.LogObserver import Observer
import os
import datetime as DT
import xml.etree.cElementTree as ET
from model.Utils import Consts as consts
from controllers.CLIUtils.enums import *
import time
import calendar
import commands
import shutil
 
class XmlLogger(Observer):
    
    def __init__(self):
        self.log_Name = None
        self.startTime = DT.datetime.now()
        self.root = None
        self.testCases = None
        self.testCase = None
        self.steps = None
        self.dir_Path = None
        self.folder_Name = None
        self.currentStep = None
        self.cbsdSerial = None
 
    def startTest(self,dir_Path,log_Name,folder_Name=None):
        if(folder_Name==None or log_Name == consts.CLI_SESSION):
            return      
        elif(folder_Name!=None):
            self.folder_Name = folder_Name
            self.dir_Path = dir_Path       
            self.log_Name = log_Name
            newpath = str(dir_Path)+ str(r'\\Logs\\SpecificFolderOfTests\\' + folder_Name)
        if not os.path.exists(newpath):
            os.makedirs(newpath)
            os.makedirs(newpath + "\\chrome")
            os.makedirs(newpath + "\\fireFox")
            os.makedirs(newpath + "\\xml")
            self.build_folder_xml(dir_Path,folder_Name)
        else:
            self.initialize_From_Existing_Xml(dir_Path,folder_Name)
 
    def startStep(self,json_dict,typeOfCalling,ipRequestAddress=None):
        if(self.folder_Name==None or self.log_Name == consts.CLI_SESSION):
            return
        if(typeOfCalling==consts.REGISTRATION_SUFFIX_HTTP):
            self.cbsdSerial = json_dict[typeOfCalling+consts.REQUEST_NODE_NAME][0]["cbsdSerialNumber"]
        else:
            try:
                cbsdSerialNumberIndex = str(json_dict[typeOfCalling+consts.REQUEST_NODE_NAME][0]["cbsdId"]).index("Mock-SAS")
                self.cbsdSerial = json_dict[typeOfCalling+consts.REQUEST_NODE_NAME][0]["cbsdId"][cbsdSerialNumberIndex+len("Mock-SAS"):]
            except Exception as E:
                raise Exception("the json not include cbsdid attribute")     
        if(self.testCase == None):
            self.build_Test_Case_XML()
        self.currentStep = ET.SubElement(self.steps,"step")
        self.currentStep.set("start",str(int(self.totimestamp())))
        ET.SubElement(self.currentStep,"name").text = typeOfCalling + " CBRS : " + self.cbsdSerial
        ET.SubElement(self.currentStep,"title").text = typeOfCalling + " CBRS : " + self.cbsdSerial
        
    def finishStep(self,response,typeOfCalling,stepStatus):  
        if(self.folder_Name==None or self.log_Name == consts.CLI_SESSION):
            return  
        self.currentStep.set("status",stepStatus.value)
        self.currentStep.set("stop",str(int(self.totimestamp())))
        ET.SubElement(self.currentStep,"steps")        
        if(stepStatus.value==StepStatus.FAILED.value):
            failure = ET.SubElement(self.testCase,"failure")
            ET.SubElement(failure,"message").text = response
            ET.SubElement(failure,"stack-trace")
        
    def finishTest(self,msg,isCmdOutput,testStatus,additionalComments):
        if(self.folder_Name==None or self.log_Name == consts.CLI_SESSION):
            return
        
        if(additionalComments!=None):
            msg = msg + " and " + consts.ADDITIONAL_COMMENTS_MESSAGE + additionalComments     
            self.currentStep = ET.SubElement(self.steps,"step")
            self.currentStep.set("start",str(int(self.totimestamp())))
            ET.SubElement(self.currentStep,"name").text = "additional comment for the test are : " + additionalComments
            ET.SubElement(self.currentStep,"title").text = "additional comment for the test are : " + additionalComments
      
        self.testCase.set("status",testStatus.value)      
        self.testCase.set("stop",str(int(self.totimestamp())))
        self.set_end_time()
        tree = ET.ElementTree(self.root)
        newFolderPath = str(self.dir_Path) + "\\Logs\\SpecificFolderOfTests\\" +self.folder_Name
        tree.write(newFolderPath +"\\xml\\" + self.folder_Name+ "-testsuite" ".xml")
        allurePath = str(self.dir_Path)+ "\\allure-cli\\bin"
        os.chdir(allurePath)
        newPath = newFolderPath +"\\fireFox"
        if not os.path.exists(newPath):
            os.makedirs(newPath)
        os.system("allure generate " + newFolderPath  + " -o "+newPath)       
        self.create_Batch_File(newFolderPath,allurePath)
        
    def create_Batch_File(self,newFolderPath,allurePath):
        
        infile=open(newFolderPath + "\\chrome\\chromeReport.bat", "w")#Opens the file
        infile.write("CD " +allurePath + " \n")#Writes the desired contents to the file
        infile.write("allure report open -o " + newFolderPath+ "\\fireFox")
        infile.close()#Closes the file       
        
    def print_to_Logs_Files(self,message,isCmdOutput):
        pass
    
    def print_To_Terminal(self,message):
        pass
        
    def build_folder_xml(self,dir_Path,folder_Name):
        root = ET.Element('ns0:test-suite')
        root.set("xmlns:ns0","urn:model.allure.qatools.yandex.ru")
        root.set("start",str(int(self.totimestamp())))


        ET.SubElement(root,"name").text = folder_Name
        ET.SubElement(root,"labels")
        self.testCases = ET.SubElement(root,"test-cases")
        self.root = root
        
    def build_Test_Case_XML(self):
        self.testCase = ET.SubElement(self.testCases,"test-case")
        self.testCase.set("start",str(int(self.totimestamp())))
        ET.SubElement(self.testCase,"name").text = self.log_Name
        attachments = ET.SubElement(self.testCase,"attachments")
        attachments.set("source","59f0fe72-7489-48f3-a826-7588a4642fc8-attachment.txt")
        attachments.set("title","Captured stdout call")
        attachments.set("type","text/plain")
        label =  ET.SubElement(self.testCase,"labels")
        labelname = ET.SubElement(label,"label")
        labelname.set("name","severity")
        self.steps = ET.SubElement(self.testCase,"steps")
        
    def set_end_time(self):
        self.root.set("stop",str(int(self.totimestamp())))
        
    def initialize_From_Existing_Xml(self,dir_Path,folder_Name):
        try:
            tree = ET.parse(str(dir_Path) + "\\Logs\\SpecificFolderOfTests\\" +folder_Name +"\\xml\\" + folder_Name+"-testsuite" ".xml")
        except Exception:
            print "the folder : " + folder_Name + " , does not contains xml file you wish to delete it (enter yes or no) " 
            inputAnswer=raw_input()
            if(inputAnswer == "yes"):
                os.rmdir(str(dir_Path) + "\\Logs\\SpecificFolderOfTests\\" +folder_Name+"\\xml")
                os.rmdir(str(dir_Path) + "\\Logs\\SpecificFolderOfTests\\" +folder_Name+"\\fireFox")
                os.rmdir(str(dir_Path) + "\\Logs\\SpecificFolderOfTests\\" +folder_Name+"\\chrome")
                time.sleep(0.5)
                os.rmdir(str(dir_Path) + "\\Logs\\SpecificFolderOfTests\\" +folder_Name)
            raise IOError("The folder not contain xml file please try again")
            
        self.root = tree.getroot()
        self.testCases = tree.find("test-cases")
        self.build_Test_Case_XML()
        

    def totimestamp(self):
        epoch = DT.datetime(1970,1,1)
        i = DT.datetime.now()      
        delta_time = (i - epoch).total_seconds()
        return (delta_time -10800)*1000.0

        