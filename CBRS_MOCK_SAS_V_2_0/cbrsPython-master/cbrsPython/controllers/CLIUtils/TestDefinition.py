import logging
import model.Utils.Consts as consts

class TestDefinition(object):
    
    def __init__(self,steps,numberOfColsFromCsv):        
        self.jsonNamesOfSteps = [[] for i in range(numberOfColsFromCsv)]
        for step in steps:
            self.jsonNamesOfSteps[step.index].append(step.jsonOfStep)
        
            