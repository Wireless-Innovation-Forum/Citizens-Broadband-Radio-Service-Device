'''
Created on Apr 26, 2017

@author: iagmon
'''
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
            
