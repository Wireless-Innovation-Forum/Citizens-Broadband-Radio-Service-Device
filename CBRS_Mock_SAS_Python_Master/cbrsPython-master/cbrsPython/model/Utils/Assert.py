'''
Created on Apr 20, 2017

@author: iagmon
'''
from model.Utils import JsonComparisonUtils
from model.Utils import Consts as consts
import collections
import xml.etree.ElementTree as ET
from click.decorators import option
from collections import OrderedDict
from xml.dom import minidom
from operator import itemgetter
import json
import jsonschema
import os

class Assertion(object):
    '''
    classdocs
    '''

    def __init__(self,enviormentConfFile,dirPath,loggerHandler,cbrsConfFile,cbsdId = None, grantId = None):
        '''
        Constructor
        '''
        self.dontCheckNode = []
        self.confFile = enviormentConfFile
        self.dirPath  = dirPath
        self.loggerHandler = loggerHandler
        self.cbrsConfFile = cbrsConfFile
        self.cbsdId = cbsdId
        self.grantId = grantId
        
    def compare_Json_Req(self,httpRequest,jsonExpected,suffix,keysFromJson=None,printIfFalse =True):
        
        ''' 
        the method will get the request json file name from the client request and will get from the two repo
        off the client and the server the json expected and the real json sent from the client 
        '''
        self.dontCheckNode = []
        
        try:
            jsonExpectedObj = JsonComparisonUtils.get_Node_Of_Json_Parsed(jsonExpected,suffix,self.confFile,self.dirPath)
        except Exception as e:
            raise IOError(e.message)  
        if(consts.REGISTRATION_SUFFIX_HTTP + consts.REQUEST_NODE_NAME == suffix):
            self.add_reg_params_to_json(jsonExpectedObj,httpRequest)
        else:
            JsonComparisonUtils.ordered_dict_prepend(jsonExpectedObj[0],"cbsdId" ,str(self.cbsdId))
            if((consts.HEART_BEAT_SUFFIX_HTTP + consts.REQUEST_NODE_NAME == suffix) or (consts.RELINQUISHMENT_SUFFIX_HTTP + consts.REQUEST_NODE_NAME == suffix) ) :
                JsonComparisonUtils.ordered_dict_prepend(jsonExpectedObj[0],"grantId" ,str(self.grantId))
        try:    
            jsonExpectedObj = self.add_Json_Optional_Parameters(jsonExpectedObj,httpRequest,suffix)
        except Exception as E: 
            raise IOError("ERROR - loading optional parameters not succeeded" + str(E)) 
        
        self.add_Actual_Params_To_Json_If_Not_Exists(jsonExpectedObj[0],httpRequest)
                
        if(bool(self.get_Attribute_Value_From_Json(jsonExpected,"measReportRequested"))==True):                                                                                                                                                                    
            self.measurement_Report_Decision(httpRequest,jsonExpectedObj, suffix)                                                               
            
        if(bool(self.get_Attribute_Value_From_Json(jsonExpected,"fullBandReport"))==True):
                self.check_Fullband_Measurement_Report (httpRequest)                                                                                                  
         
        x = JsonComparisonUtils.are_same(jsonExpectedObj[0],httpRequest,False,self.dontCheckNode)    
        if(False in x and printIfFalse == True):
            self.loggerHandler.print_to_Logs_Files(x,True)
        try:
            assert True in x
        except:
            raise IOError(consts.ERROR_VALIDATION_MESSAGE + "in the json : " + jsonExpected)
        return x
    
    def add_meas_report_config_json(self,httpRequest,suffix):
        if("measReport" in httpRequest):
            try:
                optional = JsonComparisonUtils.get_Node_Of_Json_Parsed("measReportOptional"+consts.SUFFIX_OF_JSON_FILE,"measReport",self.confFile,self.dirPath)[0]
            except :
                raise IOError("ERROR - do not have meas report eutra json") 
            for varInHttp in httpRequest["measReport"]["rcvdPowerMeasReports"]:
                result = JsonComparisonUtils.are_same(optional["rcvdPowerMeasReports"][0], varInHttp,False)
                if False in result:
                    raise IOError("ERROR - the meas report from the http is not allowed ")
            self.dontCheckNode.append("measReport")
                   
    '''
    The code below is used for check measurement report in the request messages
    '''  
    def measurement_Report_Decision(self, RequestMessage, ExpectedJsonObj, suffix):                                                                 
        
        if(consts.HEART_BEAT_SUFFIX_HTTP + consts.REQUEST_NODE_NAME == suffix):                                                                     
            if(not self.is_Json_Request_Contains_Key(RequestMessage, "measReport")):                                                                                                             
                del ExpectedJsonObj[0]["measReport"]                                                                                                
            else:                                                                                                                                   
                numberOfMeasure = len(RequestMessage["measReport"]["rcvdPowerMeasReports"])                                                         
                ExpectedJsonObj[0]["measReport"]["rcvdPowerMeasReports"] = numberOfMeasure*ExpectedJsonObj[0]["measReport"]["rcvdPowerMeasReports"]         
        else:
            if(not self.is_Json_Request_Contains_Key(RequestMessage, "measReport")):                                                                
                raise Exception("ERROR - there is no measurement report sent in request message")                                                                   
            numberOfMeasure = len(RequestMessage["measReport"]["rcvdPowerMeasReports"])                                                             
            ExpectedJsonObj[0]["measReport"]["rcvdPowerMeasReports"] = numberOfMeasure*ExpectedJsonObj[0]["measReport"]["rcvdPowerMeasReports"]     
            
        return ExpectedJsonObj                                                                                                                      

    def check_Fullband_Measurement_Report(self,RequestMessage):                                                                                     

        numberOfMeasure = len(RequestMessage["measReport"]["rcvdPowerMeasReports"])                                                                 
        ReportFreqBandwidth = []                                                                                                                   
        for i in range(numberOfMeasure):                                                                                                            
            frequencyStart = RequestMessage["measReport"]["rcvdPowerMeasReports"][i]["measFrequency"]                                               
            measBandWidth = RequestMessage["measReport"]["rcvdPowerMeasReports"][i]["measBandwidth"]                                                
            ReportFreqBandwidth.append((frequencyStart,measBandWidth) )                                                                             

        ReportFreqBandwidth.sort(key=lambda x: int(x[0]), reverse=False)                                                                            
            
        reportedBandwidth = 0                                                                                                                       
        for i in range(0,numberOfMeasure-1):
                
            if ReportFreqBandwidth[i][0]+ ReportFreqBandwidth[i][1] != ReportFreqBandwidth[i+1][0]:                                                 
                raise Exception("ERROR - there is gap between two reported frequencies or reported bandwidth does not cover full bandwidth")                                         
            reportedBandwidth += ReportFreqBandwidth[i][1]                                                                                          
            
        if(reportedBandwidth + ReportFreqBandwidth[-1][1] != 150000000):                                                                           
            raise Exception("ERROR - The measurement doesn't cover full bandwidth")                                                                 
        return                                                                                                                                      
        
        '''
        End of code changes                                                                                                                           
        '''                    
                         
    def is_Json_Request_Contains_Key(self,jsonRequest,keyToVerify,node=None):
        try:
            if node !=None:
                jsonRequest = jsonRequest[node]
            for post in jsonRequest:
                if post == keyToVerify:
                    return True
        except Exception as E:
            return E.message
        return False

                
    
    def add_Actual_Params_To_Json_If_Not_Exists(self,expectedObj,httpRequest):
        for key in httpRequest:
            if (key not in expectedObj):
                if(key not in self.dontCheckNode):
                    JsonComparisonUtils.ordered_dict_prepend(expectedObj, key, None)

    def add_reg_params_to_json(self,jsonExpected,httpRequest):
        for child in self.cbrsConfFile.childNodes[0].childNodes:
            #print child.tag, child.attrib
            if(child.firstChild!=None):
                if child.tagName == consts.REGISTRATION_SUFFIX_HTTP + "Params":
                    for child2 in child.childNodes:
                        if(child2.firstChild!=None):
                            if len(child2.childNodes)==1:                         
                                JsonComparisonUtils.ordered_dict_prepend(jsonExpected[0],child2.tagName , child2.firstChild.data)
                            else:
                                for childInChild in child2.childNodes:
                                    if(childInChild.firstChild!=None):
                                        self.dontCheckNode.append(child2.tagName)                         
                                        result = JsonComparisonUtils._are_same(childInChild.firstChild.data, httpRequest[child2.tagName][childInChild.tagName],False)
                                        if False in result:
                                            raise Exception("ERROR - there is an validation error between http request and the configuration file attribute ")
        
    def is_Json_File_Contains_Key(self, jsonExpected,keyToVerify):
        return JsonComparisonUtils.Is_Json_contains_key(jsonExpected, keyToVerify, self.confFile, self.dirPath)
    
    def get_Attribute_Value_From_Json(self,jsonExpected,keyToVerify):
        '''
        the method get key check if it exists in the expected json and return the value as a string      
        '''
        if(self.is_Json_File_Contains_Key(jsonExpected, keyToVerify)):
            return JsonComparisonUtils.get_Node_Of_Json_Parsed(jsonExpected,keyToVerify,self.confFile,self.dirPath)
        return False
    
    def get_Duration_Time_From_Grant_Json(self,jsonExpected):
        try:
            responsePart = JsonComparisonUtils.get_Node_Of_Json_Parsed(jsonExpected,consts.RESPONSE_NODE_NAME,self.confFile,self.dirPath)
        except Exception as e:
            if e.message == "node not exists":
                return consts.SUFFIX_NOT_EXISTS_IN_EXPECTED_JSON_FILE
        return responsePart[consts.GRANT_SUFFIX_HTTP+consts.RESPONSE_NODE_NAME.title()][0]['heartbeatInterval']
    
    def add_Json_Optional_Parameters(self,expected,httpRequest,suffix):
        '''
        the method get the optional parameter of the suffix type json and check if it requested from the CBSD if it is it add them to the expected json. json schema is used for the data validation.
        '''
        current_path = str(self.dirPath)
        configurable_file_path = os.path.join(current_path,'','Configuration','ObjectListConfig')     
        later_Defined_params_file = open(os.path.join(str(configurable_file_path), "laterDefindedOptional.json"))
        
        if(consts.REQUEST_NODE_NAME in str(suffix)):
            suffix = str(suffix).replace(consts.REQUEST_NODE_NAME, "")
        try:
            optional = JsonComparisonUtils.get_Node_Of_Json_Parsed(suffix+"Optional"+consts.SUFFIX_OF_JSON_FILE,suffix+"OptionalParams",self.confFile,self.dirPath)[0]
            optional_laterDefined = json.load(later_Defined_params_file, object_pairs_hook=OrderedDict)
            
        except :
            raise IOError(suffix + " do not have optional params json")   
        '''        
        check if the key is optional means its not in the expected json but it is in the requests and its allowed in the protocol 
        '''
        for key, value in httpRequest.iteritems(): 
            if key not in expected[0]:
                if key in optional_laterDefined["properties"]:
                    try:
                        jsonschema.validate(OrderedDict([(key, value)]), optional_laterDefined)
                        self.dontCheckNode.append(key)                        
                    except jsonschema.ValidationError as e:
                        raise Exception(str(e))                  
                
                elif key in optional["properties"]:
                    try:
                        jsonschema.validate(OrderedDict([(key, value)]), optional)
                        self.dontCheckNode.append(key)                        
                    except jsonschema.ValidationError as e:
                        raise Exception(str(e))
                        
                else:                       
                    raise Exception("- some parameters in http request are not defined by Specifications or bad names")
            else:
                # where value is a dictionary of nested (key, value) pairs, such as installationParam in Registration Request
                if (isinstance(value, dict)): 
                    if len(value)>1:
                        for key2, value2 in httpRequest[key].iteritems():
                            if key2 not in expected[0][key]:                      
                                if key2 in httpRequest[key]:   
                                    JsonComparisonUtils.ordered_dict_prepend(expected[0][key], key2, value2)            
        return expected                