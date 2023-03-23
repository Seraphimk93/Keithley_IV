'''
Upgraded keithley IV Script
main upgrades:
->Moved from TKinter to pyqt6 this comes with more modern looking gui as well as speed increases
->Use of Qthreads to thread most functions. This prevents freezing and overall smoother experience
->Replaced pymeasure with custom class, pymeasure is very limited and quite slow 

Seraphim Koulosousas 2023, seraphim.koulosousas.2021@live.rhul.ac.uk
'''
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QApplication, QWidget, QPushButton, QGridLayout,QLineEdit, QLabel, QToolBar,QStatusBar
from PyQt6.QtCore import QThread,  Qt, pyqtSignal
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import numpy as np
from keithleyComms  import Keithley2450
import csv

class TakeIV(QThread,Keithley2450):
    dataChanged = pyqtSignal(list)
    def __init__(self,start,end,step,timeDelay,Resource, *args,**kwargs):
        QThread.__init__(self, *args, **kwargs)
        Keithley2450.__init__(self,Resource)
        self.StartV = start
        self.EndV = end
        self.Steps = step
        self.timeDelay = timeDelay
        
        #self.Enable()
        print(self.k)
        print("connected")
        
    def TakeIV(self):
        self.STOP = False
        steps = (float(self.EndV)-float(self.StartV))/float(self.Steps)
        print("steps:", steps)
        for i in range(int(steps)):
            if self.STOP ==True:
                break
            self.SourceVoltage(float(self.StartV) + i*float(self.Steps))
            V = self.MeasureVoltage()
            I = self.MeasureCurrent()
            #I = np.random.uniform(0,1)
            #V = float(self.StartV) + i*float(self.Steps)
            print(V,I)
            self.dataChanged.emit([V,float(I)])
            # self.dataChanged.emit('{}'.format(np.random.uniform(0.5,0.7)))
            QThread.msleep(int(self.timeDelay))


    def end(self):
        self.STOP = True
        self.finished.emit()


class RampDown(QThread,Keithley2450):
    dataChanged = pyqtSignal(list)
    def __init__(self,start,end,step,timeDelay,Resource, *args,**kwargs):
        QThread.__init__(self, *args, **kwargs)
        Keithley2450.__init__(self,Resource)
        self.StartV = start
        self.EndV = end
        self.Steps = step
        self.timeDelay = timeDelay

        self.Enable()
        print("connected")
        
    def RampDown(self):
        self.STOP = False
        steps = (float(self.EndV)-float(self.StartV))/float(self.Steps)
        print("steps:", steps)
        for i in range(int(steps)):
            if self.STOP ==True:
                break
                print("break")
            self.SourceVoltage(float(self.EndV) - i*float(self.Steps))
            #V = self.MeasureVoltage()
            I = self.MeasureCurrent()
            #I = np.random.uniform(0,1)
            V = float(self.EndV) - i*float(self.Steps)
            self.dataChanged.emit([float(V),float(I)])
            # self.dataChanged.emit('{}'.format(np.random.uniform(0.5,0.7)))
            QThread.msleep(int(self.timeDelay))


    def end(self):
        self.STOP = True
        self.finished.emit()


class Track(QThread,Keithley2450):
    dataChanged = pyqtSignal(list)
    def __init__(self,timeDelay,Resource, *args,**kwargs):
        QThread.__init__(self, *args, **kwargs)
        Keithley2450.__init__(self,Resource)
        self.timeDelay= timeDelay
        
    def TrackIV(self):
        self.STOP = False
        while self.STOP==False:
            V = self.MeasureVoltage
            I = self.MeasureCurrent
            self.dataChanged.emit([V,I])
            # self.dataChanged.emit('{}'.format(np.random.uniform(0.5,0.7)))
            QThread.msleep(int(self.timeDelay))


    def end(self):
        self.STOP = True
        self.finished.emit()



class MainWindow(QMainWindow,Keithley2450):
    def __init__(self, *args, **kwargs):
        # super(MainWindow, self).__init__(*args, **kwargs)
        QMainWindow.__init__(self,*args,**kwargs)
        Keithley2450.__init__(self)

        pg.setConfigOptions(antialias=True)
        self.setWindowTitle("Keithley 1 IV")

        #Initialise arrays for storing Voltage and current
        self.Volts = []
        self.Current = [] 

        
        self.initToolBar()#Initialise toolbar
        self.setStatusBar(QStatusBar(self))


        self.LiveVoltage = QLabel("Voltage [V]: ")
        self.LiveCurrent = QLabel("Current [uA]: ")
        self.Comms = QLabel("Welcome to another SezzaDAWWG{} software solution! {} {} {}".format(u'\u2122','\U0001F60E','\U0001F919','\U0001F919'))
        self.TM = QLabel("SezzaDAWWG Software ©",)
        self.TM.setStatusTip("Welcome to another SezzaDAWWG{} software solution! {} {} {}".format(u'\u2122','\U0001F60E','\U0001F919','\U0001F919'))
        self.TM.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        #Create Graph to Plot IV
        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setLabel('bottom', "Voltage [V]")
        self.graphWidget.setLabel('left', "Current [A]")
        self.graphWidget.setBackground('#000000')
        pen = pg.mkPen(color=(255, 255, 255),width=5)
        self.data_line =  self.graphWidget.plot(self.Volts, self.Current, pen=pen,fillLevel=-0.3, brush=(105,105,105,50))


        #Define layout
        layout = QGridLayout()
        layout.addWidget(self.graphWidget,0,0,1,5)
        layout.addWidget(self.Comms,2,0)
        layout.addWidget(self.TM,3,4)
        layout.addWidget(self.LiveVoltage,2,3)
        layout.addWidget(self.LiveCurrent,2,4)



        widget = QWidget()
        widget.setMinimumSize(1000, 500)
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        
        
        

    def initToolBar(self):
        '''
        Initialise Toolbar with all control functions
        '''
        keithley_toolbar = QToolBar("keithley toolbar")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, keithley_toolbar)

        #keithley 1 controls 
        self.keithley_connect = QPushButton("Connect Keithley 1")
        self.keithley_Disconnect = QPushButton("Disconnect Keithley 1")
        self.keithley_Enable = QPushButton("Enable Keithley 1")
        self.keithley_Disable = QPushButton("Disable Keithley 1")
        self.keithley_takeIV = QPushButton("Take IV")
        self.RampDown = QPushButton("RampDown")
        self.StopButton = QPushButton("Stop")
        self.GoToButton = QPushButton("Goto")
        self.SaveAS = QPushButton("Save as..")
        
        #connect keithley 1 controls to functions
        self.keithley_connect.clicked.connect(self.ConnectKeithley)
        self.keithley_Disconnect.clicked.connect(self.Disconnect)
        self.keithley_Enable.clicked.connect(self.Enable)
        self.keithley_Disable.clicked.connect(self.Disable)
        self.keithley_takeIV.clicked.connect(self.TakeIV)
        self.StopButton.clicked.connect(self.Stop)
        self.SaveAS.clicked.connect(self.SavePlot)
        self.GoToButton.clicked.connect(self.GoTo)
        self.RampDown.clicked.connect(self.RampDownVoltage)

        #User defined Inputs
        self.start = QLabel("Start Voltage [V]")
        self.end = QLabel("End Voltage [V]")
        self.steps = QLabel("Step size [V]")
        self.timeDelay = QLabel("Time Delay [ms]")
        self.GoToValue = QLabel("Go To [V]")
        self.k1start = QLineEdit()
        self.k1end = QLineEdit()
        self.k1steps = QLineEdit()
        self.k1timeDelay =QLineEdit()
        self.GoToValueInput =QLineEdit()
        

        self.ToggleInputs(False) #keep buttons shaded out till keithley is connected

        self.keithley_connect.setStatusTip("Connect to Keithley 1")
        self.keithley_Disconnect.setStatusTip("Disconnect from Keithley 1")
        self.keithley_Enable.setStatusTip("Enable Keithley 1 Output")
        self.keithley_Disable.setStatusTip("Disable Keithley 1 Output")
        self.keithley_takeIV.setStatusTip("Take I-V Curve")
        self.StopButton.setStatusTip("Stop I-V Curve Measurement")
        self.SaveAS.setStatusTip("Save I-V Curve")
        self.GoToButton.setStatusTip("Jump to specific Voltage")
        self.RampDown.setStatusTip("Ramp the Voltage Down")
        self.k1start.setStatusTip("Enter the IV Curve Starting Voltage [V]")
        self.k1end.setStatusTip("Enter the IV Curve Ending Voltage [V]")
        self.k1steps.setStatusTip("Enter the IV Curve Voltage Increments [V]")
        self.k1timeDelay.setStatusTip("Enter the the IV Curve Time Delay in milliseconds")
        self.GoToValueInput.setStatusTip("Enter a Voltage to Go To")
    
        #Add Controsl and user inputs to toolbar
        keithley_toolbar.addWidget(self.keithley_connect)
        keithley_toolbar.addWidget(self.keithley_Disconnect)
        keithley_toolbar.addWidget(self.keithley_Enable)
        keithley_toolbar.addWidget(self.keithley_Disable)
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
        keithley_toolbar.addWidget(self.GoToValue)
        keithley_toolbar.addWidget(self.GoToValueInput)
        keithley_toolbar.addWidget(self.GoToButton)
        keithley_toolbar.addWidget(self.SaveAS)

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
        self.k1 = self.Connect('USB0::0x05E6::0x2450::04490665::INSTR')
        self.ToggleInputs(True)
        self.Comms.setText("Keithley is Connected")

    def Disconnect(self):
        #self.worker.end()
        self.Disable()
        self.SourceVoltage(0)
        self.ToggleInputs(False)
        

    def TakeIV(self):
        start = self.k1start.text()
        end = self.k1end.text()
        step = self.k1steps.text()
        timeDelay = self.k1timeDelay.text()
        self.thr = QThread()
        self.worker = TakeIV(start,end,step,timeDelay,self.k1)
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
        self.worker.end()
        self.RDworker.end()
        self.stop = True

    def GoTo(self):
        self.SourceVoltage(self.GoToValueInput.text())
        I=self.MeasureCurrent()
        self.Volts.append(float(self.GoToValueInput.text()))
        self.Current.append(float(I))
        self.data_line.setData(self.Volts, self.Current)
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
        self.k1end.setEnabled(Bool)
        self.k1steps.setEnabled(Bool)
        self.k1timeDelay.setEnabled(Bool)
        self.GoToValue.setEnabled(Bool)
        self.RampDown.setEnabled(Bool)
        self.GoToValueInput.setEnabled(Bool)
   
 

    def update_plot(self,data):
        self.Volts.append(data[0])
        self.Current.append(data[1])  # Add a new random value.
        self.data_line.setData(self.Volts, self.Current)  # Update the data.
        self.LiveVoltage.setText(str("%.2f" % round(data[0], 2)))
        self.LiveCurrent.setText(str("%.2f" % round(data[1], 2)))
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


def main():

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
   


if __name__ == '__main__':
    main()
