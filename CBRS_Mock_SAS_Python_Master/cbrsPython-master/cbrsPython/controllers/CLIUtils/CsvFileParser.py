'''
Created on Apr 25, 2017

@author: iagmon
'''
import csv
from controllers.CLIUtils.Step import Step
import errno
import os
from pathlib import Path
class CsvFileParser(object):
    '''
    classdocs
    '''


    def __init__(self,csvFileName,confFile,dirPath):
        '''
        Constructor
        '''
        self.csvFileName = csvFileName
        self.confFile = confFile
        self.dirPath = dirPath
        
    def initializeTestDefinition(self):
        steps = []
        try:
            with open(self.csvFileName+".csv") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader: 
                    index =0
                    for col in row:
                        expression = Path(os.path.join(self.confFile.getElementsByTagName("jsonsRepoPath")[0].firstChild.data,row[col]))
                        #pathExpected = Path((str(Path(__file__).parents[3]) + str(expression)))
                        pathExpected = os.path.join(str(self.dirPath),str(expression))
                        if row[col]!="":
                            if Path.exists(Path(pathExpected)) :
                                steps.append(Step(row[col],index))
                                index+=1
                            else:
                                raise Exception 
            return steps
        except Exception as e:
            raise IOError("the file " + self.csvFileName + " or the jsons file inside the csv rows not found")
        
    def find_Number_Of_Cols(self):
        try:
            with open(self.csvFileName+".csv") as csvfile:
                reader = csv.DictReader(csvfile)
                return len(reader.next())
        except:
            raise IOError("the file " + self.csvFileName + " not found")
        
            



