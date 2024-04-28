
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QStatusBar, QToolBar, QPushButton, QLabel, QLineEdit
from PyQt6.QtCore import  Qt
from PyQt6.QtGui import QFont
from keithleyComms  import Keithley2450
import pyqtgraph as pg
from IVAnalysis import deriv_Vbd, FwdAnalysis
import numpy as np

class IVAnalysis(QMainWindow,Keithley2450):
    def __init__(self,x,y, *args, **kwargs):
        # super(MainWindow, self).__init__(*args, **kwargs)
        QMainWindow.__init__(self,*args,**kwargs)
        # Keithley2450.__init__(self)
        pg.setConfigOptions(antialias=True)
        self.setWindowTitle("IV Analysis")
        self.Volts = x
        self.Current = y

        self.initToolBar()#Initialise toolbar
        self.setStatusBar(QStatusBar(self))

        
        self.graphWidget = pg.PlotWidget()
        my_font = QFont("Helvetica", 16)
        self.graphWidget.setLabel('bottom', "Voltage [V]")
        self.graphWidget.setLabel('left', "Current [A]")
        self.graphWidget.getAxis("bottom").label.setFont(my_font)
        self.graphWidget.getAxis("left").label.setFont(my_font)
        self.graphWidget.setBackground('#000000')
        pen = pg.mkPen(color=(105, 255, 255),width=5)
        
        self.graphWidget.addLegend()
        self.graphWidget.showGrid(x=True, y=True)
        self.data = self.graphWidget.plot(self.Volts, self.Current, pen=pen,fillLevel=-0.3, brush=(105,105,105,50),name = "Original IV")
        self.graphWidget.setLimits(xMin=(min(self.Volts)), xMax=max(self.Volts), yMin=min(self.Current), yMax=max(self.Current))
        # self.graphWidget.A
        self.Comms = QLabel("Powered by ElDAWWG IVAnalysis{} code {} {}".format(u'\u2122','\U0001F60E','\U0001F919','\U0001F919'))
        self.TM = QLabel("<a href='https://www.youtube.com/watch?v=xm3YgoEiEDc'>SezzaDAWWG Software</a> ©")
        self.TM.setStatusTip("Welcome to another SezzaDAWWG{} software solution! {} {} {}".format(u'\u2122','\U0001F60E','\U0001F919','\U0001F919'))
        self.TM.setAlignment(Qt.AlignmentFlag.AlignRight)
        #Define layout
        layout = QGridLayout()
        layout.addWidget(self.graphWidget,0,0,1,5)
        layout.addWidget(self.Comms,2,0)
        layout.addWidget(self.TM,3,4)

        widget = QWidget()
        widget.setMinimumSize(1000, 500)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def derivAnalysis(self):
        Vs = float(self.Vstart.text())
        Ve = float(self.Vend.text())
        fthresh = float(self.f_thresh.text())
        self.voltage, self.dydx, self.breakdown, self.breakdown_error = deriv_Vbd(self.Volts,self.Current,Vstart=Vs, Vstop=Ve,f_thresh = fthresh)
        self.Comms.setText("Breakdown: {}[V], Breakdown error: {}[V]".format(round(self.breakdown[0],4),round(self.breakdown_error[0],4)))
        self.update_plot_Reverse()

    def FwdAnalysis(self):
        self.Resistance, self.perr, self.DiodeVoltage, self.popt = FwdAnalysis(self.Volts,self.Current,float(self.FwdThreshDialog.text()))
        self.Comms.setText("Resistance: {} [Ohm], Resistance Error {:#.4g} [Ohm], I intersect Error {:#.4g} [A] , Diode Voltage: {}[V]".format(round(self.Resistance,4),1/self.perr[0],self.perr[1],round(self.DiodeVoltage,4)))
        self.update_plot_Fwd()

    def update_plot_Reverse(self):
        self.graphWidget.plot(x=[self.breakdown[0],self.breakdown[0]],y=[0,max(self.dydx)],pen=pg.mkPen(color=(255, 0, 0),width=5),fillLevel=-0.3, brush=(105,105,105,50),name = "Breakdown")
        self.graphWidget.plot(x=[self.breakdown[0]- self.breakdown_error[0],self.breakdown[0]- self.breakdown_error[0]],y=[0,max(self.dydx)],pen=pg.mkPen(color=(255, 255, 255),width=5,style=Qt.PenStyle.DashLine),fillLevel=-0.3, brush=(105,105,105,50),name = "Breakdown error")
        self.graphWidget.plot(x=[self.breakdown[0]+ self.breakdown_error[0],self.breakdown[0]+ self.breakdown_error[0]],y=[0,max(self.dydx)],pen=pg.mkPen(color=(255, 255, 255),width=5,style=Qt.PenStyle.DashLine),fillLevel=-0.3, brush=(105,105,105,50))
        self.data.setData(self.voltage, self.dydx)  # Update the data.
        self.graphWidget.setLabel('left', "dln(I)/dV")
        self.graphWidget.setLimits(xMin=(min(self.voltage)), xMax=max(self.voltage), yMin=min(self.dydx), yMax=max(self.dydx))
     
    def update_plot_Fwd(self):
        def line(x,m,c):
            return m*x+c
        xax=np.array([self.DiodeVoltage,self.Volts[np.argmax(self.Current)]])

        self.graphWidget.plot(x=xax,y=line(xax,*self.popt),pen=pg.mkPen(color=(255, 0, 0),width=5),fillLevel=-0.3, brush=(105,105,105,50),name = "Linear Fit")
        # self.graphWidget.plot(x=[self.breakdown[0]- self.breakdown_error[0],self.breakdown[0]- self.breakdown_error[0]],y=[0,max(self.dydx)],pen=pg.mkPen(color=(255, 255, 255),width=5,style=Qt.PenStyle.DashLine),fillLevel=-0.3, brush=(105,105,105,50),name = "Breakdown error")
        # self.graphWidget.plot(x=[self.breakdown[0]+ self.breakdown_error[0],self.breakdown[0]+ self.breakdown_error[0]],y=[0,max(self.dydx)],pen=pg.mkPen(color=(255, 255, 255),width=5,style=Qt.PenStyle.DashLine),fillLevel=-0.3, brush=(105,105,105,50))
        # self.data.setData(self.voltage, self.dydx)  # Update the data.
        self.graphWidget.setLabel('left', "Current [A]")
        self.graphWidget.setLimits(xMin=(min(self.voltage)), xMax=max(self.voltage), yMin=min(self.dydx), yMax=max(self.dydx))
     
    def initToolBar(self):
        '''
        Initialise Toolbar with all control functions
        '''
        analysis_toolbar = QToolBar("keithley toolbar")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, analysis_toolbar)
        self.dAnalysis = QPushButton("Calculate Breakdown (derivative)")
        self.FwdAnalysisButton = QPushButton("Analyse Forward Bias IV")

        self.dAnalysis.clicked.connect(self.derivAnalysis)
        self.FwdAnalysisButton.clicked.connect(self.FwdAnalysis)
        
        #labels
        self.VoltageStart = QLabel("Voltage Start [V]:")
        self.Vstart = QLineEdit("20")

        self.VoltageEnd = QLabel("Voltage End [V]:")
        self.Vend = QLineEdit("75")
        self.Threshold = QLabel("Threshold:")
        self.f_thresh = QLineEdit("3")
        self.FwdThreshlabel = QLabel("Forward Threshold [A]: ")
        self.FwdThreshDialog = QLineEdit("0.200") #[A]


        self.f_thresh.setStatusTip("Set a multiple of the baseline for locating breakdown")
        self.Vend.setStatusTip("Truncate End Voltage")
        self.Vstart.setStatusTip("Truncate Start Voltage")
        self.dAnalysis.setStatusTip("Determine Breakdown from dln(I)/dV")
        self.FwdThreshDialog.setStatusTip("Set the current threshold, above which the linear fit is applied")
        self.FwdAnalysisButton.setStatusTip("Analyse Forward Bias IV Curve. This will Calcualte Resistance and Diode Voltage of SiPM")
        analysis_toolbar.addWidget(self.VoltageStart)
        analysis_toolbar.addWidget(self.Vstart)
        analysis_toolbar.addWidget(self.VoltageEnd)
        analysis_toolbar.addWidget(self.Vend)
        analysis_toolbar.addWidget(self.Threshold)
        analysis_toolbar.addWidget(self.f_thresh)
        analysis_toolbar.addWidget(self.dAnalysis)
        analysis_toolbar.addWidget(self.FwdThreshlabel)
        analysis_toolbar.addWidget(self.FwdThreshDialog)
        analysis_toolbar.addWidget(self.FwdAnalysisButton)
    
