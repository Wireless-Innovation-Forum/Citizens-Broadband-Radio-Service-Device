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
from Tkinter import *
from PIL import ImageTk, Image
from model.Utils import Consts as consts
import tkMessageBox
import random
import os
import time

class GUIFramework(Frame):

    def __init__(self,master=None):
        self.csv_choise = None
        self.folder_Name = None
        Frame.__init__(self,master)
        self.master.title("CBRS PROJECT")
        self.grid(padx=10,pady=10)
        self.specificFolderFrame = None
        self.Create_Open_Widget()
        self.mainloop()
        

    def Create_Open_Widget(self):
        path = "C:/Users/iagmon/Downloads/airspan-logo.jpg"
        pilImage = Image.open(path)
        image200x100 = pilImage.resize((100, 100), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(image200x100)
        panel = Label(self, image = img)
        panel.image = img
        panel.grid(row = 0 , column = 0,sticky=W,padx=10, pady=10) 
        ct = [random.randrange(256) for x in range(3)]
        brightness = int(round(0.299*ct[0] + 0.587*ct[1] + 0.114*ct[2]))
        ct_hex = "%02x%02x%02x" % tuple(ct)
        bg_colour = '#' + "".join(ct_hex)
        self.lbText = Label(self, text=consts.SET_CSV_FILE_MESSAGE,
                            fg='White' if brightness < 120 else 'Black', 
                            bg=bg_colour,borderwidth=2, relief="groove")
        self.lbText.grid(row=1, column=0,padx=10, pady=10)     
        self.tkvar = StringVar(self)
        self.tkvar.__init__()
 
        # Dictionary with options   
        choices = []
        for file in os.listdir("C://Users//iagmon//cbrsPython//testFiles"):
            choices.append(file)
        self.tkvar.set(choices[0]) # set the default option
         
        popupMenu = OptionMenu(self, self.tkvar, *choices)
        popupMenu.grid(row = 2, column =0,sticky=W)
         
        # on change dropdown value
        def change_dropdown(*args):
            print( self.tkvar.get() )
         
        # link function to change dropdown
        self.tkvar.trace('w', change_dropdown)
        
        self.btnDisplay = Button(self, text="send CSV File Name", command=self.set_Csv_File)
        self.btnDisplay.grid(row=4, column=2,sticky =E)
        
        self.selectFolderYesOrNoLabel = Label(self, text=consts.ADD_TEST_TO_SPECIFIC_FOLDER_MESSAGE,
                            fg='White' if brightness < 120 else 'Black', 
                            bg=bg_colour,borderwidth=2, relief="groove")
        self.selectFolderYesOrNoLabel.grid(row=3, column=0,sticky=W,padx=10, pady=10)
        
        yesOrNoOption = []
        yesOrNoOption.append("yes")
        yesOrNoOption.append("no")
        
        self.yesOrNoVar = StringVar(self)
        self.yesOrNoVar.set(yesOrNoOption[1]) # set the default option
         
        popupMenu = OptionMenu(self, self.yesOrNoVar, *yesOrNoOption)
        popupMenu.grid(row = 4, column =0,sticky=W)
        
        def open_Yes_Or_No_Folder(*args):
            if self.yesOrNoVar.get()=="yes":
                self.specificFolderFrame = Label(self, text="typeNameOfFolder",
                           fg='White' if brightness < 120 else 'Black', 
                            bg=bg_colour,borderwidth=2, relief="groove")
                self.specificFolderFrame.grid(row=5, column=0,sticky=W,padx=10, pady=10)
                self.e1 = Entry(self.master)
                self.e1.grid(row=6, column=0, sticky=N+W ,columnspan=30,padx=10, pady=10)
            if(self.yesOrNoVar.get()=="no"):
                self.specificFolder.grid_forget()
                self.e1.grid_forget()
                          
        self.yesOrNoVar.trace('w', open_Yes_Or_No_Folder)
        
    def set_Csv_File(self):
        self.csv_choise = self.tkvar.get()
        if(self.specificFolderFrame!=None):
            self.folder_Name = self.e1.get()
        self.quit()
        
        
    def wait_Until_Sent_Csv_File(self):
        testInputProperty = []
        while(self.csv_choise==None):
            time.sleep(0.5)  
        if(".csv" in self.csv_choise):  
            testInputProperty.append(self.csv_choise[:-4])
        if(self.folder_Name!="" and self.folder_Name != None):
            testInputProperty.append(self.folder_Name)
        return testInputProperty
    
    def quit(self):
        self.master.destroy()
        

    def add_Logo(self):
        path = "C:/Users/iagmon/Downloads/airspan-logo.jpg"
        img = ImageTk.PhotoImage(Image.open(path))
        panel = Label(self, image = img)
        panel.pack(side = "bottom", fill = "both", expand = "yes")

