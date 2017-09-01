from abc import abstractmethod
 
class Observer(object):
    @abstractmethod
    def startTest(self,dir_Path,log_Name,folder_Name=None):
        pass
    
    @abstractmethod
    def startStep(self,json_dict,typeOfCalling,ipRequestAddress=None):
        pass
        
    @abstractmethod    
    def finishStep(self,response,typeOfCalling,stepStatus):
        pass
        
    @abstractmethod   
    def finishTest(self,message,isCmdOutput,testStatus):
        pass
    
    @abstractmethod
    def print_to_Logs_Files(self,message,isCmdOutput):
        pass
    
    @abstractmethod
    def print_To_Terminal(self,message):
        pass