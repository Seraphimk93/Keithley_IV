'''
Simple GUI to take IV curves using a keithley 2450 source meter

Seraphim Koulosousas 05/11/2022
'''

import tkinter as tk 
from tkinter.filedialog import askopenfilename, asksaveasfilename
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.lines import lineStyles
import matplotlib.pyplot as plt
import numpy as np
import time
import csv
from pymeasure.instruments.keithley import Keithley2450
from pymeasure.adapters import VISAAdapter


class IVCurve:
    def __init__ (self, master):
        ##initialise master
        master.title("SEZZAView - Keithley 1")
        bkgcolor = "LightSteelBlue3"
        fontcolor = "Black"
        
        ##keithley.source_current = 0

        self.x=[]
        self.y=[]
        self.Tgly = False
        self.Tglx = False
        
        # create all of the main containers
        top_frame = tk.Frame(master,relief=tk.RAISED,bd=1, bg=bkgcolor, width=450, height=50, pady=3)
        center = tk.Frame(master, bg=bkgcolor, width=50, height=40, padx=3, pady=3)
        self.btm_frame = tk.Frame(master, bg='white', width=450, height=45, pady=3)
        btm_frame2 = tk.Frame(master, bg='black', width=450, height=60, pady=3)
        # ctr_left = tk.Frame(center, bg='SteelBlue1', width=100, height=190)

        # layout all of the main containers
        master.grid_rowconfigure(1, weight=1)
        master.grid_columnconfigure(0, weight=1)

        top_frame.grid(row=0, sticky="ew")
        center.grid(row=1, sticky="nsew")
        self.btm_frame.grid(row=3, sticky="ew")
        btm_frame2.grid(row=4, sticky="ew")

        # create the center widgets
        center.grid_rowconfigure(0, weight=1)
        center.grid_columnconfigure(1, weight=1)

        btm_frame2.grid_columnconfigure(1,weight=1)
        btm_frame2.grid_columnconfigure(0,weight=1)

        self.btm_frame.grid_columnconfigure(0,weight=1)
        self.btm_frame.grid_columnconfigure(1,weight=1)
        self.btm_frame.grid_rowconfigure(0, weight=1)

        
        ctr_left = tk.Frame(center, relief=tk.RAISED ,bd=1,bg=bkgcolor, width=200, height=190)
        ctr_mid = tk.Frame(center, bg=bkgcolor, width=250, height=190, padx=3, pady=3)
        # ctr_right = tk.Frame(center, bg='green', width=100, height=190, padx=3, pady=3)
        # ctr_left.grid_rowconfigure(8,weight=1,minsize=50)
        # ctr_left.grid_columnconfigure(1,weight=1,minsize=50)
        ctr_left.grid(row=0, column=0, sticky="ns")
        ctr_mid.grid(row=0, column=1, sticky="nsew")



        # ctr_right.grid(row=0, column=2, sticky="ns")

        # # txt_edit = tk.Text(master) # create the large master
        # frm_buttons = tk.Frame(master, relief=tk.RAISED, bd=2)
        btn_open = tk.Button(top_frame, text="Open",command=self.open_file,highlightbackground=bkgcolor)
        btn_save = tk.Button(top_frame, text="Save As...",command=self.save_file,highlightbackground=bkgcolor)


        ##assign buttons to the geometry
        btn_open.grid(row=0, column=0, sticky="ew", padx=5)
        btn_save.grid(row=0, column=1, sticky="ew", padx=5)


        ##### plot functions###
        tglLogy = tk.Button(top_frame, text="Toggle log(y)",command=self.ToggleLog_y,highlightbackground=bkgcolor)
        tglLogy.grid(row=0,column=2,sticky="ew",padx=5)

        tglLogx = tk.Button(top_frame, text = "Toggle Log(x)", command=self.ToggleLog_x,highlightbackground=bkgcolor)
        tglLogx.grid(row=0,column=3,sticky = "ew",padx=5)

        ##### Keithley controls #
        conn = tk.Button(top_frame, text="Connect Keithley",command=self.connect,highlightbackground=bkgcolor)
        conn.grid(row=0, column=4, sticky="ew", padx=5)

        turnOn = tk.Button(top_frame, text="Enable Keithley",command=self.enable,highlightbackground=bkgcolor)
        turnOn.grid(row=0, column=5, sticky="ew", padx=5)

        turnOff = tk.Button(top_frame, text="Disable Keithley",command=self.disable,highlightbackground=bkgcolor)
        turnOff.grid(row=0, column=6, sticky="ew", padx=5)

        shutDwn = tk.Button(top_frame, text="ShutDown Keithley",command=self.shutdown,highlightbackground=bkgcolor)
        shutDwn.grid(row=0, column=7, sticky="ew", padx=5)

        #### IV INPUTS Controls ###
        tk.Label(ctr_left, text="Start Voltage [V]",bg=bkgcolor,fg = fontcolor).grid(row=0,sticky="w")
        self.start_voltage = tk.Entry(ctr_left)
        self.start_voltage.grid(row=1)

        tk.Label(ctr_left, text="End Voltage [V]",bg=bkgcolor,fg = fontcolor).grid(row=2,sticky="w")
        self.end_voltage = tk.Entry(ctr_left)
        self.end_voltage.grid(row=3)

        tk.Label(ctr_left,text ="Step Size [V]",bg=bkgcolor,fg = fontcolor).grid(row=4,sticky="w")
        self.step_size = tk.Entry(ctr_left)
        self.step_size.grid(row=5)

        tk.Label(ctr_left,text ="Time Delay [s]",bg=bkgcolor,fg = fontcolor).grid(row=6,sticky="w")
        self.Time_delay = tk.Entry(ctr_left)
        self.Time_delay.grid(row=7)


       
        tk.Button(ctr_left,text='Track', command=self.track,highlightbackground=bkgcolor).grid(row=8,column=0,sticky="ew")
        tk.Button(ctr_left, text='Take IV Curve', command=self.TakeIVCurve,highlightbackground=bkgcolor).grid(row=9,column=0,sticky="ew")
        tk.Button(ctr_left,text="Ramp Down..", command= self.ramp_down,highlightbackground=bkgcolor).grid(row=10,column=0,sticky="ew")
        tk.Button(ctr_left, text='Stop', command=self.stop_run,highlightbackground=bkgcolor).grid(row=11,column=0,sticky="ew")
        tk.Button(ctr_left, text='Clear Canvas', command=self._clear,highlightbackground=bkgcolor).grid(row=12,column=0,sticky="ew")
        
        ##### Manual Controls #####
        tk.Label(ctr_left,text = "Go To [V]",bg=bkgcolor,fg=fontcolor).grid(row=13,sticky="w")
        self.Manual_voltage = tk.Entry(ctr_left)
        self.Manual_voltage.grid(row=14)
        self.Manual_voltage.bind('<Return>',self.go_to)

        tk.Button(ctr_left,text="Go", command=self.go_to,highlightbackground=bkgcolor).grid(row=15,sticky="ew")
        tk.Button(ctr_left,text="Voltage +", command=self.increase,highlightbackground=bkgcolor).grid(row=16,sticky="ew")
        tk.Button(ctr_left,text="Voltage -", command=self.decrease,highlightbackground=bkgcolor).grid(row=17,sticky="ew")
        
    
        
        
        ####Create figure
        fig = Figure()
        self.ax = fig.add_subplot(111)
        self.ax.set_xlabel("Volts [V]")
        self.ax.set_ylabel("Current [A]")
        self.ax.set_facecolor("lightgrey")
        self.ax.minorticks_on()
        self.ax.grid(which="major",ls="--",color="black")
        self.canvas = FigureCanvasTkAgg(fig,master=ctr_mid)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
     
        ### Add Toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, ctr_mid,)
        toolbar.update()
        toolbar.pack()




       
        ### Verbose Stuff ###
        self.v = tk.StringVar()
        self.v2 = tk.StringVar()
        tk.Label(self.btm_frame,fg=fontcolor,bg="white", textvariable=self.v2).grid(row=0,column=0,sticky="w")
        tk.Label(self.btm_frame,fg=fontcolor,bg="white", textvariable=self.v).grid(row=0,column=1,sticky="e")

        ### Misc
        tk.Label(btm_frame2,text ="© Sezza Dawwwg Software",bg="black",fg = "white").grid(column=1,sticky="e")

       
    def track(self):
        '''
        Function to just kepp track of values
        '''
        self.STOP = False
        while (self.STOP==False):
            self.keithley.measure_voltage()
            v = self.keithley.voltage
            self.keithley.measure_current()
            i = self.keithley.current
            self.x.append(v)
            self.y.append(i)
            self.plot_point()
            self.v.set("Voltage [V]: {} Current [A]: {}".format(round(v,3), i))


    def TakeIVCurve(self):
        '''
        container class to take IV Curve which we can mess about with
        '''
        self.v2.set("Taking IV Curve...")
        if len(self.start_voltage.get())==0:
            self.v2.set("Please Enter Start Voltage")
            return

        if len(self.end_voltage.get())==0:
            self.v2.set("Please Enter End Voltage")
            return
        SV = float(self.start_voltage.get())
        EV = float(self.end_voltage.get())

        if SV > EV:
            self.v2.set("Start voltage must be less than End Voltage")
            return
        step = float(self.step_size.get())
        td = float(self.Time_delay.get())
        if step ==0:
            self.v2.set("Step Size must be larger than 0")
            return
        if td ==0:
            self.v2.set("Time delay must be larger than 0")
            return
        # x = np.linspace(0,100,1000)
        # y = np.sin(x)   
        self.x = []
        self.y = []
        self.keithley.source_voltage = SV
        self.keithley.measure_voltage()
        temp= self.keithley.voltage
        self.STOP = False
        
        while(temp < EV)&(self.STOP==False):
            # print(temp,np.sin(temp))
            # tk.Label(self.btm_frame, text="{}, {}".format(temp,np.sin(temp))).grid(row=0)
            self.keithley.measure_voltage()
            temp = float(self.keithley.voltage)
            self.keithley.measure_current()
            I = self.keithley.current
            self.v.set("Voltage [V]: {} Current [A]: {}".format(round(temp,3), I))
            
            self.x.append(temp)
            self.y.append(I)
            self.plot_point()
            
            self.keithley.source_voltage = temp + float(self.step_size.get())
            # self.ax.plot(self.x,self.y)
            # self.canvas.draw()
            # self.canvas.flush_events()
            time.sleep(td)

        self.v2.set("IV Curve Complete.")
        # x, y = self.line.get_data()
        # self.line.set_ydata(y - 0.2 * x)
        # self.canvas.draw()

    def ramp_down(self):
        self.v2.set("Ramping Down...")
        # SV = float(self.start_voltage.get())
        # EV = float(self.end_voltage.get())
        # if SV < EV:
        #     self.v2.set("End Voltage is above Start Voltage!")
        #     return
        if len(self.Time_delay.get())==0:
            self.v2.set("Time Delay Not Defined!")
            return

        step = float(self.step_size.get())
        td = float(self.Time_delay.get())
        if td ==0:
            self.v2.set("Time delay must be larger than 0")
            return

        if step ==0:
            self.v2.set("Step Size must be larger than 0")
            return
        self.keithley.measure_voltage() 
        temp = float(self.keithley.voltage)
        self.STOP = False
        
        while (temp > 1) & (self.STOP==False):
            # print(temp,np.sin(temp))
            # tk.Label(self.btm_frame, text="{}, {}".format(temp,np.sin(temp))).grid(row=0)

            self.keithley.measure_voltage()
            temp = float(self.keithley.voltage)
            self.keithley.measure_current()
            i = float(self.keithley.current)

            self.v.set("Voltage [V]: {} Current [A]: {}".format(round(temp,3), i))
            
            
##            self.keithley.measure_voltage() 
##            temp=self.keithley.voltage
            self.x.append(temp)
            self.y.append(self.keithley.current)
            
            self.plot_point()
            # self.ax.plot(self.x,self.y)
            # self.canvas.draw()
            # self.canvas.flush_events()
            self.keithley.source_voltage = float(temp - step)
            time.sleep(td)

        if temp<1:
            self.keithley.source_voltage = 0
            self.keithley.measure_voltage()
            temp=self.keithley.voltage
            self.keithley.measure_current()
            i = self.keithley.current
            self.x.append(temp)
            self.y.append(i)
            self.v.set("Voltage [V]: {} Current [A]: {}".format(round(temp,3), i))

        self.v2.set("Ramp Down Complete.")

    def connect(self):
        try:
            adapter = VISAAdapter('<usb address here>') # should look something like this 'USB0::0x05E6::0x2450::04490665::INSTR'
            self.keithley = Keithley2450(adapter)
            self.keithley.apply_voltage()
            ##keithley.source_current_range = 10e-3
            self.keithley.compliance_voltage = 90
            self.keithley.compliance_current = 80e-6
            self.v2.set("Connected to Keithley")
        except ValueError:
            self.v2.set("Cannot Connect to Keithley")

    def enable(self):
        self.keithley.enable_source()

    def disable(self):
        self.keithley.disable_source()

    def shutdown(self):
        self.keithley.shutdown()

    def stop_run(self):
        self.STOP = True

    def go_to(self,event=None):
        self.input_volt = float(self.Manual_voltage.get())
        self.keithley.source_voltage = self.input_volt
        self.keithley.measure_voltage()
        v = self.keithley.voltage
        self.keithley.measure_current()
        i = self.keithley.current
        self.x.append(v)
        self.y.append(i)
        self.plot_point()
        self.v.set("Voltage [V]: {} Current [A]: {}".format(round(v,3),i))

    def increase(self):
        if len(self.Manual_voltage.get())==0:
            self.input_volt=0
        else:
            self.input_volt = float(self.Manual_voltage.get())

        if len(self.step_size.get())==0:
            self.v2.set("Please insert Step Size!!")
            return

        if len(self.x)==0:
            self.x.append(0)
            self.y.append(0)

        self.keithley.measure_voltage()
        v = self.keithley.voltage
        self.keithley.measure_current()
        i= self.keithley.current

        
        self.keithley.source_voltage = v+float(self.step_size.get())
        

        self.x.append(v)
        self.y.append(i)
        self.plot_point()
        self.v2.set("Voltage Increased")
        self.v.set("Voltage [V]: {} Current [A]: {}".format(round(v,3), i))

    def decrease(self):
        if len(self.Manual_voltage.get())==0:
            self.input_volt=0
        else:
            self.input_volt = float(self.Manual_voltage.get())

        if len(self.step_size.get())==0:
            self.v2.set("Please insert Step Size!!")
            return

        if len(self.x)==0:
            self.x.append(0)
            self.y.append(np.sin(0))
        down_value = self.x[-1]-float(self.step_size.get())

        if down_value <= 0:
            self.v2.set("Voltage cannot be set below 0!")
            return

        self.keithley.measure_voltage()
        v = self.keithley.voltage
        self.keithley.measure_current()
        i= self.keithley.current



         
        self.keithley.source_voltage = v-float(self.step_size.get())

        self.x.append(v)
        self.y.append(i)
        self.plot_point()

        self.v2.set("Voltage Decreased!")
        self.v.set("Voltage [V]: {} Current [A]: {}".format(round(v,3), i))


    def plot_point(self):
        self.ax.plot(self.x,self.y)
        self.canvas.draw()
        self.canvas.flush_events()



    def ToggleLog_y(self):
        
        self.Tgly = not self.Tgly
        if(self.Tgly == True):
            self.ax.set_yscale("log")
            self.canvas.draw()
            self.canvas.flush_events()
            
        else:
            self.ax.set_yscale("linear")
            self.canvas.draw()
            self.canvas.flush_events()

    def ToggleLog_x(self):
        
        self.Tglx = not self.Tglx
        if(self.Tglx == True):
            self.ax.set_xscale("log")
            self.canvas.draw()
            self.canvas.flush_events()
            
        else:
            self.ax.set_xscale("linear")
            self.canvas.draw()
            self.canvas.flush_events()

   
    def _clear(self):
        self.ax.clear()
        self.ax.set_xlabel("Volts [V]")
        self.ax.set_ylabel("Current [A]")
        self.ax.minorticks_on()
        self.ax.grid(which="major",ls="--",color="black")
        self.canvas.draw()
        self.x=[]
        self.y=[]


    def save_file(self):
        """Save the current file as a new file."""
        filepath = asksaveasfilename(defaultextension=".csv",filetypes=[("Comma Separated Values", "*.csv"), ("All Files", "*.*")],)
        if not filepath:
            return
        with open(filepath, mode="w",newline="", encoding="utf-8") as output_file:
            write = csv.writer(output_file)
            c = zip(self.x,self.y)
            out = []
            for i,j in c:
                out.append([i,j])
            # text = tk.txt_edit.get("1.0", tk.END)
            write.writerows(out)
        # window.title(f"Simple Text Editor - {filepath}")

    def open_file(self):
        """Open a file for editing."""
        filepath = askopenfilename(filetypes=[("Comma Separated Values", "*.csv"), ("All Files", "*.*")])
        if not filepath:
            return
        # txt_edit.delete("1.0", tk.END)
        # with open(filepath, mode="r", encoding="utf-8") as input_file:
        #     text = input_file.read()
        #     txt_edit.insert(tk.END, text)
        # window.title(f"Simple Text Editor - {filepath}")
        self.x=[]
        self.y=[]
        self._clear()
        with open(filepath, 'r',encoding = "utf-8") as file:
            csvreader = csv.reader(file)
            # header = next(csvreader)
            for row in csvreader:
                self.x.append(float(row[0]))
                self.y.append(float(row[1]))
               

        self.ax.plot(self.x,self.y)
        self.canvas.draw()
        self.canvas.flush_events()
    



window = tk.Tk()
IVCurve(window)
window.mainloop()
