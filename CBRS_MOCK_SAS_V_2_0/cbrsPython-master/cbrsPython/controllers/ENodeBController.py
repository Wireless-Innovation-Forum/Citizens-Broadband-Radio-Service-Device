class ENodeBController():
    '''
    classdocs
    '''

    def __init__(self,engine):
        '''
        Constructor
        '''     
        self.engine = engine
        
        
    def linker_Between_Flask_To_Engine(self,jsonReq,typeOfCalling):
        return self.engine.process_request(jsonReq,typeOfCalling)
    

    
        
        