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
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import model.Utils.Consts as consts
from xml.dom import minidom
from pathlib import Path
from Loggers.LoggerObserver import loggerObserver
from Loggers.CmdLogger import CmdLogger
from Loggers.DebugLogger import DebugLogger
from Loggers.XmlLogger import XmlLogger
import ssl
from werkzeug.serving import WSGIRequestHandler
from flask import Flask,request,jsonify,redirect,url_for,abort
import logging
from collections import OrderedDict
import json
from model.powerMeasEngine import TxPowerEngine
from threading import Thread, Event
import threading
import time
from controllers.CLIUtils.enums import StepStatus
  
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR) 
    
@app.route("/v1.1/<typeOfCalling>",methods=['POST'])
def sent_Flask_Req_To_Server(typeOfCalling):
    '''
    the method get any post request sent from the CBSD that the url includes '/cbsd/<typeOfCalling>/' 
    send to the engine the request and after verification at the engine side sent the response from the engine 
    to the CBSD side    
    '''
    json_dict = json.loads(request.data,object_pairs_hook=OrderedDict) 
#     powerMeas = TestSession.engine 
    powerMeas = TestSession.engine    
    logger =  powerMeas.loggerHandler
    logger.start_Step(json_dict,typeOfCalling,request.remote_addr)            
    response = powerMeas.process_request(json_dict,typeOfCalling)   
    if(powerMeas.validationErrorAccuredInEngine==True): 
        logger.finish_Step(response,typeOfCalling,StepStatus.FAILED)
    else:        
        logger.finish_Step(response,typeOfCalling,StepStatus.PASSED)
             
    return jsonify(response)
       
@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    '''
    the method get a validation error message and send 400 response to CBSD with the current message  
    or send message that all the steps of the current test had been finished and you need to upload a new csv file 
    '''
    app.app_context()
    func = request.environ.get(consts.NAME_OF_SERVER_WERKZUG)
    func()
    if("ERROR" in str(request.args['validationMessage'])):
        return abort(400, str(request.args['validationMessage']))
    return consts.SERVER_SHUT_DOWN_MESSAGE + consts.TEST_HAD_BEEN_FINISHED_FLASK

def redirectShutDownDueToFinishOfTest():
        return redirect(url_for(consts.SHUTDOWN_FUNCTION_NAME, validationMessage=consts.TEST_HAD_BEEN_FINISHED_FLASK))

def get_Element_From_Config_File(confFile, elementName):
    return confFile.getElementsByTagName(elementName)[0].firstChild.data     

def stopTestSession(spectrumConf,maxEirp,loggerHandler):
    lock = threading.RLock()
    lock.acquire()
    print('To stop the test session please enter "stop", to get approved spectrum information type "get".')  
    commandInput = raw_input()
     
    if commandInput == "get":
        print_final_spectrum_Conf(spectrumConf,maxEirp,loggerHandler) 
                     
    if commandInput == "stop":
        return True
    lock. release()   

def print_final_spectrum_Conf(spectrum,Eirp,loggerHandler):
    for i in range(len(spectrum)):
        carrier = spectrum[i]
#         loggerHandler.print_to_Logs_Files('Select carrier'+str(i) + ' is ' + str(carrier), True)
        loggerHandler.print_to_Logs_Files('Selected spectrum frequency is ' + str(carrier), True)
    loggerHandler.print_to_Logs_Files('Granted Spectrum Max Eirp = ' + str(Eirp) + 'dBm/MHz', True)   
     
def create_Log_Folder():
    
    '''
    the method create logs folder with three folder inside if the folder not created already
    '''
    logsFolderPath = str(dirPath)+"\\Logs"
    if not os.path.exists(logsFolderPath):
            os.makedirs(logsFolderPath)
            os.makedirs(logsFolderPath + "\\SpecificFolderOfTests")
            os.makedirs(logsFolderPath + "\\LogsPerTest")
            os.makedirs(logsFolderPath + "\\CMDSessions")

def initialize_Reports():
    '''
    the method insert the loggers to the logger observer
    '''
    cmdLogger = CmdLogger()
    loggerHandler.register(cmdLogger)
    xmlLogger = XmlLogger()
    loggerHandler.register(xmlLogger)
    
    debugLogger = DebugLogger()
    loggerHandler.register(debugLogger)
    
def input_spectrumInfoLow(loggerHandler):
    correctFreq = False
    while correctFreq == False:
        try:
            frequency = input("please input the start frequency of Cbrs spectrum to be granted (with unit of Mhz): ")
            lowEnd = frequency * 1000000
            if lowEnd >= consts.CBRS_SPECTRUM_LOW and lowEnd <= consts.CBRS_SPECTRUM_HIGH:
                correctFreq = True
            else:
                loggerHandler.print_To_Terminal('Not a valid input, please try again')
        except:
            loggerHandler.print_To_Terminal('Not a valid input, please try again')
            
    loggerHandler.print_To_Terminal('The selected start frequency is ' + str(frequency) + 'MHz.')      
    return lowEnd    

def input_bandwidth_Carrier(lowEndselection,loggerHandler):
    correctBW = False
    while correctBW == False:
        try:
            BWinput = input("please input the bandwidth of Cbrs spectrum to be granted (with unit of Mhz): ")
#             numOfCarriers = input("please input the number of carriers to allow to be granted:")
            numOfCarriers = 1
            specturmConfig =[]
            BWFreqValue = BWinput * 1000000
            highEnd = lowEndselection + BWFreqValue*numOfCarriers
            if highEnd <= consts.CBRS_SPECTRUM_HIGH:
                for i in range(numOfCarriers):
                    spectrumCarrier = {}
                    spectrumCarrier["lowFrequency"] = lowEndselection + i*BWFreqValue
                    spectrumCarrier["highFrequency"] = lowEndselection + (i+1)*BWFreqValue
                    specturmConfig.append(spectrumCarrier)
#                     loggerHandler.print_To_Terminal('Select carrier'+str(i) + ' is ' + str(spectrumCarrier))   
                    loggerHandler.print_To_Terminal('Select spectrum frequency is ' + str(spectrumCarrier))                               
                correctBW = True
            else:
                loggerHandler.print_To_Terminal(consts.BAD_CARRIER_BW_SELECT)
        except:
            loggerHandler.print_To_Terminal('Not a valid input, please try again')                
                
    loggerHandler.print_To_Terminal('The selection of spectrum configuration is done')
    return specturmConfig   

def input_maxEirp(loggerHandler):
    correctEirp = False
    while correctEirp == False:
        try:
            eirpInput = input("please input the MaxEirp of Cbrs spectrum to be granted (with unit of dBm/MHz): ")
            if eirpInput <= consts.MAXERIP_HIGH and eirpInput >= consts.MAXEIRP_LOW:
                correctEirp = True
            else:
                loggerHandler.print_To_Terminal('Not a valid input, please try again')
        except:
            loggerHandler.print_To_Terminal('Not a valid input, please try again')      
    loggerHandler.print_To_Terminal('The selected maxEirp is ' + str(eirpInput) + 'dBm/MHz.')
    return eirpInput 


class testSession(Thread):
    
    def __init__(self,confFile,dirPath,loggerHandler,spectrumConf,maxEirp):
        '''
        Constructor
        '''
        Thread.__init__(self)
        self.confFile           = confFile
        self.dirPath            = dirPath
        self._stop              = threading.Event()
        self.loggerHandler      = loggerHandler
        self.spectrumConf       = spectrumConf
        self.maxEirp            = maxEirp
        self.engine             = TxPowerEngine(confFile,dirPath,loggerHandler,spectrumConf, maxEirp)      
        
    def run(self):
        lock = threading.RLock()
        lock.acquire()        
        while(not stopTestSession(self.spectrumConf, self.maxEirp, self.loggerHandler)):
            time.sleep(0.5)                 
        self.loggerHandler.print_To_Terminal('Type Ctrl-C to exit program.') 
        lock. release()           
           
    def stop_Thread_Due_To_Exception(self):
        self._stop.set()
        
               
if __name__ == '__main__':  
    current_path = os.path.dirname(os.path.realpath(__file__))
    dirPath = Path(__file__).parents[2]
    create_Log_Folder()
    confFile= minidom.parse(str(dirPath) +"\\Configuration\\conf.xml") 
    loggerHandler = loggerObserver(dirPath)
    initialize_Reports()

    approveSpectrumLowEnd = input_spectrumInfoLow(loggerHandler)     
    spectumConfiguration = input_bandwidth_Carrier(approveSpectrumLowEnd, loggerHandler)
    approveMaxEirp = input_maxEirp(loggerHandler)                 
      
    TestSession = testSession(confFile, dirPath, loggerHandler, spectumConfiguration, approveMaxEirp)
    TestSession.start()
      
    cliInput = threading.Thread(target=stopTestSession, args=(spectumConfiguration,approveMaxEirp,loggerHandler))  
    cliInput.start()
    
    loggerHandler.start_Test(consts.CLI_SESSION)
    loggerHandler.start_Test('PowerMeasTest')
    print_final_spectrum_Conf(spectumConfiguration,approveMaxEirp,loggerHandler)    
 
    loggerHandler.print_To_Terminal(consts.START_POWER_MEAS_TEST)         
    loggerHandler.print_to_Logs_Files(consts.SELECTED_TEST_FROM_USER_MESSAGE + str('PowerMeasTest') + " is starting now", True)
 
    WSGIRequestHandler.protocol_version = "HTTP/1.1"  
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2) # use TLS to avoid POODLE
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.set_ciphers(consts.WINNF_APPROVED_CIPHERS)
    ctx.load_verify_locations(str(dirPath) + get_Element_From_Config_File(confFile,"caCerts"))
    ctx.load_cert_chain(str(dirPath) + get_Element_From_Config_File(confFile,"pemFilePath"), str(dirPath) + get_Element_From_Config_File(confFile,"keyFilePath")) 
    host_ip = get_Element_From_Config_File(confFile,"hostIp")
    sever_port = get_Element_From_Config_File(confFile,"port")
                 
    app.run(host_ip,sever_port,threaded=True,request_handler=WSGIRequestHandler,ssl_context=ctx)       
 
    TestSession.join()
    cliInput.join() 