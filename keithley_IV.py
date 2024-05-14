'''
Upgraded keithley IV Script
main upgrades:
->Moved from TKinter to pyqt6 this comes with more modern looking gui as well as speed increases
->Use of Qthreads to thread most functions. This prevents freezing and overall smoother experience
->Replaced pymeasure with custom class, pymeasure is very limited and quite slow 
->Added IV Analysis which does a log derivative analysis to the IV curve

Seraphim Koulosousas 2023, seraphim.koulosousas.2021@live.rhul.ac.uk
'''
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QApplication, QWidget, QPushButton, QGridLayout,QLineEdit, QLabel, QToolBar,QStatusBar,QComboBox
from PyQt6.QtCore import QThread,  Qt, pyqtSignal
from PyQt6.QtGui import QFont
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import numpy as np
from keithleyComms  import Keithley2450
from IV_Analysis import IVAnalysis
import csv
import random


class TakeIV(QThread):
    dataChanged = pyqtSignal(list)
    def __init__(self,start,end,step,timeDelay,Resource, *args,**kwargs):
        QThread.__init__(self, *args, **kwargs)
        # Keithley2450.__init__(self,Resource)
        self.StartV = start
        self.EndV = end
        self.Steps = step
        self.timeDelay = timeDelay
        self.k = Resource
        
        #self.Enable()
        print(self.k)
        print("connected")
        # print("test in class",self.k.test())
        
    def TakeIV(self):
        self.STOP = False
        steps = (float(self.EndV)-float(self.StartV))/float(self.Steps)
        # print("steps:", steps)
        for i in range(int(steps)):
            if self.STOP ==True:
                break
            # print("steps:",float(self.StartV) + i*float(self.Steps))
            v = float(self.StartV) + i*float(self.Steps)
            self.k.SourceVoltage(v)
            V = self.k.MeasureVoltage()
            I = self.k.MeasureCurrent()
            #I = np.random.uniform(0,1)
            #V = float(self.StartV) + i*float(self.Steps)
            print(V,I)
            self.dataChanged.emit([V,float(I)])
            # self.dataChanged.emit('{}'.format(np.random.uniform(0.5,0.7)))
            QThread.msleep(int(self.timeDelay))


    def end(self):
        self.STOP = True
        self.finished.emit()


class RampDown(QThread):
    dataChanged = pyqtSignal(list)
    def __init__(self,start,end,step,timeDelay,Resource, *args,**kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.StartV = start
        self.EndV = end
        self.Steps = step
        self.timeDelay = timeDelay
        self.k  = Resource

        self.k.Enable()
        print("connected")
        
    def RampDown(self):
        self.STOP = False
        self.EndV = self.k.MeasureVoltage()
        steps = (float(self.EndV)-float(self.StartV))/float(self.Steps)
        # print("steps:", steps)
        for i in range(int(steps)):
            if self.STOP ==True:
                break
            self.k.SourceVoltage(float(self.EndV) - i*float(self.Steps))
            #V = self.MeasureVoltage()
            I = self.k.MeasureCurrent()
            #I = np.random.uniform(0,1)
            V = float(self.EndV) - i*float(self.Steps)
            self.dataChanged.emit([float(V),float(I)])
            # self.dataChanged.emit('{}'.format(np.random.uniform(0.5,0.7)))
            QThread.msleep(int(self.timeDelay))
        self.k.SourceVoltage(0)
        I = self.k.MeasureCurrent()
        self.dataChanged.emit([float(0),float(I)])

    def end(self):
        self.STOP = True
        self.finished.emit()


class Track(QThread):
    dataChanged = pyqtSignal(list)
    def __init__(self,timeDelay,Resource, *args,**kwargs):
        QThread.__init__(self, *args, **kwargs)
        self.timeDelay= timeDelay
        self.k=Resource
        
    def TrackIV(self):
        self.STOP = False
        while self.STOP==False:
            V = self.k.MeasureVoltage
            I = self.k.MeasureCurrent
            self.dataChanged.emit([V,I])
            # self.dataChanged.emit('{}'.format(np.random.uniform(0.5,0.7)))
            QThread.msleep(int(self.timeDelay))


    def end(self):
        self.STOP = True
        self.finished.emit()



class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        # super(MainWindow, self).__init__(*args, **kwargs)
        QMainWindow.__init__(self,*args,**kwargs)
        self.k = Keithley2450()

        pg.setConfigOptions(antialias=True)
        self.setWindowTitle("Keithley IV")

        #Initialise arrays for storing Voltage and current
        self.Volts = []
        self.Current = []
        self.clim = 8e-05 # current limit [Amps]
        self.Kdict = {"Keithley 1": 'USB0::0x05E6::0x2450::04490665::INSTR',"Keithley 2":'USB0::0x05E6::0x2450::04563534::INSTR',"Keithley 3":'USB0::1510::9296::04618475::0::INSTR' }
        self.Kcombobox = QComboBox()
        self.Kcombobox.addItem('Keithley 1')
        self.Kcombobox.addItem('Keithley 2')
        self.Kcombobox.addItem('Keithley 3')
        # Kcombobox.addItem('Three')
        # Kcombobox.addItem('Four')
        
        self.initToolBar()#Initialise toolbar
        self.setStatusBar(QStatusBar(self))

        self.V = QLabel("Voltage [V]: ")
        self.C = QLabel("Current [\u03BCA]: ")
        self.LiveVoltage = QLabel("")
        self.LiveCurrent = QLabel("")
        self.Comms = QLabel("Welcome to another SezzaDAWWG{} software solution! {} {} {}".format(u'\u2122','\U0001F60E','\U0001F919','\U0001F919'))
        self.TM = QLabel("<a href='https://www.youtube.com/watch?v=xm3YgoEiEDc'>SezzaDAWWG Software</a> ©")
        self.TM.setStatusTip("Welcome to another SezzaDAWWG{} software solution! {} {} {}".format(u'\u2122','\U0001F60E','\U0001F919','\U0001F919'))
        self.TM.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        #Create Graph to Plot IV
        self.graphWidget = pg.PlotWidget()
        my_font = QFont("Helvetica", 16)
        self.graphWidget.setLabel('bottom', "Voltage [V]")
        self.graphWidget.setLabel('left', "Current [A]")
        # Set your custom font for both axes
        self.graphWidget.getAxis("bottom").label.setFont(my_font)
        self.graphWidget.getAxis("left").label.setFont(my_font)
        self.graphWidget.setBackground('#000000')
        # pen = pg.mkPen(color=(105, 255, 255),width=5)
        self.x1 = [1,2,3,4]
        self.y1 = [0.5,3,2,3]
        self.x2 = [2,3,4,5]
        self.y2 = [0,1,2,3]
        self.graphWidget.addLegend()
        self.graphWidget.showGrid(x=True, y=True)
        r,g,b = random.randint(50,200),random.randint(50,200),random.randint(50,200) #Randomise IV Colours
        pen = pg.mkPen(color=(r, g, b),width=2.5)
        # self.graphWidget.plot(self.Volts, self.Current, pen=pen,fillLevel=-0.3,name=f"IV Curve")
        self.data_line =  self.graphWidget.plot(self.Volts, self.Current, pen=pen,fillLevel=-0.3, brush=(105,105,105,50),name="IV Curve")
        # self.graphWidget.plot(self.x1, self.y1, pen=pen,fillLevel=-0.3, brush=(105,105,105,50),name = "Sensor 1")
        # self.graphWidget.plot(self.x2, self.y2, pen=pg.mkPen(color=(105, 255, 255),width=5),fillLevel=-0.3, brush=(105,105,105,50),name = "Sensor 2")
        
        #Define layout
        layout = QGridLayout()
        layout.addWidget(self.graphWidget,0,0,1,6)
        layout.addWidget(self.Comms,2,0)
        layout.addWidget(self.TM,3,5)
        layout.addWidget(self.V,2,2)
        layout.addWidget(self.LiveVoltage,2,3)
        layout.addWidget(self.C,2,4)
        layout.addWidget(self.LiveCurrent,2,5)
        



        widget = QWidget()
        # widget.setMinimumSize(1000, 700)
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        
        
        

    def initToolBar(self):
        '''
        Initialise Toolbar with all control functions
        '''
        keithley_toolbar = QToolBar("keithley toolbar")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, keithley_toolbar)

        #keithley 1 controls 
        self.keithley_connect = QPushButton("Connect Keithley")
        self.keithley_Disconnect = QPushButton("Disconnect Keithley")
        self.keithley_Enable = QPushButton("Enable Keithley")
        self.keithley_Disable = QPushButton("Disable Keithley")
        # self.keithley_SetCurrentLimit = QPushButton("Set Current limit")
        self.keithley_takeIV = QPushButton("Take IV")
        self.RampDown = QPushButton("RampDown")
        self.StopButton = QPushButton("Stop")
        self.ClearCanvasButton = QPushButton("Clear Canvas")
        self.GoToButton = QPushButton("Goto")
        self.Open = QPushButton("Open File...")
        self.AnalyseIV = QPushButton("Analyse IV")
        
        #connect keithley 1 controls to functions
        self.keithley_connect.clicked.connect(self.ConnectKeithley)
        self.keithley_Disconnect.clicked.connect(self.Disconnect)
        self.keithley_Enable.clicked.connect(self.k.Enable)
        self.keithley_Disable.clicked.connect(self.k.Disable)
        # self.keithley_SetCurrentLimit.clicked.connect(self.SetCurrentLimit)
        self.keithley_takeIV.clicked.connect(self.TakeIVfunction)
        self.StopButton.clicked.connect(self.Stop)
        self.ClearCanvasButton.clicked.connect(self.ClearCanvas)
        self.Open.clicked.connect(self.OpenPlot)
        self.GoToButton.clicked.connect(self.GoTo)
        self.RampDown.clicked.connect(self.RampDownVoltage)
        self.AnalyseIV.clicked.connect(self.Analysis)
        

        #User defined Inputs
        self.current = QLabel("Current Limit [A]")
        self.start = QLabel("Start Voltage [V]")
        self.end = QLabel("End Voltage [V]")
        self.steps = QLabel("Step size [V]")
        self.timeDelay = QLabel("Time Delay [ms]")
        self.GoToValue = QLabel("Go To [V]")
        self.k1current = QLineEdit("{}".format(self.clim))
        self.k1start = QLineEdit("0")
        self.k1end = QLineEdit("75")
        self.k1steps = QLineEdit("0.2")
        self.k1timeDelay =QLineEdit("1")
        self.GoToValueInput =QLineEdit()
        

        self.ToggleInputs(False) #keep buttons shaded out till keithley is connected

        self.keithley_connect.setStatusTip("Connect to Keithley")
        self.keithley_Disconnect.setStatusTip("Disconnect from Keithley")
        self.keithley_Enable.setStatusTip("Enable Keithley Output")
        self.keithley_Disable.setStatusTip("Disable KeithleyOutput")
        self.k1current.setStatusTip("Set Keithley Current Limit, usually 8e-05 [A] for Reverse bias")
        # self.keithley_SetCurrentLimit.setStatusTip("Set Keithley Current Limit, usually 8e-05 [A] for Reverse bias")
        self.keithley_takeIV.setStatusTip("Take I-V Curve")
        self.StopButton.setStatusTip("Stop I-V Curve Measurement")
        self.ClearCanvasButton.setStatusTip("Clear Canvas")
        self.Open.setStatusTip("Open IV file")
        self.GoToButton.setStatusTip("Jump to specific Voltage")
        self.RampDown.setStatusTip("Ramp the Voltage Down")
        self.k1start.setStatusTip("Enter the IV Curve Starting Voltage [V]")
        self.k1end.setStatusTip("Enter the IV Curve Ending Voltage [V]")
        self.k1steps.setStatusTip("Enter the IV Curve Voltage Increments [V]")
        self.k1timeDelay.setStatusTip("Enter the the IV Curve Time Delay in milliseconds")
        self.GoToValueInput.setStatusTip("Enter a Voltage to Go To")
        self.AnalyseIV.setStatusTip("Analyse IV")
        self.Kcombobox.setStatusTip("Select Keithley to connect to")
        
    
        #Add Controsl and user inputs to toolbar
        keithley_toolbar.addWidget(self.Open)
        keithley_toolbar.addWidget(self.Kcombobox)
        keithley_toolbar.addWidget(self.keithley_connect)
        keithley_toolbar.addWidget(self.keithley_Disconnect)
        keithley_toolbar.addWidget(self.keithley_Enable)
        keithley_toolbar.addWidget(self.keithley_Disable)
        keithley_toolbar.addWidget(self.current)
        keithley_toolbar.addWidget(self.k1current)
        # keithley_toolbar.addWidget(self.keithley_SetCurrentLimit)
        keithley_toolbar.addWidget(self.start)
        keithley_toolbar.addWidget(self.k1start)
        keithley_toolbar.addWidget(self.end)
        keithley_toolbar.addWidget(self.k1end)
        keithley_toolbar.addWidget(self.steps)
        keithley_toolbar.addWidget(self.k1steps)
        keithley_toolbar.addWidget(self.timeDelay)
        keithley_toolbar.addWidget(self.k1timeDelay)
        keithley_toolbar.addWidget(self.keithley_takeIV)
        keithley_toolbar.addWidget(self.RampDown)
        keithley_toolbar.addWidget(self.StopButton)
        keithley_toolbar.addWidget(self.ClearCanvasButton)
        keithley_toolbar.addWidget(self.GoToValue)
        keithley_toolbar.addWidget(self.GoToValueInput)
        keithley_toolbar.addWidget(self.GoToButton)
        keithley_toolbar.addWidget(self.AnalyseIV)

    def TrackCurrVolt(self):
        self.TrackThread = QThread()
        self.Trackworker = Track(timeDelay=500,Resource=self.k)
        self.Trackworker.moveToThread(self.TrackThread)
        self.TrackThread.started.connect(self.Trackworker.TrackIV)
        self.Trackworker.dataChanged.connect(self.LiveCurrentVoltage)
        self.Trackworker.finished.connect(self.TrackThread.quit)
        self.Trackworker.finished.connect(self.Trackworker.deleteLater)
        self.TrackThread.finished.connect(self.TrackThread.deleteLater)
        self.TrackThread.start()

    def ConnectKeithley(self):
        address = self.Kdict[self.Kcombobox.currentText()]
        print(address)
        self.k.Connect(address)
        self.ToggleInputs(True)
        self.Comms.setText("Keithley is Connected")
        self.SetCurrentLimit(self.clim)
        print(self.k.test())

    def SetCurrentLimit(self,value):
        self.k.Source_Current_Limit(value)
        self.Comms.setText("Current limit set to: {} Amps".format(value))
        self.clim = "{}".format(value)


    def Disconnect(self):
        #self.worker.end()
        self.Disable()
        self.SourceVoltage(0)
        self.ToggleInputs(False)
        

    def TakeIVfunction(self):
        if len(self.k1current.text())==0:
            self.Comms.setText("Please Insert Current limit")
            return
        # print("take iv function: ", self.k.test())
        start = self.k1start.text()
        end = self.k1end.text()
        step = self.k1steps.text()
        timeDelay = self.k1timeDelay.text()
        self.thr = QThread()
        self.worker = TakeIV(start,end,step,timeDelay,self.k)
        self.worker.moveToThread(self.thr)
        self.thr.started.connect(self.worker.TakeIV)
        self.worker.dataChanged.connect(self.update_plot)
        self.worker.finished.connect(self.thr.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thr.finished.connect(self.thr.deleteLater)
        self.thr.start()

    def RampDownVoltage(self):
        start = self.k1start.text()
        end = self.k1end.text()
        step = self.k1steps.text()
        timeDelay = self.k1timeDelay.text()
        self.Stop()
        self.RDthr = QThread()
        self.RDworker = RampDown(start,end,step,timeDelay,self.k)
        self.RDworker.moveToThread(self.RDthr)
        self.RDthr.started.connect(self.RDworker.RampDown)
        self.RDworker.dataChanged.connect(self.update_plot)
        self.RDworker.finished.connect(self.RDthr.quit)
        self.RDworker.finished.connect(self.RDworker.deleteLater)
        self.RDthr.finished.connect(self.RDthr.deleteLater)
        self.RDthr.start()
 
    def Stop(self):
        self.stop = True
        self.worker.end()
        try:
            if self.RDthr.isRunning():
                self.RDworker.end()
        except RuntimeError:
            print()
        except AttributeError:
            print()
        try:
            if self.thr.isRunning():
                self.thr.end()
        except RuntimeError:
            print()
        except AttributeError:
            print()
    def ClearCanvas(self):
        self.Volts = []
        self.Current= []
        self.data_line.clear()
        # self.data_line.setData(self.Volts, self.Current)  # Update the data.
        self.LiveVoltage.setText(str("%.2f" % round(float(0), 2)))
        self.LiveCurrent.setText(str("%.2f" % round(float(0), 2)))
        

    def GoTo(self):
        if len(self.k1current.text())==0:
            self.Comms.setText("Please Insert Current limit")
            return
        self.k.SourceVoltage(self.GoToValueInput.text())
        I=self.k.MeasureCurrent()
        self.Volts.append(float(self.GoToValueInput.text()))
        self.Current.append(float(I))
        self.data_line.plot(self.Volts, self.Current)
        self.LiveVoltage.setText(str("Voltage [V]: %.2f" % round(float(self.GoToValueInput.text()), 2)))
        self.LiveCurrent.setText(str("Current [A]: %.2f" % round(I, 2)))
        
    def LiveCurrentVoltage(self,data):
        V = float(data[0])
        I = float(data[1])*1e06
        self.LiveVoltage.setText(str("%.2f" % round(V, 2)))
        self.LiveCurrent.setText(str("%.2f" % round(I, 2)))



    def ToggleInputs(self,Bool):
        self.keithley_Enable.setEnabled(Bool)
        self.keithley_Disconnect.setEnabled(Bool)
        self.keithley_Disable.setEnabled(Bool)
        self.keithley_takeIV.setEnabled(Bool)
        self.StopButton.setEnabled(Bool)
        self.GoToButton.setEnabled(Bool)
        self.k1start.setEnabled(Bool)
        self.k1current.setEnabled(Bool)
        # self.keithley_SetCurrentLimit.setEnabled(Bool)
        self.k1end.setEnabled(Bool)
        self.k1steps.setEnabled(Bool)
        self.k1timeDelay.setEnabled(Bool)
        self.GoToValue.setEnabled(Bool)
        self.RampDown.setEnabled(Bool)
        self.GoToValueInput.setEnabled(Bool)
   
 

    def update_plot(self,data):
        self.Volts.append(float(data[0]))
        self.Current.append(float(data[1]))  # Add a new random value.
        print("update plot:", self.Volts[-1], self.Current[-1] )
        # r,g,b = random.randint(50,200),random.randint(50,200),random.randint(50,200) #Randomise IV Colours
        # pen = pg.mkPen(color=(r, g, b),width=2.5)
        # self.graphWidget.plot(self.Volts, self.Current, pen=pen,fillLevel=-0.3,name=f"IV Curve")
        self.data_line.setData(np.array(self.Volts), np.array(self.Current))  # Update the data.
        
        # QApplication.processEvents()
        # self.graphWidget.plot(self.Volts, self.Current, pen=pen,fillLevel=-0.3, brush=(105,105,105,50),name="IV Curve")
        self.LiveVoltage.setText(str("%.2f" % round(float(data[0]), 2)))
        self.LiveCurrent.setText(str("%.2f" % round(float(data[1])*1e06, 2)))
        self.graphWidget.setXRange(min(self.Volts), max(self.Volts), padding=0)
        self.graphWidget.setYRange(min(self.Current), max(self.Current))
        # self.graphWidget.GraphicsScene.mouseEvents.MouseClickEvent()
        # QApplication.processEvents()
        # self.graphWidget.setLimits(xMin=(min(self.Volts)), xMax=max(self.Volts), yMin=min(self.Current), yMax=max(self.Current))
        # QApplication.processEvents()

    def SavePlot(self):
        """Save the current file as a new file."""

        filepath = QFileDialog.getSaveFileName(self, 'Save File')
        # filepath = asksaveasfilename(defaultextension=".csv",filetypes=[("Comma Separated Values", "*.csv"), ("All Files", "*.*")],)
        if not filepath:
            return
        with open(filepath, mode="w",newline="", encoding="utf-8") as output_file:
            write = csv.writer(output_file)
            c = zip(self.Volts,self.Current)
            out = []
            for i,j in c:
                out.append([i,j])
            write.writerows(out)

    def OpenPlot(self):
        filepath = QFileDialog.getOpenFileName(self, 'Open File')
        if len(filepath[0])==0:
            return
        self.Volts=[]
        self.Current=[]
        with open(filepath[0], 'r') as file:
            csvreader = csv.reader(file,delimiter=",")
            for row in csvreader:
                self.update_plot(row)
                # self.Volts.append(float(row[0]))
                # self.current.append(float(row[1]))

        
    def Analysis(self):
        if len(self.Volts) ==0:
            self.Comms.setText("[Error]: No Data has been taken to run analysis.")
            return
        self.IVWindow = IVAnalysis(self.Volts,self.Current)
        self.IVWindow.show()



def main():

    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1400,750)
    window.show()
    app.exec()
   


if __name__ == '__main__':
    main()
