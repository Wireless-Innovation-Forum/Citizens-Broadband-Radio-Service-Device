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
        except:
            raise IOError("ERROR - loading optional parameters not succeeded")
        self.add_Actual_Params_To_Json_If_Not_Exists(jsonExpectedObj[0],httpRequest)
        self.add_meas_report_config_json(httpRequest,suffix)
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
        airInterfaceXml = minidom.parse(str(self.dirPath) +"\\Configuration\\ObjectListConfig\\airInterfaceOptions.xml")
        for child in airInterfaceXml.childNodes[0].childNodes:
            if(child.firstChild!=None):
                if child.tagName == consts.REGISTRATION_SUFFIX_HTTP + "Params":
                    for child2 in child.childNodes:
                        if(child2.firstChild!=None):
                            for child3 in child2.childNodes:
                                if len(child3.childNodes)==1: 
                                    self.dontCheckNode.append(child2.tagName)  
                                    result = JsonComparisonUtils._are_same(child3.firstChild.data, httpRequest[child2.tagName][child3.tagName],False)
                                    if False in result:
                                                                            raise Exception("ERROR - air interface object validation error " +
                                                    "expected value for : " + str(child3.tagName) + " is : "  + str (child3.firstChild.data) +
                                                    " and the actual value is : " + httpRequest[child2.tagName][child3.tagName])                       
        groupingParamXml = minidom.parse(str(self.dirPath) +"\\Configuration\\ObjectListConfig\\groupingParam.xml") 
        if "groupingParam" in httpRequest:
            for child in groupingParamXml.childNodes[0].childNodes:
                if(child.firstChild!=None):
                    if child.tagName == "groupingParam":
                        for child2 in child.childNodes:
                            if len(child2.childNodes)==1:   
                                result = JsonComparisonUtils._are_same(child2.firstChild.data, httpRequest[child.tagName][0][child2.tagName],False)
                                if False in result:
                                    raise Exception("ERROR - grouping param object validation error " +
                                                    "expected value for : " + str(child2.tagName) + " is : "  + str (child2.firstChild.data) +
                                                    " and the actual value is : " + httpRequest[child.tagName][0][child2.tagName]) 
            self.dontCheckNode.append("groupingParam")
        
            
                                           
                                    
#                         self.dontCheckNode.append(key)  
#                         for key2 in optional[key]:                           
#                             result = JsonComparisonUtils._are_same(optional[key][key2], httpRequest[key][key2],False)
        

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
        the method get the optional parameter of the suffix type json and check if it requested from the CBSD if it is it add them to the expected json 
        '''
        ###httpRequest = httpRequest[suffix][0]
        if(consts.REQUEST_NODE_NAME in str(suffix)):
            suffix = str(suffix).replace(consts.REQUEST_NODE_NAME, "")
        try:
            optional = JsonComparisonUtils.get_Node_Of_Json_Parsed(suffix+"Optional"+consts.SUFFIX_OF_JSON_FILE,suffix+"OptionalParams",self.confFile,self.dirPath)[0]
        except :
            raise IOError(suffix + " do not have optional params json")   
        ### check if the key is optional means its not in the expected json but it is in the requests and its allowed in the protocol      
        for key, value in optional.iteritems() :
            d = collections.OrderedDict()         
            if key not in expected[0]:
                if key in httpRequest:
                    if(not self.isThereMoreThenOneValueInside(value)):
                        JsonComparisonUtils.ordered_dict_prepend(expected[0], key, value)   
                    else:## key not exists at all
                        self.dontCheckNode.append(key)  
                        for key2 in optional[key]:   
                            if key2 in httpRequest[key]:
                                if("eutraCarrierRssiRpt" in key2 or "rcvdPowerMeasReports" in key2 ):
                                    self.add_meas_report_config_json(httpRequest, suffix)            
                                if("inquiredSpectrum" in key2):
                                    for var in optional[key][key2]:
                                        for varInHttp in httpRequest[key][key2]:
                                            JsonComparisonUtils.are_same(var, varInHttp,False)
                                else:            
                                    if not isinstance(optional[key][key2], dict):                       
                                        result = JsonComparisonUtils._are_same(str(optional[key][key2]), str(httpRequest[key][key2]),False)
                                    if False in result:
                                        result = JsonComparisonUtils._are_same(optional[key][key2], httpRequest[key][key2],False)
                                        if False in result:
                                            raise Exception("ERROR - there is an validation error between http request and the optional parameter json")                                                                                          
            else:
                if len(value)>1:
                    for key2, value2 in optional[key].iteritems():
                        if key2 not in expected[0][key]:                      
                            if key2 in httpRequest[key]:   
                                JsonComparisonUtils.ordered_dict_prepend(expected[0][key], key2, value2)                          
        return expected
    
    def isThereMoreThenOneValueInside(self,value):
        numberOfValues = 0
#         if("$or" in str(value)):
#             return True
#         else:
#             return False 
        
        if("$or" in str(value)):
            strValue = str(value)
            if "[[" in strValue:
                return True                 
        if(len(str(value).split("$"))>2):
            return True
        else:
            if len(str(value).split(","))>2:
                return True
            
        return False
            
            
        
        
        