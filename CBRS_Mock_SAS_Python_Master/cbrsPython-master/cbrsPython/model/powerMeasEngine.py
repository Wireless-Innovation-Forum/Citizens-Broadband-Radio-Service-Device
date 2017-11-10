'''
Created on Apr 20, 2017

@author: iagmon
'''

import model.Utils.Consts as consts
from model.powerMeasRequestHandler import RequestHandler as cbrsObj

class TxPowerEngine(object):

    def __init__(self,confFile,dirPath,loggerHandler, spectrumConf, maxEirp):
        self.validationErrorAccuredInEngine     = False
        self.confFile                           = confFile
        self.dirPath                            = dirPath
        self.loggerHandler                      = loggerHandler
        self.cbrsObjArray                       = []
        self.allTheCBRSRegistered               = False
        self.registeredCbrs                     = []
        self.spectrumConf                       = spectrumConf
        self.maxEirp                            = maxEirp
        self.cbrsConfFile                       = None                
     
    def process_request(self,httpRequest,typeOfCalling):
        self.validationErrorAccuredInEngine     = False                           
        '''
        the method get the httpRequest and for each request sent it to the correct cbsd request handler
        '''                
        nodeResponse = typeOfCalling+consts.RESPONSE_NODE_NAME.title()        
        i = 0
        try:
            httpRequest[typeOfCalling+consts.REQUEST_NODE_NAME]
        except:
            self.validationErrorAccuredInEngine = True
            return "ERROR - in the request no " + typeOfCalling+consts.REQUEST_NODE_NAME + " node exists"
        
        for httpReq in httpRequest[typeOfCalling+consts.REQUEST_NODE_NAME]:       
            
            if(typeOfCalling=="registration"):
                if httpReq["cbsdSerialNumber"] not in self.registeredCbrs:
                    try:
                        self.add_Cbrs_Obj(httpReq["cbsdSerialNumber"])
                    except Exception as E:
                        self.validationErrorAccuredInEngine = True
                        return E.message
                try:
                    if(i==0):
                        response = self.handle_Http_Req(httpReq["cbsdSerialNumber"],httpReq,typeOfCalling,self.spectrumConf, self.maxEirp)
                        self.update_cbrsObjArray(response, typeOfCalling, httpReq)
                        self.raise_In_Case_Of_An_Error(response) 
                                               
                    elif (i>0):
                        tempResp = self.handle_Http_Req(httpReq["cbsdSerialNumber"],httpReq,typeOfCalling,self.spectrumConf, self.maxEirp)
                        self.update_cbrsObjArray(tempResp, typeOfCalling, httpReq)                                   
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
                        response = self.handle_Http_Req(httpReq["cbsdId"][cbsdSerialNumberIndex+len("Mock-SAS"):],httpReq, typeOfCalling,self.spectrumConf,self.maxEirp)
                        self.raise_In_Case_Of_An_Error(response)
                    elif (i>0):
                        tempResp = self.handle_Http_Req(httpReq["cbsdId"][cbsdSerialNumberIndex+len("Mock-SAS"):],httpReq,typeOfCalling,self.spectrumConf, self.maxEirp)
                        self.raise_In_Case_Of_An_Error(response)
                        response[nodeResponse].append(tempResp[nodeResponse][0])               
                except Exception as E:
                    self.validationErrorAccuredInEngine = True
                    return E.message
            i+=1
            
        return response     

    def update_cbrsObjArray(self, responseMessage,typeOfCalling,httpRequest):
        if(responseMessage[typeOfCalling+consts.RESPONSE_NODE_NAME.title()][0]["response"]["responseCode"] !=0):
            for item in self.cbrsObjArray:
                if item.cbsdSerialNumber == httpRequest["cbsdSerialNumber"]:
                    self.cbrsObjArray.remove(item)
        else:
            self.registeredCbrs.append(httpRequest["cbsdSerialNumber"])        
    
    def add_Cbrs_Obj(self,cbsdSerialNumber):
        tempCbrsObj = cbrsObj(cbsdSerialNumber, self.confFile, self.dirPath,self.loggerHandler,self.spectrumConf, self.maxEirp)
        if tempCbrsObj not in self.cbrsObjArray:
            self.cbrsObjArray.append(tempCbrsObj)
        del tempCbrsObj
    
    def handle_Http_Req(self,cbsdSerialNumber,httpReq,typeOfCalling,specConf, Eirp):      
        for cbrsObj in self.cbrsObjArray: 
            if cbrsObj.cbsdSerialNumber == cbsdSerialNumber:                             
                ResponseJson = cbrsObj.handle_Http_Req(httpReq,typeOfCalling)
                if cbrsObj.validationRequestDataError == True:
                    self.validationErrorAccuredInEngine = True
                return ResponseJson                                                       
        self.validationErrorAccuredInEngine = True
        raise IOError("ERROR - there is no cbrs obj registered with the cbsdSerialNumber :  " + str(cbsdSerialNumber) )
    
    def check_Validation_Error(self):
        if self.validationErrorAccuredInEngine == True:
            return True
        
        for cbrsObj in self.cbrsObjArray: 
            if cbrsObj.validationErrorAccuredInEngine ==True:
                return True
        return False

    def check_Test_Stop(self):
        for cbrsObj in self.cbrsObjArray: 
            if cbrsObj.deregistrationDone ==True:
                return True
        return False
        
    def raise_In_Case_Of_An_Error(self,response):
        if "ERROR" in response:
            raise IOError(response)