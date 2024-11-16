import sys
from time import sleep
from PyQt5.QtWidgets import QApplication
from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment import Procedure, Results, unique_filename
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter
from pymeasure.instruments.keithley.keithley2470 import Keithley2470
from pymeasure.adapters import VISAAdapter
import numpy as np
import logging
import pyvisa


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


# This will print the list of available VISA resources, you can use this to find the address of your instrument
rm = pyvisa.ResourceManager()
rmlist = rm.list_resources()
print(rmlist) 

device_id = Parameter('Device ID')
contact_id = Parameter('Contact ID')
data_points = IntegerParameter('Data Points', default=50)
averages = IntegerParameter('Averages', default=50)
dist_type = Parameter('Distribution (lin/log)', default='log')
min_voltage = FloatParameter('Minimum Voltage', default=-100)
max_voltage = FloatParameter('Maximum Voltage', default=100)
zero_voltage = FloatParameter('Zero Voltage', default=0)

# adapter = VISAAdapter("USB0:0x05E6::0x2470::04473920::INSTR") # For Needle IV Prober
adapter = VISAAdapter("USB0::0x05E6::0x2470::04625649::INSTR") # For Pockels

keithley = Keithley2470(adapter)

keithley.reset()
keithley.use_rear_terminals()
keithley.write(":OUTPut:INTerlock:STATe OFF")
keithley.apply_voltage(compliance_current=1e-4)
keithley.measure_current(nplc=1)
sleep(0.1)
keithley.stop_buffer()
keithley.disable_buffer()
keithley.beep(392, 1)
sleep(2)
keithley.triad(392, 0.25)

keithley.enable_source()
keithley.ramp_to_voltage(-100.0)
keithley.triad(392, 1)
keithley.ramp_to_voltage(0)
keithley.disable_source()
keithley.beep(392, 1)