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