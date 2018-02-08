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
from flask import Flask,request,jsonify,g,redirect,url_for,abort
from controllers.ENodeBController import ENodeBController
import Utils.Consts as consts
from collections import OrderedDict
import json
from controllers.CLIUtils.enums import StepStatus
from __builtin__ import True
import flask
import datetime as DT

PRINT_MSG_BETWEEN_TESTS = False           # print msg to screen for req/resp between test cases
NICE_MSG_HANDLING_BETWEEN_TESTS = True     # False = old handling (respCode=103), True = nicer handling

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)



enodeBController = ENodeBController(None)
@app.route("/"+consts.WINNF_PROTOCOL_VERSION+"/<typeOfCalling>",methods=['POST'])
def sent_Flask_Req_To_Server(typeOfCalling):
    '''
    the method get any post request sent from the CBSD that the url includes '/cbsd/<typeOfCalling>/' 
    send to the engine the request and after verification at the engine side sent the response from the engine 
    to the CBSD side    
    '''
    logger = enodeBController.engine.loggerHandler
    json_dict = json.loads(request.data,object_pairs_hook=OrderedDict)
    while (not enodeBController.engine.check_Last_Step_In_All_CBRS()):
        logger.start_Step(json_dict,typeOfCalling,request.remote_addr)
        response = enodeBController.linker_Between_Flask_To_Engine(json_dict,typeOfCalling)
        if("ERROR" in str(response)): ### if engine get an error while validate the request the flask will sent a shutdown call for the flask server
            return redirect(url_for(consts.SHUTDOWN_FUNCTION_NAME, validationMessage=str(response)))
        logger.finish_Step(response,typeOfCalling,StepStatus.PASSED)           
        return jsonify(response)
    
    finalResp = []
    timeNow = (DT.datetime.utcnow().replace(microsecond=0)).isoformat()+'Z'
    if NICE_MSG_HANDLING_BETWEEN_TESTS == True:
        responseName = str(typeOfCalling)+"Response"
        for req in json_dict[typeOfCalling+consts.REQUEST_NODE_NAME]:
            x = enodeBController.engine.generate_canned_response(req, typeOfCalling)
            finalResp.append(x[responseName][0])
    
        if PRINT_MSG_BETWEEN_TESTS == True:
            print timeNow+" - RECEIVED = " +str(json_dict)
            print timeNow+" - SENT =  "+str({responseName: finalResp})
        return jsonify( {responseName: finalResp})
        
    else:       # old method of canned responses.  To be deprecated...
        if(typeOfCalling!=consts.REGISTRATION_SUFFIX_HTTP):
            finalResp = []
            nonRegistereddata = {  "response": {
                                    "responseCode":103,
                                    "responseData": ["cbsdId"]
                                    }
                                }
         
            finalResp = []
            if len(json_dict[typeOfCalling+consts.REQUEST_NODE_NAME])>1:
                for req in json_dict[typeOfCalling+consts.REQUEST_NODE_NAME]:
                    finalResp.append(nonRegistereddata)
                if PRINT_MSG_BETWEEN_TESTS == True:
                    print timeNow+" - RECEIVED = " +str(json_dict) 
                    print timeNow+" - SENT =  "+str({str(typeOfCalling)+"Response": finalResp})
                return jsonify( {str(typeOfCalling)+"Response": finalResp})
            else:
                finalResp = {str(typeOfCalling)+"Response": [{
                                    "response":{"responseCode":103,
                                                "responseData": ["cbsdId"]
                                                }
                                }]
                             }
                if PRINT_MSG_BETWEEN_TESTS == True:
                    print timeNow+" - RECEIVED = " +str(json_dict) 
                    print timeNow+" - SENT =  "+str(finalResp)
                return jsonify(finalResp)
                 
        else:
            registeredData = {
                                                        "response":{"responseCode":103}
                                                    }
            allRegisteredData =[]
         
            if len(json_dict[typeOfCalling+consts.REQUEST_NODE_NAME])>1:
                for req in json_dict[typeOfCalling+consts.REQUEST_NODE_NAME]:
                    allRegisteredData.append(registeredData)
                finalResp = {str(typeOfCalling)+"Response": allRegisteredData}
                if PRINT_MSG_BETWEEN_TESTS == True:
                    print timeNow+" - RECEIVED = " +str(json_dict)
                    print timeNow+" - SENT =  "+str(finalResp)
                return jsonify( finalResp)
            else:
                finalResp = {str(typeOfCalling)+"Response": [{
                                                    "response":{"responseCode":103}
                                                }]
                            }
                if PRINT_MSG_BETWEEN_TESTS == True:
                    print timeNow+" - RECEIVED = " +str(json_dict) 
                    print timeNow+" - SENT =  "+str(finalResp)
                return jsonify(finalResp)

       
@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    '''
    the method get a validation error message and send 400 response to CBSD with the current message  
    or send message that all the steps of the current test had been finished and you need to upload a new csv file 
    '''
    logger = enodeBController.engine.loggerHandler
    app.app_context()
#    func = request.environ.get(consts.NAME_OF_SERVER_WERKZUG)
#    func()
    if("ERROR" in str(request.args['validationMessage'])):
        logger.finish_Step("the server shot down because :  " + str(request.args['validationMessage']),False,StepStatus.FAILED)
        logger.print_to_Logs_Files(str(request.args['validationMessage']), True)
        return abort(400, str(request.args['validationMessage']))
    return consts.SERVER_SHUT_DOWN_MESSAGE + consts.TEST_HAD_BEEN_FINISHED_FLASK

def redirectShutDownDueToFinishOfTest():
        return redirect(url_for(consts.SHUTDOWN_FUNCTION_NAME, validationMessage=consts.TEST_HAD_BEEN_FINISHED_FLASK))
import ssl
from multiprocessing import Process
from werkzeug.serving import WSGIRequestHandler
WSGIRequestHandler.protocol_version = "HTTP/1.1"
def runFlaskServer(host,port,ctx):
    app.run(host,port,threaded=True,request_handler=WSGIRequestHandler,ssl_context=ctx)



