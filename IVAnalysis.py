''' 
IV Analysis module for RHUL data
Provides functions to use in IV notebook or executable

ELeason Nov 2022
''' 

import sys
import numpy as np
from numpy import diff
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt


def plot_tileIV(IV_dir, file,lbl):
    ''' Function to plot full tile IV curve from csv file'''
    #IV_dir = "/mnt/hpdaq3win/Users/plombox/Documents/DarkSide/Data/vPDU2/IV_curves/"+file
    IV_path = IV_dir + file
    IV = np.loadtxt(IV_path, delimiter=",")
    voltages = np.array(IV[:,0])
    currents = np.array(IV[:,1])

    ind = str(file).find("_")
    tile_no = file[ind+1:ind+4]

    plt.plot(voltages, currents, label=lbl)

def plot_sipmIV(IV_dir, file):
    ''' Function to plot single sipm IV curve from csv file'''
    #IV_dir = "/mnt/hpdaq3win/Users/plombox/Documents/DarkSide/Data/vPDU2/"+file
    IV_path = IV_dir + file
    IV = np.loadtxt(IV_path, delimiter=",")
    voltages = np.array(IV[:,0])
    currents = np.array(IV[:,1])

    ind = str(file).find("sipm")
    sipm_no = file[ind:ind+7] 
    
    plt.plot(voltages, currents, alpha=0.8, label=sipm_no)


##Linear fit part
#define some functions...
def two_lines(x, a, b, c, d):
    '''Two line function used in linear Vbd fit'''
    one = a*x + b
    two = c*x + d
    return np.maximum(one, two)

def linear_Vbd(x, y, Vstart, Vstop):
   '''Function to find Vbd using linear fit
   Arguments: csv IV file, Vstart, Vstop, plot option ("p" to plot)
   Outputs: Vbd value, Vbd error
   '''
   #read in data
   #IV_dir = "/mnt/hpdaq3win/Users/plombox/Documents/DarkSide/Data/vPDU2/IV_curves/"+file
   # IV_path = IV_dir + file
   # IV = np.loadtxt(IV_path, delimiter=",")
   voltages = np.array(x)
   currents = np.array(y)
   #cut to fit in some voltage range
   ind_start = np.argwhere(voltages>=Vstart)[0][0]
   ind_stop = np.argwhere(voltages>=Vstop)[0][0]
   voltages_cut = voltages[ind_start:ind_stop]
   currents_cut = currents[ind_start:ind_stop]

   #fit lines
   pw, cov = curve_fit(two_lines, voltages_cut, currents_cut)

   #Calculate crossover - breakdown voltage
   Vbd = (pw[3] - pw[1]) / (pw[0] - pw[2])
   #print("Breakdown:", Vbd)

   #Find errors on fit parameters
   perr = np.sqrt(np.diag(cov))

   #Error propagation for Vbd
   d_Vbd = Vbd*np.sqrt(((perr[3]**2+perr[1]**2)/(pw[3]-pw[1])**2)
                +((perr[0]**2+perr[2]**2)/(pw[0]-pw[2])**2))
   #print("Error:", d_Vbd)

   #if plot option on make check plots
   # if plot_opt=="p":
   #    fig = plt.figure()
   #    ax = plt.plot(voltages_cut, currents_cut, color='grey')
   #    plt.plot(voltages, voltages*pw[0]+pw[1], linestyle='dotted', color='orange')
   #    plt.plot(voltages, voltages*pw[2]+pw[3], linestyle='dotted', color='red')
   #    plt.vlines([Vbd], 0, 8e-5, color='black', linestyle='dashed')

   #    plt.xlim(0, 77)
   #    plt.ylim(0, 3e-5)
   #    plt.xlabel("Voltage [V]")
   #    plt.ylabel("Current [A]")

   return Vbd, d_Vbd

##Derivative fit part
def deriv_Vbd(x,y, Vstart, Vstop, f_thresh):
   '''Function to find Vbd using derivative method
   Arguments: csv IV file, plot option ("p" to plot)
   Outputs: Vbd value, Vbd error
   '''

   voltages = np.array(x)
   currents = np.array(y)

   #cut to fit in some voltage range
   ind_start = np.argwhere(voltages>=Vstart)[0][0]
   ind_stop = np.argwhere(voltages<=Vstop)[-1][0]
   voltages_cut = voltages[ind_start:ind_stop]
   currents_cut = currents[ind_start:ind_stop]

   #calculate derivative
   dydx = diff(np.log(currents_cut))/diff(voltages_cut)
   #average over 2 bins if want to match Naples 0.2V steps
   R = 1 #number bins to average
   ry = dydx[0:-1].reshape(-1, R).mean(axis=1)
   ry =ry [~np.isnan(ry)]
   rx = voltages_cut[1:-1].reshape(-1, R).mean(axis=1)  
   #find mean of first part
   mean = np.mean(ry[0:10])
   #find where derivative exceeds 1sigma
   f_thr = f_thresh
   i = np.argwhere(ry>f_thr*mean)
   #corresponding Vbd
   Vbd = rx[i][0]

   #print("Breadkdown:", Vbd[0])
   #error
   d_Vbd = Vbd*mean*f_thr/np.sqrt(10)
   #print("Error:", d_Vbd)

  

   return voltages_cut[0:-1], dydx, Vbd, d_Vbd

def FwdAnalysis(voltages,currents, threshold):
    def line(x,m,c):
        return m*x+c
    voltages = np.array(voltages)
    currents = np.array(currents)
    voltageAboveThresh = voltages[currents>threshold][:np.argmax(currents[currents>threshold])]
    currentsAboveThresh = currents[currents>threshold][:np.argmax(currents[currents>threshold])]
    popt, pcov = curve_fit(line,voltageAboveThresh,currentsAboveThresh)
    perr = np.sqrt(np.diag(pcov))

    return 1/popt[0], perr , -popt[1]/popt[0], popt #resistance [Ohm], Parameter errors,  Diode Voltage [V], popt

