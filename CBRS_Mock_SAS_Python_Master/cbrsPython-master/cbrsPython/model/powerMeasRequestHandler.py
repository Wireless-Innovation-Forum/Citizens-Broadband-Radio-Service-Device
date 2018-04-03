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
import model.Utils.JsonComparisonUtils as jsonComparer 
import model.Utils.Consts as consts
import datetime as DT
from random import *
import os
from model.Utils import JsonComparisonUtils
import json
import jsonschema
from collections import OrderedDict
import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend


class RequestHandler(object):
    '''
    Process the https request and validate parameters in the incoming request message
    '''

    def __init__(self,cbsdSerialNumber,EnviormentConfFile,dirPath,currentLogger,specConf, Eirp):

        self.validDurationTime                  = 0
        self.validationErrorAccuredInEngine     = False
        self.loggerHandler                      = currentLogger
        self.assertion                          = None
        self.grantIdlist                          = []
        self.enviormentConfFile                 = EnviormentConfFile
        self.dirPath                            = dirPath
        self.cbsdId                             = None
        self.grantId                            = 0
        self.expectedRelBeforeDeragistration    = False                                     
        self.secondsForDelay                    = 0                                                                                             
        self.heartbeatErrorList                 = [500, 501, 502, 105] 
        self.immediatelyShutdown                = False 
        self.shorterGrantTime                   = False   
        self.cbsdSerialNumber                   = cbsdSerialNumber    
        self.validationRequestDataError         = False
        self.deregistrationDone                 = False  
        self.spectrumConfig                     = None
        self.cbrsSpectrumHighEnd                = 0
        self.cbrsSpectrumLowEnd                 = 0
        self.spectrumConf                       = specConf
        self.currentGrantEIRP                   = Eirp                                          
            
    def handle_Http_Req(self, httpRequest,typeOfCalling):     
        
        self.cbrsSpectrumHighEnd = consts.CBRS_SPECTRUM_HIGH
        self.cbrsSpectrumLowEnd = consts.CBRS_SPECTRUM_LOW
        self.validationRequestDataError = False 
                                                                   
        try:
            self.Check_Request_Parameters(httpRequest,typeOfCalling)  
                  
        except Exception as e:
            self.validationRequestDataError = True 
            self.loggerHandler.print_to_Logs_Files(str(e), True) 
    
        reponseNode = str(typeOfCalling)
        responseFile = "powerMeas_"+reponseNode+consts.SUFFIX_OF_JSON_FILE
       
        return self.process_response(typeOfCalling,httpRequest,responseFile)               

    def get_Element_From_Config_File(self, confFile, elementName):
        return confFile.getElementsByTagName(elementName)[0].firstChild.data 

    def Check_Request_Parameters(self,httpRequest,typeOfCalling):
        '''
        the method get the requested parameters checked to see if they are valid, jsonschema is used for the data validation.
        '''      
        suffix = typeOfCalling+consts.REQUEST_NODE_NAME
        current_path = str(self.dirPath)
        configurable_file_path = os.path.join(current_path,'','Configuration','ObjectListConfig')     
        later_Defined_params_file = open(os.path.join(str(configurable_file_path), "laterDefindedOptional.json"))
        
        if(consts.REQUEST_NODE_NAME in str(suffix)):
            suffix = str(suffix).replace(consts.REQUEST_NODE_NAME, "")
        try:
            
            optional = JsonComparisonUtils.get_Node_Of_Json_Parsed(suffix+"Optional"+consts.SUFFIX_OF_JSON_FILE,suffix+"OptionalParams",self.enviormentConfFile,self.dirPath)[0]
            optional_laterDefined = json.load(later_Defined_params_file, object_pairs_hook=OrderedDict)
            
        except :
            raise IOError(suffix + " do not have optional params json")   
        '''        
        check if the key is optional means its not in the expected json but it is in the requests and its allowed in the protocol 
        '''
        for key, value in httpRequest.iteritems(): 
            if key in optional_laterDefined["properties"]:
                try:
                    jsonschema.validate(OrderedDict([(key, value)]), optional_laterDefined)                    
                except jsonschema.ValidationError as e:
                    raise Exception(str(e)) 
                    self.validationRequestDataError = True
                                    
            elif key in optional["properties"]:
                try:
                    jsonschema.validate(OrderedDict([(key, value)]), optional)                       
                except jsonschema.ValidationError as e:
                    raise Exception(str(e))
                    self.validationRequestDataError = True            
                                             
            else:                       
                raise Exception("- some parameters in http request are not defined by Specifications or bad names")  
                self.validationRequestDataError = True                     
        
    
    def parse_Json_To_Dic_By_File_Name(self,jsonFileName,nodeName,confFile):
        try:
            return jsonComparer.get_Node_Of_Json_Parsed(jsonFileName,nodeName,confFile,self.dirPath)
        except Exception as e:
            if e.message == "node not exists":
                return consts.SUFFIX_NOT_EXISTS_IN_EXPECTED_JSON_FILE
  
    def process_response(self,typeOfCalling,httpRequest, responseFile): 
        jsonAfterParse = self.parse_Json_To_Dic_By_File_Name(responseFile,consts.RESPONSE_NODE_NAME,self.enviormentConfFile)
        if len(jsonAfterParse) > 1:
            for item in jsonAfterParse.iteritems():
                if item[0] != typeOfCalling+consts.RESPONSE_NODE_NAME.title():
                    del jsonAfterParse[item[0]]            
        specificRespJson = jsonAfterParse[typeOfCalling+consts.RESPONSE_NODE_NAME.title()][0]      
        
        if(typeOfCalling == consts.REGISTRATION_SUFFIX_HTTP):
            
            if(self.validationRequestDataError == True):
                self.change_Value_Of_Param_In_Dict(specificRespJson, "response", {"responseCode": 103})
            else: 
                if(self.cbsdId==None):
                    self.cbsdId = httpRequest["fccId"]+ "Mock-SAS" + self.cbsdSerialNumber
                self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId) 
        
        elif(typeOfCalling == consts.SPECTRUM_INQUIERY_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson,"cbsdId",self.cbsdId)            
            self.processSpectrumInquiryResponse(specificRespJson,httpRequest)
            
        elif(typeOfCalling == consts.GRANT_SUFFIX_HTTP):
            if(self.validationRequestDataError == True):
                self.change_Value_Of_Param_In_Dict(specificRespJson, "response", {"responseCode": 103})
                self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId)
            else:
                self.change_Value_Of_Param_In_Dict(specificRespJson,"cbsdId",self.cbsdId)
                self.processGrantResponse(specificRespJson,httpRequest)            
                        
        elif(typeOfCalling == consts.HEART_BEAT_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId)
            
            if(httpRequest["grantId"] in self.grantIdlist): 
                self.change_Value_Of_Param_In_Dict(specificRespJson, "grantId", httpRequest["grantId"])
                secondsToAdd = int(consts.SECONDS_TO_ADD_FOR_TX_EXPIRE_TIME)
                result = self.get_Expire_Time(secondsToAdd,specificRespJson)
                self.change_Value_Of_Param_In_Dict(specificRespJson, "transmitExpireTime", result) 
                                         
            else:
                self.validationRequestDataError = True
                self.loggerHandler.print_to_Logs_Files('The requested grantId is not valid', True)                
                self.change_Value_Of_Param_In_Dict(specificRespJson, "response", {"responseCode": 103})   
                
            if("grantRenew" in httpRequest):                                                           
                if(httpRequest["grantRenew"] == True or httpRequest["grantRenew"]=="true"):
                    secondsToAdd = consts.SHORTER_GRANT_EXPIRY_TIME
                    result = self.get_Expire_Time(secondsToAdd)
                    self.change_Value_Of_Param_In_Dict(specificRespJson, "grantExpireTime", result)                                 
                    
        elif (typeOfCalling == consts.RELINQUISHMENT_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId)
            if(httpRequest["grantId"] in self.grantIdlist):  
                self.change_Value_Of_Param_In_Dict(specificRespJson, "grantId", self.grantId)
                self.grantIdlist.remove(httpRequest["grantId"])  
                
            else:
                self.validationRequestDataError = True
                self.loggerHandler.print_to_Logs_Files('The requested grantId is not valid', True)                
                self.change_Value_Of_Param_In_Dict(specificRespJson, "response", {"responseCode": 103})                               
        
        elif(typeOfCalling == consts.DEREGISTRATION_SUFFIX_HTTP):
            self.change_Value_Of_Param_In_Dict(specificRespJson, "cbsdId", self.cbsdId)
            if(specificRespJson["response"]["responseCode"] ==0):
                self.deregistrationDone = True  
        
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
        
    def processSpectrumInquiryResponse(self,jsonResponsedefined,httpRequest):  
        '''
        The code below is to build up SpectrumInquiry response message when multiple spectrum 
        included, not required pre-setup in expected json file
        '''                     
        if('cbsdId' not in httpRequest or "inquiredSpectrum" not in httpRequest):
            self.validationRequestDataError = True            
            responseResult = {"responseCode" : 102}
            self.loggerHandler.print_to_Logs_Files('The required parameters are missing in SpectrumInquiry request message', True)
            self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "response", responseResult)
            
        elif(httpRequest['cbsdId'] != self.cbsdId):
            self.validationRequestDataError = True            
            responseResult = {"responseCode" : 103}
            self.loggerHandler.print_to_Logs_Files('The required parameters are invalid in SpectrumInquiry request message', True)
            self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "response", responseResult)
            
        else:
            availableChannel=[] 
            for itemReq in httpRequest["inquiredSpectrum"]:
                responseChannel = {} 
                if('lowFrequency' not in itemReq or 'highFrequency' not in itemReq):
                    self.validationRequestDataError = True                   
                    responseResult = {"responseCode" : 103}
                    self.loggerHandler.print_to_Logs_Files('The required parameters are invalid in SpectrumInquiry request message', True)
                    self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "response", responseResult)
                    
                elif(itemReq["highFrequency"] <= itemReq["lowFrequency"]):
                    self.validationRequestDataError = True                    
                    responseResult = {"responseCode" : 103}
                    self.loggerHandler.print_to_Logs_Files('The Highfrequency is lower than Lowfrequency in the request message.', True)                    
                    self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "response", responseResult)
                                     
                elif(itemReq["lowFrequency"]<self.cbrsSpectrumLowEnd or itemReq["highFrequency"]>self.cbrsSpectrumHighEnd):
                    self.validationRequestDataError = True                    
                    responseResult = {"responseCode" : 300}
                    self.loggerHandler.print_to_Logs_Files('The frequency inquired is out of CBRS band.', True)                    
                    self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "response", responseResult)
                
                else:
                    for i in range(len(self.spectrumConf)):
                        if itemReq["lowFrequency"] >= self.spectrumConf[i]["lowFrequency"] and \
                                itemReq["highFrequency"] <= self.spectrumConf[i]["highFrequency"]:
                            responseChannel["frequencyRange"] = itemReq                                 
                            responseChannel["ruleApplied"]="FCC_PART_96"                    
                            responseChannel["maxEirp"]=self.currentGrantEIRP
                            if(itemReq["lowFrequency"]>=consts.SPECTRUM_GAA_LOW and itemReq["highFrequency"] <= consts.SPECTRUM_GAA_HIGH):
                                responseChannel["channelType"]="GAA"
                            elif(itemReq["lowFrequency"]>consts.SPECTRUM_PAL_LOW and itemReq["highFrequency"] < consts.SPECTRUM_PAL_HIGH):
                                responseChannel["channelType"]="PAL"                   
                            availableChannel.append(responseChannel)
                            self.loggerHandler.print_to_Logs_Files('The requested spectrum is in the range, SpectrumInquiry response code is 0', True)                             
                            
                    if(len(availableChannel) == 0):
                        for i in range(len(self.spectrumConf)): 
                            responseChannel["frequencyRange"] = {}
                            responseChannel["frequencyRange"]["highFrequency"]=self.spectrumConf[i]["highFrequency"]
                            responseChannel["frequencyRange"]["lowFrequency"]=self.spectrumConf[i]["lowFrequency"]
                            responseChannel["ruleApplied"]="FCC_PART_96"
                            responseChannel["maxEirp"]=self.currentGrantEIRP
                            if(responseChannel["frequencyRange"]["lowFrequency"]>=consts.SPECTRUM_GAA_LOW and \
                                    responseChannel["frequencyRange"]["highFrequency"]<=consts.SPECTRUM_GAA_HIGH):
                                responseChannel["channelType"]="GAA"  
                            if(responseChannel["frequencyRange"]["lowFrequency"]>=consts.SPECTRUM_PAL_LOW and \
                                    responseChannel["frequencyRange"]["highFrequency"]<=consts.SPECTRUM_PAL_HIGH):
                                responseChannel["channelType"]="PAL"                         
                            availableChannel.append(responseChannel)  
                            self.loggerHandler.print_to_Logs_Files('The requested spectrum is out of the range, availableChannel is sent out', True)                
                                
                    responseResult = {"responseCode" : 0}
                    self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "availableChannel", availableChannel)                                                      

    
    def processGrantResponse(self,jsonResponsedefined,httpRequest):  
        
        grantResp = jsonResponsedefined          
        if 'cbsdId' not in httpRequest or 'operationParam' not in httpRequest \
                    or 'operationFrequencyRange' not in httpRequest['operationParam']:
            self.validationRequestDataError = True
            responseResult = {"responseCode" : 102}
            self.loggerHandler.print_to_Logs_Files('The required parameters are missing in grant request message', True)
            self.change_Value_Of_Param_In_Dict(grantResp, "response", responseResult)
            self.change_Value_Of_Param_In_Dict(grantResp, "cbsdId", self.cbsdId)
                
        elif(httpRequest['cbsdId'] != self.cbsdId):
            self.validationRequestDataError = True            
            responseResult = {"responseCode" : 103}
            self.loggerHandler.print_to_Logs_Files('The required parameters are invalid in Grant request message', True)
            self.change_Value_Of_Param_In_Dict(grantResp, "response", responseResult)
            self.change_Value_Of_Param_In_Dict(grantResp, "cbsdId", self.cbsdId)
                    
        elif(httpRequest['operationParam']['operationFrequencyRange']['highFrequency'] < httpRequest['operationParam']['operationFrequencyRange']['lowFrequency']):
            responseResult = {"responseCode" : 103}
            self.validationRequestDataError = True            
            self.loggerHandler.print_to_Logs_Files('The required parameters are invalid in Grant request message', True)
            self.change_Value_Of_Param_In_Dict(grantResp, "response", responseResult)
            self.change_Value_Of_Param_In_Dict(grantResp, "cbsdId", self.cbsdId)
                
        else: 
            FreqInRange = False
            for i in range(len(self.spectrumConf)):
                if httpRequest['operationParam']['operationFrequencyRange']['lowFrequency'] == self.spectrumConf[i]["lowFrequency"] and \
                        httpRequest['operationParam']['operationFrequencyRange']['highFrequency'] == self.spectrumConf[i]["highFrequency"]:
                    FreqInRange = True
                    if(httpRequest['operationParam']['maxEirp']> self.currentGrantEIRP):
#                        self.validationRequestDataError = True                        
                        responseResult = {"responseCode" : 400}
                        self.loggerHandler.print_to_Logs_Files('The requested maxEirp value is too high', True)
                        self.change_Value_Of_Param_In_Dict(grantResp, "response", responseResult)  
                    
                    else:
                        successGrantId = False
                        while(successGrantId == False):     
                            self.grantId = str(randint(1, 1000000000))
#                             self.grantId = str(12345)
                            if(self.grantId not in self.grantIdlist):
                                successGrantId = True                         
                        self.grantIdlist.append(self.grantId)                    
                        self.change_Value_Of_Param_In_Dict(grantResp, "grantId", self.grantId)  
                        self.change_Value_Of_Param_In_Dict(grantResp, "heartbeatInterval", consts.HEARTBEAT_INTERVAL)                        
                                       
                        secondsToAdd = int(consts.SECONDS_TO_ADD_FOR_GRANT_EXPIRE_TIME)                                          
                        result = self.get_Expire_Time(secondsToAdd)
                        self.change_Value_Of_Param_In_Dict(grantResp, "grantExpireTime", result)
                                
                        if(httpRequest['operationParam']['operationFrequencyRange']['lowFrequency']>=consts.SPECTRUM_GAA_LOW and \
                                httpRequest['operationParam']['operationFrequencyRange']['highFrequency'] <= consts.SPECTRUM_GAA_HIGH):
                            channelType ="GAA"
                         
                        elif(httpRequest['operationParam']['operationFrequencyRange']['lowFrequency']>=consts.SPECTRUM_PAL_LOW and \
                                httpRequest['operationParam']['operationFrequencyRange']['highFrequency'] <= consts.SPECTRUM_PAL_HIGH):
                            channelType ="PAL"                   
                        self.change_Value_Of_Param_In_Dict(grantResp, "channelType", channelType)
                        
            if(FreqInRange == False):
#                self.validationRequestDataError = True                    
                responseResult = {"responseCode" : 400}
                self.loggerHandler.print_to_Logs_Files('The requested frequency is not in the available spectrum range', True)
                self.change_Value_Of_Param_In_Dict(grantResp, "response", responseResult)    
                                 
        if(grantResp["response"]["responseCode"] !=0):
#            newAvailableChannel = []
            for i in range(len(self.spectrumConf)):
                ## NOTE: this only works for len(self.spectrumConf = 1), protocol does not allow array of operationParam
                newResponseChannel ={}
                newResponseChannel["operationFrequencyRange"] = {}
                newResponseChannel["operationFrequencyRange"]["highFrequency"]=self.spectrumConf[i]["highFrequency"]
                newResponseChannel["operationFrequencyRange"]["lowFrequency"]=self.spectrumConf[i]["lowFrequency"]
                newResponseChannel["maxEirp"]=self.currentGrantEIRP
                         
#                newAvailableChannel.append(newResponseChannel)
            self.change_Value_Of_Param_In_Dict(jsonResponsedefined, "operationParam", newResponseChannel)
            self.loggerHandler.print_to_Logs_Files('The Grant response code is not 0, applicable spectrum parameters have been sent out.', True)                                                  
  
            