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
import logging
class QuestionHandler(object):
    '''
    classdocs
    '''


    def __init__(self,loggerHandler):
        '''
        Constructor
        '''
        self.loggerHandler = loggerHandler
        
    def ShowQuestionsAndGetAnswersFromClient(self,questionsAndAnswers):
        '''
        the methods open a session with the technician of the questions answer part 
        '''
        answers = []
        correctAnsweres = True
        for questAnswer in questionsAndAnswers:   
            self.loggerHandler.print_to_Logs_Files("the question is : " + questAnswer[consts.QUESTION_NODE] + consts.CHOOSE_ONE_OF_THE_ANSWERS_MESSAGE,True)
            for answer in questAnswer[consts.ANSWERS_NODE]:            
                self.loggerHandler.print_To_Terminal(answer) 
            
            inputAnswer = raw_input()
            self.loggerHandler.print_to_Logs_Files("for the question : " + questAnswer[consts.QUESTION_NODE] + " , the user choose " + str(inputAnswer),True)
            if not inputAnswer == questAnswer[consts.EXPECT_ANSWER_NODE]:
                correctAnsweres = False
            
        self.loggerHandler.print_To_Terminal(consts.ADDITIONAL_COMMENTS_MESSAGE)
        inputAnswer = raw_input()
        
        if(correctAnsweres):
            answers.append(consts.PASS_MESSAGE)
        else:
            answers.append(consts.FAIL_MESSAGE)
        answers.append(inputAnswer) 
        return answers
            
