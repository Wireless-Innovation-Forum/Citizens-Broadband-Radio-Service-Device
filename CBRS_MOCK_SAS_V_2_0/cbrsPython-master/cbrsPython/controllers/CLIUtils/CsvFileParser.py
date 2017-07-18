'''
Created on Apr 25, 2017

@author: iagmon
'''
import csv
from controllers.CLIUtils.Step import Step
import errno
import os
class CsvFileParser(object):
    '''
    classdocs
    '''


    def __init__(self,csvFileName):
        '''
        Constructor
        '''
        self.csvFileName = csvFileName
        
    def initializeTestDefinition(self):
        steps = []
        try:
            with open(self.csvFileName+".csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader: 
                    index =0
                    for col in row:   
                        steps.append(Step(row[col],index))
                        index+=1
            return steps
        except:
            raise IOError("the file " + self.csvFileName + " not found")
        
    def find_Number_Of_Cols(self):
        try:
            with open(self.csvFileName+".csv") as csvfile:
                reader = csv.DictReader(csvfile)
                return len(reader.next())
        except:
            raise IOError("the file " + self.csvFileName + " not found")
        
            



