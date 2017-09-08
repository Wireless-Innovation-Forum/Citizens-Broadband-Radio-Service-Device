'''
Created on Jun 1, 2017

@author: iagmon
'''


class loggerObserver(object):
    '''
    classdocs
    '''
 
    def __init__(self,dirPath):
        self.observers = []
        self.dirPath = dirPath
 
    def register(self, observer):
        if not observer in self.observers:
            self.observers.append(observer)
 
    def unregister(self, observer):
        if observer in self.observers:
            self.observers.remove(observer)
 
    def unregister_all(self):
        if self.observers:
            del self.observers[:]
 
    def update_observers(self, *args, **kwargs):
        for observer in self.observers:
            observer.update(*args, **kwargs)
            
    def start_Test(self,loggerName,folderName=None):
        for observer in self.observers:
            observer.startTest(self.dirPath,loggerName,folderName)
    
    def start_Step(self,json_dict,typeOfCalling,ipRequestAddress=None):
        for observer in self.observers:
            observer.startStep(json_dict,typeOfCalling,ipRequestAddress)
                       
    def finish_Step(self,response,typeOfCalling,stepStatus):
        for observer in self.observers:
            observer.finishStep(response,typeOfCalling,stepStatus)
            
    def finish_Test(self,msg,isCmdOutput,testStatus,additionalComments = None):
        for observer in self.observers:
            observer.finishTest(msg,isCmdOutput,testStatus,additionalComments)
            
    def print_to_Logs_Files(self,message,isCmdOutput):
        for observer in self.observers:
            observer.print_to_Logs_Files(message,isCmdOutput)

    def print_To_Terminal(self,message):
        for observer in self.observers:
            observer.print_To_Terminal(message)