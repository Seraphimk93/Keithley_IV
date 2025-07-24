Simple GUI to communicate with Keithley 2450 

- development branch is a much better GUI but its still a bit buggy 

# Windows Setup
You will need NI Visa installed on the computer 

you will also need to change line 7 in `KeithleyComms.py` from :

~~~python
self.rm = pyvisa.ResourceManager("@py")
~~~

to 

~~~python
self.rm = pyvisa.ResourceManager()
~~~


you will also need to install pyvisa 


# Linux Setup 

if running on linux you will still need to install the NI visa drivers  -- though this is more of a pain on Linux

you will also need to install pyvisa 

leave line 7 in `KeithleyComms.py` as is 


# Using GUI

Linux:
~~~console
[foo@bar ~] python3 keithley_IV.py
~~~

Windows powershell:
~~~powershell
PS C:\> python keithley_IV.py
~~~
