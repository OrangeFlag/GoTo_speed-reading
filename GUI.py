from AutoGUI import Ui_MainWindow
from PyQt5.QtCore import QCoreApplication, QTimer
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QAction, QWidget)
from PyQt5 import QtCore, QtGui, QtWidgets

import sys
import os
import platform
from time import sleep
import ctypes

from array import *
from ctypes import *
from sys import exit

if sys.platform.startswith('win32'):
    import msvcrt
elif sys.platform.startswith('linux'):
    import atexit

from select import select
from ctypes import *

try:
    if sys.platform.startswith('win32'):
        libEDK = cdll.LoadLibrary("/bin/win32/edk.dll")
    elif sys.platform.startswith('linux'):
        srcDir = os.getcwd()
        if platform.machine().startswith('arm'):
            libPath = srcDir + "/bin/armhf/libedk.so"
        else:
            libPath = srcDir + "/bin/linux64/libedk.so"
        libEDK = CDLL(libPath)
    else:
        raise Exception('System not supported.')
except Exception as e:
    #print ('Error: cannot load EDK lib:', e)
    exit()



#-------------------------------------------AI
import numpy as np
import keras
from keras.preprocessing import sequence
from keras.utils import np_utils
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.embeddings import Embedding
from sklearn.model_selection import train_test_split
from sklearn import datasets
from sklearn.model_selection import cross_validate

len_vector = 30
Count_vectors = len_vector//5

model = Sequential()
model.add(Dense(len_vector, input_dim=len_vector))
model.add(Activation('sigmoid'))
model.add(Dropout(0.1))
model.add(Dense(1))
model.add(Activation('sigmoid'))

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['acc'])

#model.load_weights("/home/yorick/Analiz_final/Weights.h5py")


#--------------------------------------------------------------------------

class GUI(Ui_MainWindow):
    Timer = [QTimer(), QTimer()]
    i = [0]
    AutomaticSpeed = [False]
    TextMas = []
    Timeout = [600, 1000]
    X = []
    Y = []
    IsEpocConnect = [False]


    ready = 0
    IEE_EmoEngineEventCreate = libEDK.IEE_EmoEngineEventCreate
    IEE_EmoEngineEventCreate.restype = c_void_p
    eEvent = c_void_p(IEE_EmoEngineEventCreate())
    # #print(eEvent, type(eEvent), c_uint(eEvent))
    IEE_EmoEngineEventGetEmoState = libEDK.IEE_EmoEngineEventGetEmoState
    IEE_EmoEngineEventGetEmoState.argtypes = [c_void_p, c_void_p]
    IEE_EmoEngineEventGetEmoState.restype = c_int

    IEE_EmoStateCreate = libEDK.IEE_EmoStateCreate
    IEE_EmoStateCreate.restype = c_void_p
    eState = c_void_p(IEE_EmoStateCreate())

    userID = c_uint(0)
    user = pointer(userID)
    ready = 0
    state = c_int(0)

    alphaValue = c_double(0)
    low_betaValue = c_double(0)
    high_betaValue = c_double(0)
    gammaValue = c_double(0)
    thetaValue = c_double(0)

    alpha = pointer(alphaValue)
    low_beta = pointer(low_betaValue)
    high_beta = pointer(high_betaValue)
    gamma = pointer(gammaValue)
    theta = pointer(thetaValue)

    channelList = array('I', [3, 7, 9, 12, 16])  # IED_AF3, IED_AF4, IED_T7, IED_T8, IED_Pz

    #EPOC
    def EPOCConnect(self):
        # -------------------------------------------------------------------------
        #print ("===================================================================")
        #print ("Example to get the average band power for a specific channel from" \
        #" the latest epoch.")
        #print ("===================================================================")

        # -------------------------------------------------------------------------
        if libEDK.IEE_EngineConnect(bytes("Emotiv Systems-5".encode('utf-8'))) != 0:
            return False
                #print ("Emotiv Engine start up failed.")
        return True




    def EPOC_Get(self):
        self.state = libEDK.IEE_EngineGetNextEvent(self.eEvent)
        if self.state == 0:
            eventType = libEDK.IEE_EmoEngineEventGetType(self.eEvent)
            libEDK.IEE_EmoEngineEventGetUserId(self.eEvent, self.user)
            if eventType == 16:  # libEDK.IEE_Event_enum.IEE_UserAdded
                self.ready = 1
                libEDK.IEE_FFTSetWindowingType(self.userID, 1);  # 1: libEDK.IEE_WindowingTypes_enum.IEE_HAMMING
                #print ("User added")
            
            while self.ready == 1:
                for i in self.channelList:
                    result = c_int(0)
                    result = libEDK.IEE_GetAverageBandPowers(self.userID, i, self.theta, self.alpha, self.low_beta, self.high_beta, self.gamma)
            
                    if result == 0:    #EDK_OK
                        return [float(self.thetaValue.value), float(self.alphaValue.value),
                                                   float(self.low_betaValue.value), float(self.high_betaValue.value), float(self.gammaValue.value)]
     
        elif self.state != 0x0600:
            #print ("Internal error in Emotiv Engine ! ")
            return []
        return []



    def EPOC_Disconnect(self):
        libEDK.IEE_EngineDisconnect()
        libEDK.IEE_EmoStateFree(self.eState)
        libEDK.IEE_EmoEngineEventFree(self.eEvent)
    def AIGet(self, X):
        return model.predict(X)
    def __init__(self):
        super().__init__()
        self.MainWindow = QMainWindow()
        self.setupUi(self.MainWindow)
        self.add()
    def add(self): 
        _translate = QtCore.QCoreApplication.translate
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Чтение"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Исходный текст"))
        #self.verticalSlider.valueChanged.connect(self.lcdNumber.display)
        self.pushButton.clicked.connect(self.StartPause)
        self.pushButton_2.clicked.connect(self.Stop)
        self.checkBox.stateChanged.connect(self.Automatic)
        self.plainTextEdit.textChanged.connect(self.Parse)
        self.lineEdit.setText("300")
        self.lineEdit.editingFinished.connect(self.ChangeTimeout)
        self.Timer[0].timeout.connect(self.ShowWord)

        self.MainWindow.setWindowTitle("Speed reader")
        self.Timer[1].timeout.connect(self.Automatic)
	#KeybordShortcut
        Action = QAction("Up",self.tab)
        Action.setShortcut(QKeySequence("Up"))
        self.tab.addAction(Action)
        Action.triggered.connect(self.UPTrigger)


        Action2 = QAction("Down",self.tab)
        Action2.setShortcut(QKeySequence("Down"))
        self.tab.addAction(Action2)
        Action2.triggered.connect(self.DOWNTrigger)


    def UPTrigger(self):
        self.lineEdit.setText(str(int(self.lineEdit.text())+20))
        self.ChangeTimeout()

    def DOWNTrigger(self):
        self.lineEdit.setText(str(int(self.lineEdit.text())-20))
        self.ChangeTimeout()
 

    def ShowWord(self):
        if (len(self.TextMas) <= self.i[0]):
            self.textBrowser.setHtml("""<p>""" + "This is End" + "</p>")
            return 0   
        self.textBrowser.setHtml("""<p>"""  + self.TextMas[self.i[0]] + "</p>" )
        self.i[0] += 1

    def StartPause(self):
        _translate = QtCore.QCoreApplication.translate
        if (self.Timer[0].isActive()):
               self.Timer[0] = QTimer()
               self.Timer[0].timeout.connect(self.ShowWord)
               self.pushButton.setText(_translate("MainWindow", "Start"))
        else:
               self.Timer[0].start(self.Timeout[0])
               self.pushButton.setText(_translate("MainWindow", "Pause"))
    def Stop(self):
        _translate = QtCore.QCoreApplication.translate
        self.Timer[0] = QTimer()
        self.Timer[0].timeout.connect(self.ShowWord)
        self.pushButton.setText(_translate("MainWindow", "Start"))
        self.i[0] = 0
        
    def Automatic(self):
        self.AutomaticSpeed[0] = self.checkBox.isChecked()
        if (self.AutomaticSpeed[0]):
            if (not self.IsEpocConnect[0]):
                if (not self.EPOCConnect()):
                    self.checkBox.setChecked(False)
                    return
                self.IsEpocConnect[0] = True
            self.X.clear()
            while (len(self.X) != len_vector):
                self.X += self.EPOC_Get()
                sleep(0.1)
            self.Y.clear()
            #print(self.X)
            #print(np.array(self.X).shape)
            Temp = np.array(self.X).reshape(1, 30)
            #print(Temp.shape)
            self.Y += [self.AIGet(Temp)[0][0]]
            #print("self.Y", self.Y)
            self.lineEdit.setText(str(int(int(self.lineEdit.text())+(self.Y[0]-0.5)*20)))
            self.ChangeTimeout()

            self.Timer[1].start(self.Timeout[1])
            
        else:
            self.EPOC_Disconnect()
            self.IsEpocConnect[0] = False
            self.Timer[1] = QTimer()
            self.Timer[1].timeout.connect(self.Automatic)
            
            
            
            
            
        
    def Parse(self):
        self.i[0] = 0
        self.TextMas.clear()
        line = self.plainTextEdit.toPlainText().split()
        for x in line:
            self.TextMas.append(x)
        #print(line)
    def ChangeTimeout(self):
        self.Timeout[0] = int(self.lineEdit.text())
        self.Timer[0].setInterval(self.Timeout[0])
        #print(self.Timeout)