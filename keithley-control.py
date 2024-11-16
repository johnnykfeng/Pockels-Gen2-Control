import sys
from time import sleep
from PyQt5.QtWidgets import QApplication
from pymeasure.display.windows import ManagedWindow
from pymeasure.experiment import Procedure, Results, unique_filename
from pymeasure.experiment import IntegerParameter, FloatParameter, Parameter
from pymeasure.instruments.keithley.keithley2470 import Keithley2470
from pymeasure.adapters import VISAAdapter
import numpy as np
# import TemperatureController
# import PositionController

import logging
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())



adapter = VISAAdapter("USB0::0x05E6::0x2470::04625649::INSTR") # For Pockels
keithley = Keithley2470(adapter)

def startup():
    print("Starting up Keithley")
    keithley.reset()
    keithley.use_rear_terminals()
    keithley.write(":OUTPut:INTerlock:STATe OFF")
    keithley.apply_voltage(compliance_current=1e-4)
    keithley.auto_range_source()
    keithley.measure_current(nplc=1)
    sleep(0.1)
    keithley.stop_buffer()
    keithley.disable_buffer()
    print("End of startup")

if __name__ == "__main__":
    startup()
    keithley.beep(392, 1)
    keithley.enable_source()
    # keithley.config_buffer(10)

    keithley.source_voltage = 0
    target_voltage = 100
    keithley.ramp_to_voltage(target_voltage)
    sleep(3)
    keithley.source_voltage = 50
    sleep(3)
    print("End of script")

