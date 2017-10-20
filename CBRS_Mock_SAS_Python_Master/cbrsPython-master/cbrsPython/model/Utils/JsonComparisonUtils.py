'''
Created on Apr 23, 2017

@author: iagmon
'''


import json
from __builtin__ import True


class Stack:
    def __init__(self):
        self.stack_items = []

    def append(self, stack_item):
        self.stack_items.append(stack_item)
        return self

    def __repr__(self):
        stack_dump = ''
        for item in self.stack_items:
            stack_dump += str(item)
        return stack_dump

    def __str__(self):
        stack_dump = ''
        for item in self.stack_items:
            stack_dump += str(item)
        return stack_dump


class StackItem:
    def __init__(self, reason, expected, actual):
        self.reason = reason
        self.expected = expected
        self.actual = actual

    def __repr__(self):
        return 'Reason: {0}\nExpected:\n{1}\nActual:\n{2}' \
               .format(self.reason, _format_value(self.expected), _format_value(self.actual))

    def __str__(self):
        return '\n\nReason: {0}\nExpected:\n{1}\nActual:\n{2}' \
               .format(self.reason, _format_value(self.expected), _format_value(self.actual))


def _indent(s):
    return '\n'.join('  ' + line for line in s.splitlines())


def _format_value(value):
    return _indent(_generate_pprint_json(value))


def _generate_pprint_json(value):
    return json.dumps(value, sort_keys=True, indent=4)


def _is_dict_same(expected, actual, ignore_value_of_keys):
    # DAN - I had to flip flop this
    for key in expected:
        if not key in actual:
            return False, \
                   Stack().append(
                        StackItem('Expected key "{0}" Missing from Actual'
                                      .format(key),
                                  expected,
                                  actual))

        if not key in ignore_value_of_keys:
            # have to change order
            #are_same_flag, stack = _are_same(actual[key], expected[key], ignore_value_of_keys)
            
            ### key part noam ###
            are_same_flag, stack = _are_same(expected[key], actual[key],ignore_value_of_keys)
            if not are_same_flag:
                return False, \
                       stack.append(StackItem('Different values', expected[key], actual[key]))
    return True, Stack()

def _is_list_same(expected, actual, ignore_value_of_keys):
    for i in xrange(len(expected)):
        are_same_flag, stack = _are_same(expected[i], actual[i], ignore_value_of_keys)
        if not are_same_flag:
            return False, \
                   stack.append(
                       StackItem('Different values (Check order)', expected[i], actual[i]))
    return True, Stack()

def _bottom_up_sort(unsorted_json):
    if isinstance(unsorted_json, list):
        new_list = []
        for i in xrange(len(unsorted_json)):
            new_list.append(_bottom_up_sort(unsorted_json[i]))
        return sorted(new_list)

    elif isinstance(unsorted_json, dict):
        new_dict = {}
        for key in sorted(unsorted_json):
            new_dict[key] = _bottom_up_sort(unsorted_json[key])
        return new_dict

    else:
        return unsorted_json

def _are_same(expected, actual, ignore_value_of_keys, ignore_json_length=False):
    # Check for None
    if expected is None:
        return expected == actual, Stack()

    # Ensure they are of same type
    if type(expected) != type(actual):
        inRange = False
        if "$" in str(expected):             
            inRange = validate_Json_Value_Special_Sign(expected,actual)
            expected = inRange
            if(inRange==False):
                return False, \
                   Stack().append(
                       StackItem('Type Mismatch: Expected Type: {0}, Actual Type: {1}'
                                    .format(type(expected), type(actual)),
                                 expected,
                                 actual))
            return inRange,Stack() 
        

    # Compare primitive types immediately
    if type(expected) in (int, str, bool, long, float, unicode):
        if "$" in str(expected):
            try:
                inRange = validate_Json_Value_Special_Sign(expected,actual)
            except Exception as e:
                return False,\
                Stack().append(
                   StackItem(e.message,
                             expected,
                             actual)) 
            if(inRange == False):
                return False, \
               Stack().append(
                   StackItem('Not in range: the value : {0} , is not in the range expected : {1}'
                                .format(actual, str(expected)[str(expected).find(":")+1: len(str(expected))-1]),
                             expected,
                             actual))           
            return inRange,Stack()
        
        return str(expected).replace('"', "") == str(actual).replace('"', ""), Stack()

    # Ensure collections have the same length (if applicable)
    if ignore_json_length:
        # Ensure collections has minimum length (if applicable) 
        # This is a short-circuit condition because (b contains a)
        if len(expected) > len(actual):
            return False, \
                   Stack().append(
                        StackItem('Length Mismatch: Minimum Expected Length: {0}, Actual Length: {1}'
                                      .format(len(expected), len(actual)),
                                  expected,
                                  actual))

    else:
        # Ensure collections has same length
        if len(expected) != len(actual):
            return False, \
                   Stack().append(
                       StackItem('Length Mismatch: Expected Length: {0}, Actual Length: {1}'
                                      .format(len(expected), len(actual)),
                                  expected,
                                  actual))

    

    if isinstance(expected, dict):
        return _is_dict_same(expected, actual, ignore_value_of_keys)

    if isinstance(expected, list):
        return _is_list_same(expected, actual, ignore_value_of_keys)

    return False, Stack().append(StackItem('Unhandled Type: {0}'.format(type(expected)), expected, actual))


def are_same(original_a, original_b, ignore_list_order_recursively=False, ignore_value_of_keys=[]):  
    if ignore_list_order_recursively:
        a = _bottom_up_sort(original_a)
        b = _bottom_up_sort(original_b)
    else:
        a = original_a
        b = original_b   
    return _are_same(a, b, ignore_value_of_keys,len(ignore_value_of_keys)>0)


def contains(expected_original, actual_original, ignore_list_order_recursively=False, ignore_value_of_keys=[]):
    if ignore_list_order_recursively:
        actual = _bottom_up_sort(actual_original)
        expected = _bottom_up_sort(expected_original)
    else:
        actual = actual_original
        expected = expected_original
    return _are_same(expected, actual, ignore_value_of_keys, True)

def json_are_same(a, b, ignore_list_order_recursively=False, ignore_value_of_keys=[]):
    return are_same(json.loads(a), json.loads(b), ignore_list_order_recursively, ignore_value_of_keys)


def validate_Json_Value_Special_Sign(expected,actual):
    strExpected = str(expected)
    strAcutal = str(actual)
    
    if("range" in str(expected)):
        indexOfPunctuation = strExpected.find(":")
        indexOfSeperationSign = strExpected.find("To")
        lowestVal = strExpected[indexOfPunctuation+1:indexOfSeperationSign]
        heighestVal =  strExpected[indexOfSeperationSign+2:len(strExpected)-1].replace("}","")
        if float(lowestVal) <= float(strAcutal) and (float(heighestVal) >= float(strAcutal)):
            return True
        raise Exception ("ERROR - the actual value : " + strAcutal + " not in the range expected : " + lowestVal + " To : " + heighestVal  )
    if("or" in strExpected):
        try:
            for value in expected.iteritems() :
                strActualOnlyLetters =strAcutal.replace("[", "").replace("u'", "").replace("'","").replace("]","")
                for value in value[1]:
                    strExpectedOnlyLetters = str(value).lower().replace("[", "").replace("u'", "").replace("'","").replace("]","")
                    if len((strExpectedOnlyLetters).split(","))>1 :
                        valuesOfExpected = strExpectedOnlyLetters.split(",")
                        valuesOfActual = strActualOnlyLetters.split(",")
                        for cell in valuesOfActual:
                            if cell in valuesOfExpected:
                                return value         
                    if strExpectedOnlyLetters.upper() == strActualOnlyLetters.upper():
#                     if strExpectedOnlyLetters.upper() == strAcutal.upper():
                        return value
        except :
            indexOfPuncuation = strExpected.find(":")
            strExpected = strExpected[indexOfPuncuation+1:]
            if "[[" in strExpected :
                optionsArray = strExpected[1:-1].split("],[")
                i=0
                for key in optionsArray :
                    key = key.replace("[","").replace("]","")
                    optionsArray[i] = key
                    i+=1
            else:          
                optionsArray = strExpected.replace("'", "").replace("[","").replace("]","").split(",")
            for value in optionsArray :
                strExpectedOnlyLetters = str(value).replace("[", "").replace("u'", "").replace("'","").replace('"',"").replace("]","")
                strActualOnlyLetters =strAcutal.replace("[", "").replace("u'", "").replace("'","").replace("]","")
                if len((value).split(","))>1 :
                    valuesOfExpected = value.replace('"',"").split(",")
                    valuesOfActual = strActualOnlyLetters.split(",")
                    for cell in valuesOfActual:
                        if str(cell).strip() not in valuesOfExpected:
                            return False 
                    return value         
                if strExpectedOnlyLetters == strAcutal:
                    return value
        raise Exception ("ERROR - the actual value : " + strAcutal + " is not one of the valid options in the json file " )
                
    if("maximumLength" in strExpected):
        indexOfPunctuation = strExpected.find(":")
        lenExpected = strExpected[indexOfPunctuation+1:len(strExpected)-1]
        if(len(strAcutal)<=int(lenExpected)):
            return strAcutal
        raise Exception ("the actual value : " + strAcutal + " is more then the limit length  : " +  lenExpected )
            

from collections import OrderedDict

def Get_Json_After_Parse_To_Dic(jsonFileName, confFile, dirPath):
    '''
    the method get the jsonFileName the config file and the path leading to that file
    perform a loading of the json in an order way to an dictionary    
    '''
    filePath = str(dirPath) + confFile.getElementsByTagName("jsonsRepoPath")[0].firstChild.data
    if("Optional" in str(jsonFileName)):
        filePath = filePath + "OptionalParams\\"
    myfile = open(filePath + str(jsonFileName))
    jsonAfterParse = json.load(myfile, object_pairs_hook=OrderedDict)
    return jsonAfterParse

def get_Node_Of_Json_Parsed(jsonFileName,nodeOfJsonRequest,confFile,dirPath):
    jsonAfterParse = Get_Json_After_Parse_To_Dic(jsonFileName, confFile, dirPath)
    if(Is_Json_contains_key(jsonFileName, nodeOfJsonRequest, confFile, dirPath,jsonAfterParse)):
        return jsonAfterParse[nodeOfJsonRequest]
    else:
        raise IOError("ERROR - the node : " + str(nodeOfJsonRequest) +" not exists in the expected json file :" + str(jsonFileName))
        
def Is_Json_contains_key(jsonFileName,nodeOfJsonRequest,confFile,dirPath,jsonAfterParse=None):
    if(jsonAfterParse==None):
        jsonAfterParse = Get_Json_After_Parse_To_Dic(jsonFileName, confFile, dirPath)
    if(nodeOfJsonRequest in jsonAfterParse):
        return True
    return False


def ordered_dict_prepend(dct, key, value, dict_setitem=dict.__setitem__):
        root = dct._OrderedDict__root
        first = root[1]
    
        if key in dct:
            link = dct._OrderedDict__map[key]
            link_prev, link_next, _ = link
            link_prev[1] = link_next
            link_next[0] = link_prev
            link[0] = root
            link[1] = first
            root[1] = first[0] = link
        else:
            root[1] = first[0] = dct._OrderedDict__map[key] = [root, first, key]
            return dict_setitem(dct, key, value)
        


    
