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

### Program Constants
WINNF_PROTOCOL_VERSION =                    "v1.1"
SHORTER_GRANT_EXPIRY_TIME =                 360
DEFAULT_RULE_APPLIED =                      "FCC_PART_96"
DEFAULT_CHANNEL_TYPE =                      "GAA"
SECONDS_TO_ADD_FOR_GRANT_EXPIRE_TIME =      604800          # seconds ahead for grantExpireTime - 1 week
SECONDS_TO_ADD_FOR_TX_EXPIRE_TIME =         200             # seconds ahead for transmitExpireTime
SECONDS_FOR_DELAY_RESPONSE =                SECONDS_TO_ADD_FOR_TX_EXPIRE_TIME   # Worst-case value
CPI_SIGNATURE_VALID_TYPES =                 ['RS256', 'ES256']
CPI_INSTALLPARAM_CATA_OPTIONAL =            ['antennaAzimuth', 'antennaDowntilt', 'antennaBeamwidth']   # params REG-Cond for Cat B, optional for Cat A

HEARTBEAT_INTERVAL =                        60
HEARTBEAT_INTERVAL_GRACE_PERIOD =           5.0    # seconds

CBRS_SPECTRUM_HIGH =                        3700000000
CBRS_SPECTRUM_LOW =                         3550000000
MAXEIRP_LOW =                               -137
MAXERIP_HIGH =                              37

SPECTRUM_PAL_HIGH =                         3650000000
SPECTRUM_PAL_LOW =                          3550000000
SPECTRUM_GAA_HIGH =                         3700000000
SPECTRUM_GAA_LOW =                          3550000000

WINNF_APPROVED_CIPHER_LIST = [
    'AES128-GCM-SHA256',                # TLS_RSA_WITH_AES_128_GCM_SHA256
    'AES256-GCM-SHA384',                # TLS_RSA_WITH_AES_256_GCM_SHA384
    'ECDHE-ECDSA-AES128-GCM-SHA256',    # TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
    'ECDHE-ECDSA-AES256-GCM-SHA384',    # TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    'ECDHE-RSA-AES128-GCM-SHA256',      # TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
    '@STRENGTH'
    ]

WINNF_APPROVED_CIPHERS = ':'.join(WINNF_APPROVED_CIPHER_LIST) # string of ciphers separated by colons

MAX_NUM_HBT_FOR_MEASREPORT =    5   # number of HBT responses for measReport to appear, before failing test

### Other Constants
ERROR_VALIDATION_MESSAGE =                  "ERROR - An Error occurred while comparing between actual and expected request"
RESULTS_OF_TEST_MESSAGE =                   "The final result of the test : "
SET_CSV_FILE_MESSAGE =                      "Please enter a csv file path that include the test you request to run (pay attention insert the csv file without the csv suffix) \n, type quit and press ctrl+c to close"
START_TEST_MESSAGE =                        "Start of the test"
CLOSE_USER_SESSION =                        "Session user will now close"
SENT_FLASK_REQUEST =                        "sent flask request to engine"
SHUTDOWN_FUNCTION_NAME =                    'shutdown'
TEST_HAD_BEEN_FINISHED_FLASK =              " all the steps of the test had been finished see final results at the console "
NAME_OF_SERVER_WERKZUG =                    "werkzeug.server.shutdown"
SERVER_SHUT_DOWN_MESSAGE =                  "Server shutting down due to"
E_NODE_B_SENT_TO_ENGINE_REQUEST =           "cbsd sent request to engine from server"
INIT_TEST_DEFINITION =                      "init the test definition by the test steps sent from the user"
SUFFIX_OF_JSON_FILE =                       ".json"
COMPARING_JSONS_MESSAGE =                   "compare between requested json to expected json"
REQUEST_NODE_NAME =                         "Request"
RESPONSE_NODE_NAME =                        "response"
QUESTION_NODE_NAME =                        "questions"
HEART_BEAT_SUFFIX_HTTP =                    "heartbeat"
SPECTRUM_INQUIERY_SUFFIX_HTTP =             "spectrumInquiry"
HEART_BEAT_ARRIVED_MESSAGE =                "heartBeat request arrived to engine"
GRANT_SUFFIX_HTTP =                         "grant"
RELINQUISHMENT_SUFFIX_HTTP =                "relinquishment"
NSTEP_SESSION_WITH_TECHNITIAN =             "arrived to nstep starting question answer session with the technician"
HEARTBEAT_FROM_ENGINE_TO_CBSD_MESSAGE =      "return heart beat part of json from engine to the cbsd"
ADDITIONAL_COMMENTS_MESSAGE =               "the additional comments for the current test are : "
ANSWERS_NODE =                              "answers"
QUESTION_NODE =                             "question"
SUFFIX_NOT_EXISTS_IN_EXPECTED_JSON_FILE =   "ERROR - the suffix of the type of calling from http request is not exists in the expected json file from the csv"
HEART_BEAT_REACHED_TO_LIMIT_MESSAGE =       "ERROR - heartbeat had reached to the limit of heartbeat set from the config file"
HEART_BEAT_TIMEOUT_MESSAGE  =               "ERROR - the duration between the heartbeats are more then expected from json file"
EXPECT_ANSWER_NODE =                        "expectedAnswer"
CHOOSE_ONE_OF_THE_ANSWERS_MESSAGE =         " please choose one of the answers :"
LAST_STEP_TYPE =                            "nstep"
HEART_BEAT_REPEATS_SUFFIX =                 "Repeats"
ADD_TEST_TO_SPECIFIC_FOLDER_MESSAGE =       "would you like to add the test to specific folder ? (select yes or no)"
CLI_SESSION                        =        "CLISession"
GRANT_BEFORE_HEARTBEAT_ERROR       =        "ERROR - heartbeat request can be only after grant request"
SELECT_TO_ADD_TEST_MESSAGE         =        "you have choose to add the test "
SELECT_TO_ADD_FOLDER_MESSAGE    =           " to the specific folder :"
SELECTED_TEST_FROM_USER_MESSAGE =           "the selected test from the user : "
PASS_MESSAGE =                              "PASS"
FAIL_MESSAGE =                              "FAIL"
JSON_REQUEST_NOT_INCLUDE_KEY =              "ERROR - the http request does not include key : "
JSON_THIS_CBRS_STEPS_HAD_BEEN_FINISHED =    {
                                                "message" : "the specific cbrs had finished all steps successfully but the domain proxy still have cbrs that not finished all steps",
                                                "response": {
                                                    "responseCode": 0
                                                }
                                            }
REGISTRATION_SUFFIX_HTTP =                  "registration"
DEREGISTRATION_SUFFIX_HTTP =                "deregistration"
EMPTY_CSV_FILE_NAME_MESSAGE =               "cannot enter empty line for csv file try again"
ENTER_YES_OR_NO_MESSAGE =                   "valid input to the question is yes or no"
TYPE_NAME_OF_FOLDER      =                  "enter log of test to the specific folder"
VALIDATION_PASSED_MESSAGE =                 "validation passed successfully, the engine sent "
GOODBYE_MESSAGE =                           "The last test had been finished and no other csv file had been entered,  goodbye"
QUIT_PROGRAM_MESSAGE =                      "you decided to quit the program have a good day"
START_POWER_MEAS_TEST =                     "The Mock-SAS has been started please enabling CBSD for the power measurement test, the Mock-SAS will keep running during the test"
BAD_CARRIER_BW_SELECT =                     "The combination of carrier number and bandwidth is not valid, please try again"