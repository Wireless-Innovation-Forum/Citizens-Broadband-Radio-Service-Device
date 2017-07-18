'''
Created on Apr 20, 2017

@author: iagmon
'''
from model.Utils import JsonComparisonUtils
from model.Utils import Consts as consts
class Assertion(object):
    '''
    classdocs
    '''


    def __init__(self,enviormentConfFile,dirPath,loggerHandler,cbrsConfFile):
        '''
        Constructor
        '''
        self.confFile = enviormentConfFile
        self.dirPath  = dirPath
        self.loggerHandler = loggerHandler
        self.cbrsConfFile = cbrsConfFile
        
    def compare_Json_Req(self,httpRequest,jsonExpected,suffix):
        
        ''' 
        the method will get the request json file name from the client request and will get from the two repo
        off the client and the server the json expected and the real json sent from the client 
        '''
        try:
            jsonExpectedObj = JsonComparisonUtils.get_Node_Of_Json_Parsed(jsonExpected,suffix,self.confFile,self.dirPath)
            jsonExpectedObj = self.add_Json_Optional_Parameters(jsonExpectedObj,httpRequest,suffix)
        except Exception as e:
            raise IOError(e.message)  
        if(consts.REGISTRATION_SUFFIX_HTTP in suffix):
            # example for insert to request defaults params from specific config file
            JsonComparisonUtils.ordered_dict_prepend(jsonExpectedObj[0],"fccId" , self.cbrsConfFile.getElementsByTagName("fccId")[0].firstChild.data)
            JsonComparisonUtils.ordered_dict_prepend(jsonExpectedObj[0],"userId" , self.cbrsConfFile.getElementsByTagName("userId")[0].firstChild.data)
        '''if(consts.HEART_BEAT_SUFFIX_HTTP in suffix):
            ignoreKeys = []
            ignoreKeys.append("operationState")
            x = JsonComparisonUtils.are_same(jsonExpectedObj[0],httpRequest,False,ignoreKeys)'''
        '''else:'''
        x = JsonComparisonUtils.are_same(jsonExpectedObj[0],httpRequest)
        if(False in x):
            self.loggerHandler.print_to_Logs_Files(x,True)
        try:
            assert True in x
        except:
            raise IOError(consts.ERROR_VALIDATION_MESSAGE + "in the json : " + jsonExpected)
        return x
        

    def is_Json_Contains_Key(self, jsonExpected,keyToVerify):
        return JsonComparisonUtils.Is_Json_contains_key(jsonExpected, keyToVerify, self.confFile, self.dirPath)
    
    def get_Attribute_Value_From_Json(self,jsonExpected,keyToVerify):
        '''
        the method get key check if it exists in the expected json and return the value as a string      
        '''
        if(self.is_Json_Contains_Key(jsonExpected, keyToVerify)):
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
            if key not in expected[0]:
                if key in httpRequest:
                    JsonComparisonUtils.ordered_dict_prepend(expected[0], key, value)                    
        return expected
        
        
        