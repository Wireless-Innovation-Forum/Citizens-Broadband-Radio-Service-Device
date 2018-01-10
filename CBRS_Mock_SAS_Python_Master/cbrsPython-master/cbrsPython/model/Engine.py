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

import model.Utils.Consts as consts
from model.CBRSRequestHandler import CBRSRequestHandler as cbrsObj
import datetime as DT


class MyEngine(object):

    def __init__(self,testDefinition,confFile,dirPath,loggerHandler):
        self.testDefinition                    = testDefinition
        self.validationErrorAccuredInEngine     = False
        self.confFile                           = confFile
        self.dirPath                            = dirPath
        self.loggerHandler                      = loggerHandler
        self.cbrsObjArray                       = []
        self.allTheCBRSRegistered               = False

    def process_request(self,httpRequest,typeOfCalling):
        '''
        the method get the httpRequest and for each request sent it to the correct cbsd request handler
        '''
        request_arrival_time = DT.datetime.utcnow()
        if(self.validationErrorAccuredInEngine==True):
            return "ERROR - error accoured in the last request from the CBRS"
        nodeResponse = typeOfCalling+consts.RESPONSE_NODE_NAME.title()
        i = 0
        try:
            httpRequest[typeOfCalling+consts.REQUEST_NODE_NAME]
        except:
            self.validationErrorAccuredInEngine = True
            return "ERROR - in the request no " + typeOfCalling+consts.REQUEST_NODE_NAME + " node exists in message"
        for httpReq in httpRequest[typeOfCalling+consts.REQUEST_NODE_NAME]:
            
            if(typeOfCalling=="registration"):
                try:
                    self.add_Cbrs_Obj(httpReq["cbsdSerialNumber"])
                except Exception as E:
                    self.validationErrorAccuredInEngine = True
                    return E.message
                try:
                    if(i==0):
                        response = self.handle_Http_Req(httpReq["cbsdSerialNumber"],httpReq,typeOfCalling, request_arrival_time)
                        self.raise_In_Case_Of_An_Error(response)
                    elif (i>0):
                        tempResp = self.handle_Http_Req(httpReq["cbsdSerialNumber"],httpReq,typeOfCalling, request_arrival_time)
                        self.raise_In_Case_Of_An_Error(tempResp)
                        response[nodeResponse].append(tempResp[nodeResponse][0])
                except Exception as E:
                    self.validationErrorAccuredInEngine = True
                    return "for the CBRS with the cbsdSerialNumber :" + str(httpReq["cbsdSerialNumber"]) + " " +  E.message
                    
                    
            else:
                try:
                    cbsdSerialNumberIndex = str(httpReq["cbsdId"]).index("Mock-SAS")
                except : 
                    self.validationErrorAccuredInEngine = True
                    return consts.JSON_REQUEST_NOT_INCLUDE_KEY + " cbsdId , or that the cbsdid in the http request is not include mock-sas" 
                try:
                    if(i==0):
                        response = self.handle_Http_Req(httpReq["cbsdId"][cbsdSerialNumberIndex+len("Mock-SAS"):],httpReq, typeOfCalling, request_arrival_time)
                        self.raise_In_Case_Of_An_Error(response)
                    elif (i>0):
                        tempResp = self.handle_Http_Req(httpReq["cbsdId"][cbsdSerialNumberIndex+len("Mock-SAS"):],httpReq,typeOfCalling, request_arrival_time)
                        self.raise_In_Case_Of_An_Error(response)
                        response[nodeResponse].append(tempResp[nodeResponse][0])               
                except Exception as E:
                    self.validationErrorAccuredInEngine = True
                    return E.message
            i+=1
        if(len(self.cbrsObjArray) == len(self.testDefinition.jsonNamesOfSteps)):
            self.allTheCBRSRegistered = True
        return response
                    
    
    def add_Cbrs_Obj(self,cbsdSerialNumber):
        tempCbrsObj = cbrsObj(cbsdSerialNumber, self.testDefinition, self.confFile, self.dirPath,self.loggerHandler)
        if tempCbrsObj not in self.cbrsObjArray:
            self.cbrsObjArray.append(tempCbrsObj)
        del tempCbrsObj
    
    def handle_Http_Req(self,cbsdSerialNumber,httpReq,typeOfCalling, msg_timestamp):
        for cbrsObj in self.cbrsObjArray: 
            if cbrsObj.cbsdSerialNumber == cbsdSerialNumber:
                if(self.check_Last_Step_In_All_CBRS()==False and cbrsObj.isLastStepInCSV==True):
                    # if one CBSD completes test before other, give it a canned response instead of unknown message...
                    canned_resp = self.generate_canned_response(httpReq,typeOfCalling)
                    return canned_resp
                return cbrsObj.handle_Http_Req(httpReq,typeOfCalling, msg_timestamp)
        self.validationErrorAccuredInEngine = True
        raise IOError("ERROR - there is no cbrs obj registered with the cbsdSerialNumber :  " + str(cbsdSerialNumber) )
    
    def check_Validation_Error(self):
        if self.validationErrorAccuredInEngine == True:
            return True
        for cbrsObj in self.cbrsObjArray: 
            if cbrsObj.validationErrorAccuredInEngine ==True:
                return True
        return False
        
    def raise_In_Case_Of_An_Error(self,response):
        if "ERROR" in response:
            raise IOError(response)
        
    def check_Last_Step_In_All_CBRS(self):
        '''
        the method check the last step of all the column of json from the csv , each column should fit to diffrent cbsd
        '''
        if(self.allTheCBRSRegistered == True):
            for cbrsObj in self.cbrsObjArray:
                if(cbrsObj.isLastStepInCSV == False):
                    return False
            if(len(self.cbrsObjArray)==0):
                return False
            return True
        return False
    
    def get_Question_Answer_Part(self):
        '''
        the method collect the question answer part from all the cbrs object 
        '''
        i=0
        for cbrsObj in self.cbrsObjArray:
            if(i==0):
                tempQuestAnswerPart = cbrsObj.get_Question_Answer_Part()
            if len(self.cbrsObjArray) == 1:
                return tempQuestAnswerPart
            elif(i>0):
                tempResp = cbrsObj.get_Question_Answer_Part()
                for questAnswer in tempResp:
                    tempQuestAnswerPart.append(questAnswer)
            i+=1       
        return tempQuestAnswerPart
    
    def generate_canned_response(self, req, callType):
        ''' Generates a canned response for CBSD to keep it sane while another CBSD still has steps to complete.
            Does not allow new REG or GRA, but provides SUCCESS response to SIQ, HBT, RLQ and DRG.
            No parameter checking done -- this CBSD has finished the test so we just want to give it a valid
            response instead of an error message...
        '''    
        if callType == 'registration':
            rsp = { 'registrationResponse':[ {
                        'response': {
                            'responseCode': 200
                            }
                        } ]
                   }
        elif callType == 'spectrumInquiry':
            rsp = { 'spectrumInquiryResponse': [ {
                            'cbsdId': req['cbsdId'],
                            'availableChannel': {
                                'frequencyRange': {
                                    'lowFrequency':  3550000000,
                                    'highFrequency': 3555000000
                                    },
                                'channelType': 'GAA',
                                'ruleApplied': 'FCC_PART_96'
                                },
                            'response': {
                                'responseCode': 0
                                }
                            } ]
                       }
        elif callType == 'grant':
            rsp = { 'grantResponse': [ {
                            'cbsdId': req['cbsdId'],
                            'response': {
                                'responseCode': 400
                                }
                            } ]
                       }    
        elif callType == 'heartbeat':
            if 'grantId' in req:
                rsp = { 'heartbeatResponse': [ {
                            'cbsdId': req['cbsdId'],
                            'grantId': req['grantId'],
                            'transmitExpireTime': (DT.datetime.utcnow().replace(microsecond=0) + DT.timedelta(seconds=consts.SECONDS_TO_ADD_FOR_TX_EXPIRE_TIME)).isoformat()+'Z',
                            'response': {
                                'responseCode': 0
                                }
                            } ]
                       }
            else:
                rsp = { 'heartbeatResponse': [ {
                            'cbsdId': req['cbsdId'],
                            'response': {
                                'responseCode': 102,
                                'responseData': ['grantId']
                                }
                            } ]
                       }
        elif callType == 'relinquishment':
            if 'grantId' in req:
                rsp = { 'relinquishmentResponse': [ {
                            'cbsdId': req['cbsdId'],
                            'grantId': req['grantId'],
                            'response': {
                                'responseCode': 0
                                }
                            } ]
                       }
            else:
                rsp = { 'relinquishmentResponse': [ {
                            'cbsdId': req['cbsdId'],
                            'response': {
                                'responseCode': 102,
                                'responseData': ['grantId']
                                }
                            } ]
                       }
        elif callType == 'deregistration':
            rsp = { 'deregistrationResponse': [ {
                            'cbsdId': req['cbsdId'],
                            'response': {
                                'responseCode': 0
                                }
                            } ]
                       }
        else:   # unknown callType -- should never get here...
            rsp ={ 'unknownMessageResponse': ['response not defined']}
            
        return rsp  