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