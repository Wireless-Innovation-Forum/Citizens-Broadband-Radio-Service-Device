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
                        pathExpected = os.path.join(str(self.dirPath),str(expression).rstrip())
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
        
            



