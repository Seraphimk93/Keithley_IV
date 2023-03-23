import pyvisa

class Keithley2450():
    def __init__(self,Resource=None):
        self.k=None
        if Resource==None:
            self.rm = pyvisa.ResourceManager()
        else:
            self.k = Resource
            self.k.write(":SOUR:FUNC VOLT") # set as a voltage source
            self.CurrentMeasureNPLC(0.1) #set the current measurement NPLC
        print("keithley initialised")
        print(self.k)
        
    def Connect(self,address):
        if self.k != None:
            return
        try:
            self.k = self.rm.open_resource(address)
            print(self.k.query('*IDN?'))
            self.CurrentMeasureNPLC(0.1)
            self.ConnStatus=True
        except ValueError:
            print('[ERROR]: Cannot connect to Scope. Check Scope usb is connected and scope is turned On')
            self.ConnStatus=False
        self.k.write(":SOUR:FUNC VOLT") # set as a voltage source
        print("connect:", self.k)
        return self.k
        
        
    def Source_Voltage_Limit(self,Limit):
        self.k.write(":SOUR:CURR:VLIM {}".format(Limit)) # set voltage limit 
    
    def Source_Current_Limit(self,Limit):
        self.k.write(":SOUR:VOLT:ILIM {}".format(Limit)) # set current limit

    def Enable(self):
        self.k.write(":OUTP ON")
        #print("Enable in keithley class")

    def Disable(self):
        self.k.write(":OUTP OFF")

    def SourceVoltage(self, V):
        # self.k.write(":SOUR:FUNC VOLT")
        self.k.write(":SOURce:VOLT:LEV {}".format(V))

    def MeasureVoltage(self):
        return float(self.k.query("MEAS:VOLT?"))

    def MeasureCurrent(self):
        return float(self.k.query("MEAS:CURR?"))

    def CurrentMeasureNPLC(self,n):
        self.k.write("CURR:NPLC {}".format(n))
