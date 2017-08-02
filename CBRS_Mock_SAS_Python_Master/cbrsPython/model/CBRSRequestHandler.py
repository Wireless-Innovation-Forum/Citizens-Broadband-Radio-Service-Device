'''
Created on May 22, 2017

@author: iagmon
'''
import model.Utils.JsonComparisonUtils as jsonComparer 
import model.Utils.Consts as consts
import datetime as DT
from model.Utils.Assert import Assertion
from xml.dom import minidom
from random import *

class CBRSRequestHandler(object):
    '''
    classdocs
    '''


    def __init__(self, cbsdSerialNumber,testDefinition,EnviormentConfFile,dirPath,currentLogger):
        self.cbsdSerialNumber                   = cbsdSerialNumber
        self.repeatesAllowed                    = False
        self.repeatsType                        = None
        self.oldHttpReq                         = None
        self.validDurationTime                  = 0
        self.lastHeartBeatTime                  = None
        self.grantBeforeHeartBeat               = False
        self.validationErrorAccuredInEngine     = False
        self.isLastStepInCSV                    = False
        self.numberOfStep                       = 0
        self.numberOfHearbeatRequests           = 0
        self.loggerHandler                      = currentLogger
        self.assertion                          = None
        self.heartBeatLimitCounter              = EnviormentConfFile.getElementsByTagName("heartbeatLimit")[0].firstChild.data
        self.jsonSteps = []
        self.enviormentConfFile = EnviormentConfFile
        self.dirPath = dirPath
        self.cbrsConfFile = None
        self.measReportCounter = 0
        self.cbsdId = None
        self.grantId = 0
        self.set_Current_Json_Steps(testDefinition, EnviormentConfFile, dirPath)
        
    
    def set_Current_Json_Steps(self,testDefinition,confFile,dirPath):
        cbsdFoundInJsons = False
        for jsonCol in testDefinition.jsonNamesOfSteps:
            if jsonComparer.get_Node_Of_Json_Parsed(jsonCol[0],"registrationRequest",confFile,dirPath)[0]["cbsdSerialNumber"]== self.cbsdSerialNumber:
                cbsdFoundInJsons = True
                self.jsonSteps = jsonCol
                try:
                    self.cbrsConfFile = minidom.parse(str(self.dirPath) +"\\cbrsPython\\model\\CBRSConf\\"+ self.cbsdSerialNumber+".xml")
                except:
                    raise IOError("ERROR - missing cbrs conf file of the CBSD : " + self.cbsdSerialNumber)
                self.assertion = Assertion(self.enviormentConfFile,dirPath,self.loggerHandler,self.cbrsConfFile)
        if(not cbsdFoundInJsons):
            raise IOError("ERROR - missing registration json in one of the csv columns with the cbsd serial number " + self.cbsdSerialNumber)
            
    def handle_Http_Req(self,httpRequest,typeOfCalling):
        req = httpRequest
        if(typeOfCalling==consts.HEART_BEAT_SUFFIX_HTTP):
            if(self.assertion.is_Json_Request_Contains_Key( req, "measReportConfig")):
                del req["measReportConfig"]
        if(self.repeatsType == typeOfCalling and self.repeatesAllowed == True and self.oldHttpReq == req):#self.verify_Equal_Req_Except_Of_Operation_State(typeOfCalling,httpRequest)):
            ### in case its an heartbeat calling need to check if it is cross the limit 
            ###counter get from the config file or heartbeat call 
            ###passed the timeout that get from the last grant response         
            if(typeOfCalling == consts.HEART_BEAT_SUFFIX_HTTP):
                if(self.measReportCounter>5):
                    self.validationErrorAccuredInEngine = True
                    return "ERROR - no meas report received in the last 5 heart beats request"       
                if(int(self.numberOfHearbeatRequests)<int(self.heartBeatLimitCounter)):
                    self.numberOfHearbeatRequests+=1
                    if(not self.is_Valid_Heart_Beat_Time()):
                        self.validationErrorAccuredInEngine = True
                        return consts.HEART_BEAT_TIMEOUT_MESSAGE                      
                else:
                    self.validationErrorAccuredInEngine = True
                    return consts.HEART_BEAT_REACHED_TO_LIMIT_MESSAGE
                if self.assertion.is_Json_Request_Contains_Key(httpRequest, "measReportConfig"):
                    self.measReportCounter = 1
                else :
                    self.measReportCounter +=1
            print self.measReportCounter
            self.numberOfStep-=1### if its repeat type json number of step should be the same as it was before

        elif(self.Is_Repeats_Available(self.get_Expected_Json_File_Name(),typeOfCalling)==True):
            if(typeOfCalling == consts.SPECTRUM_INQUIERY_SUFFIX_HTTP): 
                self.Initialize_Repeats_Type_Allowed(consts.SPECTRUM_INQUIERY_SUFFIX_HTTP,httpRequest, typeOfCalling)
            elif(typeOfCalling == consts.HEART_BEAT_SUFFIX_HTTP):#need to verify that the request before was grant#    
                if(self.validDurationTime == None):
                    return consts.GRANT_BEFORE_HEARTBEAT_ERROR                  
                self.Initialize_Repeats_Type_Allowed(consts.HEART_BEAT_SUFFIX_HTTP,httpRequest, typeOfCalling)
                self.numberOfHearbeatRequests=1 
                self.lastHeartBeatTime = DT.datetime.now()  
                self.measReportCounter = 1      
        else:
            if(typeOfCalling==consts.GRANT_SUFFIX_HTTP):
                self.grantBeforeHeartBeat = True
                self.numberOfHearbeatRequests=0
            elif(typeOfCalling!=consts.HEART_BEAT_SUFFIX_HTTP):
                self.grantBeforeHeartBeat = False
                self.validDurationTime = 0
                self.numberOfHearbeatRequests=0
            elif(typeOfCalling==consts.HEART_BEAT_SUFFIX_HTTP):
                ### checks that heartbeat request has been sent only after grant or another heartbeat
                if(not self.grantBeforeHeartBeat):
                    self.validationErrorAccuredInEngine = True
                    return consts.GRANT_BEFORE_HEARTBEAT_ERROR 
            self.repeatesAllowed = False
            self.repeatsType = None              
        try:
                self.compare_Json_Req(httpRequest,self.get_Expected_Json_File_Name(),typeOfCalling)  
                    
        except Exception as e:
            self.validationErrorAccuredInEngine = True  
            return e.message
        if(typeOfCalling==consts.GRANT_SUFFIX_HTTP):
            ### if it is a grant request we need to initialize the valid duration time between the heartbeats
            self.validDurationTime = self.assertion.get_Duration_Time_From_Grant_Json(self.get_Expected_Json_File_Name())
        self.oldHttpReq = httpRequest
        ## relinquish is too fast and sent request before entering the loop of new test  
        if(self.validationErrorAccuredInEngine == False):     
            return self.process_response(typeOfCalling,httpRequest)
        
        
    def Is_Repeats_Available(self,expectedJsonName,typeOfCalling):
        '''
        the method checks if the calling is a heartbeat or spectrum type and get the repeatsAllowed value from the expectedJson
        '''
        if(typeOfCalling!= consts.HEART_BEAT_SUFFIX_HTTP and typeOfCalling!= consts.SPECTRUM_INQUIERY_SUFFIX_HTTP):
            return False
        return bool(self.assertion.get_Attribute_Value_From_Json(expectedJsonName,"repeatsAllowed"))

    def compare_Json_Req(self,httpRequest,expectedJsonFileName,typeOfCalling,keys=None):
        self.assertion.compare_Json_Req(httpRequest,expectedJsonFileName,typeOfCalling+consts.REQUEST_NODE_NAME,keys)
    
    def parse_Json_To_Dic_By_File_Name(self,jsonFileName,nodeName,confFile):
        try:
            return jsonComparer.get_Node_Of_Json_Parsed(jsonFileName,nodeName,confFile,self.dirPath)
        except Exception as e:
            if e.message == "node not exists":
                return consts.SUFFIX_NOT_EXISTS_IN_EXPECTED_JSON_FILE
    
    def get_Expected_Json_File_Name(self,numberOfStep = None):
        if(numberOfStep == None):
            numberOfStep = self.numberOfStep
        return self.jsonSteps[numberOfStep]
    
    def get_Question_Answer_Part(self):
        return self.questAnswerPartOfJson
    
    def Initialize_Repeats_Type_Allowed(self,repeatType, httpRequest, typeOfCalling):
        '''
        the method initialize the repeat type and the boolean that indicates that repeats are allowed
        '''
        self.repeatsType = repeatType
        self.repeatesAllowed = True
        
    def is_Valid_Heart_Beat_Time(self):
        ''''
        the method get the current time and compare the time that had passed from the last heartbeat
        check if it is less then what pulled from the last grant response
        '''
        currentTime = DT.datetime.now()
        timeBetween = (currentTime-self.lastHeartBeatTime).total_seconds()
        print str(timeBetween)
        if(float(timeBetween)-3.0>float(self.validDurationTime)):
            return False
        self.lastHeartBeatTime = DT.datetime.now()            
        return True
    
    
    def process_response(self,typeOfCalling,httpRequest):  
        jsonAfterParse = self.parse_Json_To_Dic_By_File_Name(self.get_Expected_Json_File_Name(),consts.RESPONSE_NODE_NAME,self.enviormentConfFile)
        specificRespJson = jsonAfterParse[typeOfCalling+consts.RESPONSE_NODE_NAME.title()][0]
        if(typeOfCalling == consts.SPECTRUM_INQUIERY_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson,"cbsdId",self.cbsdId)
        elif (typeOfCalling == consts.RELINQUISHMENT_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId) 
            self.change_Value_Of_Param_In_Dict(specificRespJson, "grantId", self.grantId)  
        elif(typeOfCalling == consts.GRANT_SUFFIX_HTTP):
            if(self.grantId == 0) :
                self.grantId = randint(1, 1000000000)  
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.grantId) 
            self.change_Value_Of_Param_In_Dict(specificRespJson, "grantId", self.grantId)             
            result = self.get_Expire_Time()
            self.change_Value_Of_Param_In_Dict(specificRespJson, "grantExpireTime", result)  
        elif(typeOfCalling == consts.HEART_BEAT_SUFFIX_HTTP):
            if(self.measReportCounter>1):
                if("measReportConfig" in specificRespJson):
                    del specificRespJson["measReportConfig"]
            result = self.get_Expire_Time()
            self.change_Value_Of_Param_In_Dict(specificRespJson, "transmitExpireTime", result)
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId) 
            self.change_Value_Of_Param_In_Dict(specificRespJson, "grantId", self.grantId)  
        elif(typeOfCalling == consts.REGISTRATION_SUFFIX_HTTP):
            if(self.cbsdId==None):
                self.cbsdId = httpRequest["fccId"]+ "Mock-SAS" + self.cbsdSerialNumber
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId)   
            
        if(len(self.jsonSteps) == self.numberOfStep+1):
            self.questAnswerPartOfJson = self.parse_Json_To_Dic_By_File_Name(self.get_Expected_Json_File_Name(),consts.QUESTION_NODE_NAME,self.enviormentConfFile)
            self.isLastStepInCSV = True  
        self.numberOfStep+=1
        return jsonAfterParse
    
    def change_Value_Of_Param_In_Dict(self,dictName,attrToChange,value):
        if(attrToChange in dictName):
                del dictName[attrToChange]
        jsonComparer.ordered_dict_prepend(dictName, attrToChange, value) 
    
    def get_Expire_Time(self):
        secondsToAdd = int(self.cbrsConfFile.getElementsByTagName("secondsToAddForExpireTime")[0].firstChild.data)
        currentDateTime = DT.datetime.utcnow()
        
        if(int(secondsToAdd) <60):
            currentDateTime = currentDateTime + DT.timedelta(seconds = 30)
        elif(int(secondsToAdd)<3600):
            currentDateTime = currentDateTime + DT.timedelta(seconds = secondsToAdd%60 , minutes = int(secondsToAdd/60))
        elif(int(secondsToAdd)<86400):
            currentDateTime = currentDateTime + DT.timedelta(seconds = secondsToAdd%60)
            minutesToAdd = secondsToAdd/60
            if(minutesToAdd<60):
                currentDateTime = currentDateTime + DT.timedelta(minutes = minutesToAdd)
            else:
                currentDateTime = currentDateTime + DT.timedelta(minutes = minutesToAdd%60,hours = minutesToAdd/60)
        
            
        currentDateTime = str(currentDateTime)[:-4]
        currentDateTime = str(currentDateTime).replace(" ", "T")   
        currentDateTime = str(currentDateTime).replace(currentDateTime, currentDateTime+"Z") 
        return currentDateTime
        