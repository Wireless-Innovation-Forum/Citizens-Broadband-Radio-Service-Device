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
import os
from time import sleep
import json
import jsonschema
import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
import base64


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
        self.secondLastHeartBeatTime            = None
        self.grantBeforeHeartBeat               = False
        self.validationErrorAccuredInEngine     = False
        self.isLastStepInCSV                    = False
        self.numberOfStep                       = 0
        self.numberOfHearbeatRequests           = 0
        self.loggerHandler                      = currentLogger
        self.assertion                          = None
        self.heartBeatLimitCounter              = EnviormentConfFile.getElementsByTagName("heartbeatLimit")[0].firstChild.data
        self.jsonSteps                          = []
        self.spectrumInquieryAvailableRepeatsEveryWhereRequest =[]
        self.enviormentConfFile                 = EnviormentConfFile
        self.dirPath                            = dirPath
        self.cbrsConfFile                       = None
        self.cbsdId                             = None
        self.grantId                            = 0
        self.expectedRelBeforeDeragistration    = False
        self.isDelayTriggered                   = False
        self.delayEndTime                       = DT.datetime.utcnow()                                       
        self.secondsForDelay                    = 0                                            
        self.isMeasRepRequested                 = False                                        
        self.stopGrantRenew                     = False                                                
        self.measReportCounter                  = 0    
        self.heartbeatErrorList                 = [500, 501, 502, 105] 
        self.immediatelyShutdown                = False 
        self.shorterGrantTime                   = False 
        self.postErrorMessage                   = False     
        self.set_Current_Json_Steps(testDefinition, EnviormentConfFile, dirPath)         
        
    
    def set_Current_Json_Steps(self,testDefinition,confFile,dirPath):
        cbsdFoundInJsons = False
        for jsonCol in testDefinition.jsonNamesOfSteps:
            xmlFileLinked = jsonComparer.get_Node_Of_Json_Parsed(jsonCol[0],"xmlFilelLinked",confFile,dirPath)
            xmlPath = os.path.join(str(self.dirPath), "Configuration", "CBSDconfig", xmlFileLinked+".xml")
            if os.path.exists(xmlPath)==False:
                raise IOError("ERROR - missing cbrs conf file of the CBSD : " + self.cbsdSerialNumber)
            self.cbrsConfFile = minidom.parse(xmlPath)
            
            if str(self.cbrsConfFile.getElementsByTagName("cbsdSerialNumber")[0].firstChild.data).replace('"',"")  == self.cbsdSerialNumber :
                cbsdFoundInJsons = True
                self.jsonSteps = jsonCol
                self.assertion = Assertion(self.enviormentConfFile,dirPath,self.loggerHandler,self.cbrsConfFile)  
                            
        if(not cbsdFoundInJsons):
            raise IOError("ERROR - missing registration json in one of the csv columns with the cbsd serial number " + self.cbsdSerialNumber)

        grantExpireTime = int(consts.SECONDS_TO_ADD_FOR_GRANT_EXPIRE_TIME)
        transmitTime = int(consts.SECONDS_TO_ADD_FOR_TX_EXPIRE_TIME)
        if(grantExpireTime<transmitTime):
            raise IOError("ERROR - for the cbrs with the serial number : " + self.cbsdSerialNumber +  " the transmit time is bigger than the grant expire time")
        
        for availableInqueryStep in self.jsonSteps:
            currentJson = self.parse_Json_To_Dic_By_File_Name(availableInqueryStep,consts.SPECTRUM_INQUIERY_SUFFIX_HTTP + consts.REQUEST_NODE_NAME,self.enviormentConfFile)
            if currentJson != None:
                if bool(self.assertion.get_Attribute_Value_From_Json(availableInqueryStep, "appearAlways")) == True:
                    self.spectrumInquieryAvailableRepeatsEveryWhereRequest.append(availableInqueryStep)
        for step in self.spectrumInquieryAvailableRepeatsEveryWhereRequest:
            self.jsonSteps.remove(step)
                                        
            
    def handle_Http_Req(self,httpRequest,typeOfCalling):
        
        req = httpRequest
        if(self.isDelayTriggered==True):                                                                                                        
            current_time = DT.datetime.utcnow()
            deltaT = self.delayEndTime - current_time
            remainingTimeToSleep = int(deltaT.total_seconds()) + 5      # sleep until HBT absent is over, plus extra 5 sec
            if remainingTimeToSleep <= 0:
                remainingTimeToSleep = 1
            self.loggerHandler.print_to_Logs_Files('request message received while HBT is absent, sleep '+str(remainingTimeToSleep)+' sec before responding', False)                                                                                                        
            sleep(remainingTimeToSleep)                                                                                                                                                                                                    
        
        if(bool(self.assertion.get_Attribute_Value_From_Json(self.get_Expected_Json_File_Name(),"noMoreStep"))==True):          
            self.isLastStepInCSV = True                  

        if(bool(self.assertion.get_Attribute_Value_From_Json(self.get_Expected_Json_File_Name(),"shorterGrantTime"))==True):          
            self.shorterGrantTime = True 
            
        if(bool(self.assertion.get_Attribute_Value_From_Json(self.get_Expected_Json_File_Name(),"postErrorMessage"))==True):          
            self.postErrorMessage = True                
                                
        if(typeOfCalling == consts.SPECTRUM_INQUIERY_SUFFIX_HTTP):
            for jsonFile in self.spectrumInquieryAvailableRepeatsEveryWhereRequest:
                try:
                    self.assertion.compare_Json_Req(httpRequest, jsonFile, consts.SPECTRUM_INQUIERY_SUFFIX_HTTP+consts.REQUEST_NODE_NAME,None,False)
                    return self.returnSpectInquieryInCaseOfRepeatsAllowedAlwaysValidationSucceed(jsonFile,httpRequest)
                except Exception as e:
                    self.validationErrorAccuredInEngine = True  
                    raise IOError (str(e))   
        
        if(typeOfCalling==consts.HEART_BEAT_SUFFIX_HTTP): 

            if(self.lastHeartBeatTime != None):
                if(not self.is_Valid_Heart_Beat_Time()):
                    self.validationErrorAccuredInEngine = True
                    return consts.HEART_BEAT_TIMEOUT_MESSAGE
            else:
                self.lastHeartBeatTime = DT.datetime.utcnow()   
		
            if(bool(self.assertion.get_Attribute_Value_From_Json(self.get_Expected_Json_File_Name(),"measReportRequested"))==True):         
                self.isMeasRepRequested = True
                    
            if(bool(self.assertion.get_Attribute_Value_From_Json(self.get_Expected_Json_File_Name(),"stopGrantRenewFlag"))==True):          
                self.stopGrantRenew = True                                                                                                               

            if(bool(self.assertion.get_Attribute_Value_From_Json(self.get_Expected_Json_File_Name(),"immediatelyShutdown"))==True):          
                self.immediatelyShutdown = True                     
            
            if(self.isMeasRepRequested == True):                                                                                            
                if(self.assertion.is_Json_Request_Contains_Key(httpRequest, "measReport")):                                                 
                    self.measReportCounter = 1                                                                                              
                else :                                                                                                                      
                    self.measReportCounter +=1                                                                                              
                print self.measReportCounter                                                                                                

            if(self.measReportCounter>5):                                                                                                   
                self.validationErrorAccuredInEngine = True                                                                                  
                return "ERROR - no meas report received in the last 5 heart beats request"                                                      
                    
        if(typeOfCalling == consts.RELINQUISHMENT_SUFFIX_HTTP):
            self.expectedRelBeforeDeragistration =  self.verify_If_Rel_Before_Deregistration_Expected()
            
        if(typeOfCalling == consts.DEREGISTRATION_SUFFIX_HTTP):
            self.numberOfStep = (len(self.jsonSteps)-1)             
            
        if(self.repeatsType == typeOfCalling and self.repeatesAllowed == True and self.oldHttpReq == req):
            ### in case its an heartbeat calling need to check if it is cross the limit 
            ###counter get from the config file or heartbeat call 
            ###passed the timeout that get from the last grant response         
            if(typeOfCalling == consts.HEART_BEAT_SUFFIX_HTTP):                                                                           
                if(int(self.numberOfHearbeatRequests)<int(self.heartBeatLimitCounter)):
                    self.numberOfHearbeatRequests+=1
                else:
                    self.validationErrorAccuredInEngine = True
                    return consts.HEART_BEAT_REACHED_TO_LIMIT_MESSAGE
            self.numberOfStep-=1
            ### if its repeat type json number of step should be the same as it was before

        
        elif(self.Is_Repeats_Available(self.get_Expected_Json_File_Name(),typeOfCalling)==True):
            
            if(typeOfCalling == consts.SPECTRUM_INQUIERY_SUFFIX_HTTP): 
                self.Initialize_Repeats_Type_Allowed(consts.SPECTRUM_INQUIERY_SUFFIX_HTTP,httpRequest, typeOfCalling)
            
            elif(typeOfCalling == consts.HEART_BEAT_SUFFIX_HTTP):
                #need to verify that the request before was grant#                                                          
                if(self.validDurationTime == None):
                    return consts.GRANT_BEFORE_HEARTBEAT_ERROR                  
                self.Initialize_Repeats_Type_Allowed(consts.HEART_BEAT_SUFFIX_HTTP,httpRequest, typeOfCalling)
                self.numberOfHearbeatRequests=1 
                self.lastHeartBeatTime = DT.datetime.utcnow()
                self.secondLastHeartBeatTime = self.lastHeartBeatTime      
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
            raise IOError (str(e))
        # Check CPI data in registration message, if present...                                                                                                              
        if(typeOfCalling == consts.REGISTRATION_SUFFIX_HTTP):
            if 'cpiSignatureData' in httpRequest:
                if 'installationParam' in httpRequest:
                    self.loggerHandler.print_to_Logs_Files("ERROR: cpiSignatureData and installationParam exist in same registration message ", True)
                    self.validationErrorAccuredInEngine = True
                    raise IOError ("failure -- cpiSignatureData and installationParam exist in same registration message")
                elif 'cbsdCategory' in httpRequest:
                    if self.checkCpiSignedData(dict(httpRequest['cpiSignatureData']), httpRequest['cbsdCategory']) == False:
                        self.validationErrorAccuredInEngine = True
                        raise IOError ("cpiSignature check failed")
                else:
                    self.loggerHandler.print_to_Logs_Files("cbsdCategory missing, can't check cpi data against json schema", True)
                    self.validationErrorAccuredInEngine = True
                    raise IOError ("cpiSignature check failed -- no cbsdCategory in Reg request")
                    
        if(typeOfCalling==consts.GRANT_SUFFIX_HTTP):
            ### if it is a grant request we need to initialize the valid duration time between the heartbeats
            self.validDurationTime = self.assertion.get_Duration_Time_From_Grant_Json(self.get_Expected_Json_File_Name())
        self.oldHttpReq = httpRequest
        ## relinquish is too fast and sent request before entering the loop of new test  
        if(self.validationErrorAccuredInEngine == False):     
            return self.process_response(typeOfCalling,httpRequest)
     
    def verify_If_Rel_Before_Deregistration_Expected(self):
        currentJsonExpectedByCSV = self.parse_Json_To_Dic_By_File_Name(self.get_Expected_Json_File_Name(),consts.RESPONSE_NODE_NAME,self.enviormentConfFile)
        if(consts.RELINQUISHMENT_SUFFIX_HTTP not in currentJsonExpectedByCSV):
            if(consts.DEREGISTRATION_SUFFIX_HTTP+consts.RESPONSE_NODE_NAME.title() in currentJsonExpectedByCSV):
                return True
        return False
    
    def returnSpectInquieryInCaseOfRepeatsAllowedAlwaysValidationSucceed(self,expectedJsonName,httpRequest):
        jsonAfterParse = self.parse_Json_To_Dic_By_File_Name(expectedJsonName,consts.RESPONSE_NODE_NAME,self.enviormentConfFile)
        specificRespJson = jsonAfterParse[consts.SPECTRUM_INQUIERY_SUFFIX_HTTP+consts.RESPONSE_NODE_NAME.title()][0]
        self.change_Value_Of_Param_In_Dict(specificRespJson,"cbsdId",self.cbsdId)
        self.processSpectrumInquiryResponse(specificRespJson,httpRequest)        
        return jsonAfterParse
        
    def is_Absent_Response_Set(self,expectedJsonName):                                            
        theFlag = (bool(self.assertion.get_Attribute_Value_From_Json(expectedJsonName,"isAbsentResponse")))     
        if theFlag == True:                                                                                     
            self.isDelayTriggered = True
            self.delayEndTime = DT.datetime.utcnow() + DT.timedelta(seconds = self.secondsForDelay)
            if self.secondLastHeartBeatTime != None:
                self.loggerHandler.print_to_Logs_Files('LAST HBT RESPONSE THAT SET TRANSMIT_EXPIRE_TIME WAS AT:  '+str(self.secondLastHeartBeatTime), True)                                                                      
            return True                                                                                                     
        
    def Is_Repeats_Available(self,expectedJsonName,typeOfCalling):
        '''
        the method checks if the calling is a heartbeat or spectrum type and get the repeatsAllowed value from the expectedJson
        '''
        if(typeOfCalling!= consts.HEART_BEAT_SUFFIX_HTTP and typeOfCalling!= consts.SPECTRUM_INQUIERY_SUFFIX_HTTP):
            return False
        return bool(self.assertion.get_Attribute_Value_From_Json(expectedJsonName,"repeatsAllowed"))

    def compare_Json_Req(self,httpRequest,expectedJsonFileName,typeOfCalling,keys=None):
        self.secondsForDelay = int(consts.SECONDS_FOR_DELAY_RESPONSE)
        if(not self.is_Absent_Response_Set(self.get_Expected_Json_File_Name())==True):                                      
            self.assertion.compare_Json_Req(httpRequest,expectedJsonFileName,typeOfCalling+consts.REQUEST_NODE_NAME,keys)           

        else:                                                                                                                       
            sleep(self.secondsForDelay)                                                                                             
            self.assertion.compare_Json_Req(httpRequest,expectedJsonFileName,typeOfCalling+consts.REQUEST_NODE_NAME,keys)                  
    
    def parse_Json_To_Dic_By_File_Name(self,jsonFileName,nodeName,confFile):
        try:
            return jsonComparer.get_Node_Of_Json_Parsed(jsonFileName,nodeName,confFile,self.dirPath)
        except Exception as e:
            if e.message == "node not exists":
                return consts.SUFFIX_NOT_EXISTS_IN_EXPECTED_JSON_FILE
    
    def get_Expected_Json_File_Name(self,numberOfStep = None):
        if(self.expectedRelBeforeDeragistration):
            return "rel_In_Case_Of_Deregistration.json"
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
        currentTime = DT.datetime.utcnow()
        timeBetween = (currentTime-self.lastHeartBeatTime).total_seconds()
        self.loggerHandler.print_to_Logs_Files("The time interval between two heartbeat request messages is " + str(timeBetween), False)        
        if(float(timeBetween)>float(self.validDurationTime)):
            return False
        self.secondLastHeartBeatTime=  self.lastHeartBeatTime
        self.lastHeartBeatTime = DT.datetime.utcnow()            
        return True
  
    def process_response(self,typeOfCalling,httpRequest): 
        jsonAfterParse = self.parse_Json_To_Dic_By_File_Name(self.get_Expected_Json_File_Name(),consts.RESPONSE_NODE_NAME,self.enviormentConfFile)
        
        if len(jsonAfterParse) > 1:
            for item in jsonAfterParse.iteritems():
                if item[0] != typeOfCalling+consts.RESPONSE_NODE_NAME.title():
                    del jsonAfterParse[item[0]]
        specificRespJson = jsonAfterParse[typeOfCalling+consts.RESPONSE_NODE_NAME.title()][0]
        
        if(typeOfCalling == consts.SPECTRUM_INQUIERY_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson,"cbsdId",self.cbsdId)
            self.processSpectrumInquiryResponse(specificRespJson,httpRequest)
                        
        elif (typeOfCalling == consts.RELINQUISHMENT_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId) 
            self.change_Value_Of_Param_In_Dict(specificRespJson, "grantId", self.grantId) 
            if specificRespJson['response']['responseCode'] == 102 or specificRespJson['response']['responseCode'] == 103:
                if 'responseData' in specificRespJson['response']:
                    if 'cbsdId' in specificRespJson['response']['responseData']:
                        del specificRespJson['cbsdId']
                        del specificRespJson['grantId']
                    elif 'grantId' in specificRespJson['response']['responseData']:
                        del specificRespJson['grantId']
                    else:
                        pass    # responseCode = 102 or 103, responseData exists, but not 'cbsdId' or 'grantId'... what to do?  Currently keeps cbsdId and grantId in response
                else:
                    pass    # responseCode = 102 or 103, responseData doesn't exist.  What to do?  Currently keeps cbsdId and grantId in response

        elif(typeOfCalling == consts.GRANT_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId) 
            self.processGrantResponse(specificRespJson,httpRequest)            
                        
        elif(typeOfCalling == consts.HEART_BEAT_SUFFIX_HTTP):
            if specificRespJson["response"]["responseCode"] in self.heartbeatErrorList or self.immediatelyShutdown == True:
                secondsToAdd = 0
            else:
                secondsToAdd = int(consts.SECONDS_TO_ADD_FOR_TX_EXPIRE_TIME)
            result = self.get_Expire_Time(secondsToAdd,specificRespJson)
            self.change_Value_Of_Param_In_Dict(specificRespJson, "transmitExpireTime", result)
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId) 
            self.change_Value_Of_Param_In_Dict(specificRespJson, "grantId", self.grantId)
            if("grantRenew" in httpRequest and self.stopGrantRenew == False):                                                           
                if(httpRequest["grantRenew"] == True or httpRequest["grantRenew"]=="true"):
                    if self.shorterGrantTime == False:
                        secondsToAdd = consts.SECONDS_TO_ADD_FOR_GRANT_EXPIRE_TIME
                    else:
                        secondsToAdd = consts.SHORTER_GRANT_EXPIRY_TIME
                    result = self.get_Expire_Time(secondsToAdd)
                    self.change_Value_Of_Param_In_Dict(specificRespJson, "grantExpireTime", result)
                      
        elif(typeOfCalling == consts.REGISTRATION_SUFFIX_HTTP):
            if specificRespJson['response']['responseCode'] == 0:
                if(self.cbsdId==None):
                    self.cbsdId = httpRequest["fccId"]+ "Mock-SAS" + self.cbsdSerialNumber
                    self.assertion.cbsdId = self.cbsdId
                self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId)
            elif 'cbsdId' in specificRespJson:
                del specificRespJson['cbsdId']
                  
        elif(typeOfCalling == consts.DEREGISTRATION_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId)  
        
        if(self.expectedRelBeforeDeragistration == True):
            self.numberOfStep-=1
            self.expectedRelBeforeDeragistration = False
        
        if(len(self.jsonSteps) == self.numberOfStep+1 or self.isLastStepInCSV == True):
            self.questAnswerPartOfJson = self.parse_Json_To_Dic_By_File_Name(self.get_Expected_Json_File_Name(),consts.QUESTION_NODE_NAME,self.enviormentConfFile)
            self.isLastStepInCSV = True  
        
        self.numberOfStep+=1
        return jsonAfterParse
    
    def change_Value_Of_Param_In_Dict(self,dictName,attrToChange,value):
        if(attrToChange in dictName):
                del dictName[attrToChange]
        jsonComparer.ordered_dict_prepend(dictName, attrToChange, value) 
    
    def get_Expire_Time(self,secondsToAdd,specificRespJson=None):
        currentDateTime = DT.datetime.utcnow()
        rounded = currentDateTime - DT.timedelta(microseconds=currentDateTime.microsecond)
        currentDateTime = rounded
        if(specificRespJson!=None):
            if("response" in specificRespJson):
                if("responseCode" in specificRespJson["response"]):
                    if(specificRespJson["response"]["responseCode"] !=0):
                        return self.reWrite_UTC_Time(currentDateTime)
                    
        currentDateTime = currentDateTime + DT.timedelta(seconds = secondsToAdd) 
        
        return self.reWrite_UTC_Time(currentDateTime)
            
    def reWrite_UTC_Time(self,currentDateTime):
        currentDateTime = str(currentDateTime)
        currentDateTime = str(currentDateTime).replace(" ", "T")   
        currentDateTime = str(currentDateTime).replace(currentDateTime, currentDateTime+"Z") 
        return currentDateTime
        
    def processSpectrumInquiryResponse(self,jsonResonsedefined,httpRequest):  
        '''
        The code below is to build up SpectrumInquiry response message when multiple spectrum 
        included, not required pre-setup in expected json file
        '''
# if available, use channelType from first instance of inquiredSpectrum, else default
        try:
            siq_channelType = jsonResonsedefined['availableChannel'][0]['channelType']  
        except:
            siq_channelType = consts.DEFAULT_CHANNEL_TYPE
# if available, use ruleApplied from first instance of inquiredSpectrum, else default 
        try:
            siq_ruleApplied = jsonResonsedefined['availableChannel'][0]['ruleApplied']
        except:
            siq_ruleApplied = consts.DEFAULT_RULE_APPLIED
                    
        if(jsonResonsedefined["response"]["responseCode"] ==0):
            if "availableChannel" in jsonResonsedefined:
                availableChannel=[]
                for itemReq in httpRequest["inquiredSpectrum"]:
                    responseChannel = {}
                    responseChannel["ruleApplied"]= siq_ruleApplied
                    responseChannel["channelType"]= siq_channelType
                
                    responseChannel["frequencyRange"] = itemReq
                    if "maxEirp" in jsonResonsedefined["availableChannel"][0]:
                        responseChannel["maxEirp"]=jsonResonsedefined["availableChannel"][0]["maxEirp"]
                    if "groupingParam" in jsonResonsedefined["availableChannel"][0]:
                        responseChannel["groupingParam"] = jsonResonsedefined["availableChannel"][0]["groupingParam"]
                    availableChannel.append(responseChannel)
                self.change_Value_Of_Param_In_Dict(jsonResonsedefined, "availableChannel", availableChannel)
                                  
        else:
            pass
    
    def processGrantResponse(self,jsonResponsedefined,httpRequest):
        
        if(jsonResponsedefined["response"]["responseCode"] ==0):
            if(self.grantId == 0) :
                self.grantId = str(randint(1, 1000000000))                
                self.assertion.grantId = self.grantId  
            self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "grantId", self.grantId) 
            
            if(self.shorterGrantTime != True):
                secondsToAdd = int(consts.SECONDS_TO_ADD_FOR_GRANT_EXPIRE_TIME)               
            else:
                secondsToAdd = consts.SHORTER_GRANT_EXPIRY_TIME
            
            if (not 'channelType' in jsonResponsedefined):
                jsonResponsedefined['channelType'] = consts.DEFAULT_CHANNEL_TYPE
				
            if(not "heartbeatInterval" in jsonResponsedefined):
                jsonResponsedefined["heartbeatInterval"] = consts.HEARTBEAT_INTERVAL				
                
            result = self.get_Expire_Time(secondsToAdd)
            self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "grantExpireTime", result) 
            
            if "operationParam" in jsonResponsedefined:
                if "operationParam" in httpRequest:
                    reqOperParams = httpRequest["operationParam"]
                    self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "operationParam", reqOperParams)
                else:
                    raise IOError('There is no requested parameters in the request message')                  
        else:
            pass
        
    def checkCpiSignedData(self,cpiSigData, cbsdCat):
        """ Given cpiSignatureData from registration request message, verifies the signature on data,
            and checks data with jsonSchema for cpiSignatureData
        """
        self.loggerHandler.print_to_Logs_Files("Registration message contains cpiSignatureData", False)
        decodedHeader = json.loads(base64.standard_b64decode(cpiSigData['protectedHeader']))
        self.loggerHandler.print_to_Logs_Files("protectedHeader = "+str(decodedHeader), False)

        encoded_cpi_data = cpiSigData['protectedHeader'] \
                        + '.' + cpiSigData['encodedCpiSignedData'] \
                        + '.' + cpiSigData['digitalSignature']
        unverified_cpi_payload = jwt.decode(encoded_cpi_data, verify=False)     ### This is data without signature check
        self.loggerHandler.print_to_Logs_Files("encodedCpiSignedData contents = "+json.dumps(unverified_cpi_payload, indent=4), False)
        try:
            cpi_cert_filename = os.path.normpath(os.path.join(str(self.dirPath), str(self.enviormentConfFile.getElementsByTagName('cpiCert')[0].firstChild.data)))
            cpi_cert = open(cpi_cert_filename, 'r').read()
            cpi_cert_obj = load_pem_x509_certificate(cpi_cert, default_backend())
            cpi_public_key = cpi_cert_obj.public_key()
        except:
            self.loggerHandler.print_to_Logs_Files('Error in loading CPI certificate file', True)
            return False
        try:
            verified_cpi_payload = jwt.decode(encoded_cpi_data, cpi_public_key, algorithms=consts.CPI_SIGNATURE_VALID_TYPES)
            self.loggerHandler.print_to_Logs_Files("verified signature on cpiSignatureData", False)
        except (jwt.exceptions.InvalidTokenError, jwt.exceptions.DecodeError, jwt.exceptions.InvalidKeyError, jwt.exceptions.InvalidAlgorithmError) as e:
            self.loggerHandler.print_to_Logs_Files("cpiSignatureData signature error: " +str(e), True)
            return False
        except:
            self.loggerHandler.print_to_Logs_Files("cpiSignatureData signature error: other error", True)
            return False

        schema_filename = os.path.normpath(os.path.join(str(self.dirPath), str(self.enviormentConfFile.getElementsByTagName('jsonsRepoPath')[0].firstChild.data),'OptionalParams', 'cpiSignatureDataSchema.json'))
        try:
            file = open(schema_filename, 'r')
            cpi_schema = json.load(file)
        except:
            self.loggerHandler.print_to_Logs_Files("Error opening cpiSignatureDataSchema", True)
            return False
#        If Cat A, then some installationParams must be removed from required list
        if cbsdCat == 'A':
            self.loggerHandler.print_to_Logs_Files("cbsdCategory= 'A', removing optional param from cpi_schema", False)
            for catAparamOptional in consts.CPI_INSTALLPARAM_CATA_OPTIONAL:
                cpi_schema['definitions']['installationParam']['required'].remove(catAparamOptional)        
        try:
            x = jsonschema.validate(verified_cpi_payload, cpi_schema)
            self.loggerHandler.print_to_Logs_Files("cpiSignatureData data successfully validated against jsonschema ", False)
        except jsonschema.ValidationError as e:
            self.loggerHandler.print_to_Logs_Files('cpiSignature decoded json schema validation error = '+ e.message, True)
            return False
        except:
            self.loggerHandler.print_to_Logs_Files('jsonschema validate fail', False)
            return False
            
        return True