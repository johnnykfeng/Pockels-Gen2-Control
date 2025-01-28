"""
Python class to control the Keithley 2470 SourceMeter
Use the pyvisa library to communicate with the instrument
and raw SCPI commands to control the instrument

For SCPI commands, refer to the Keithley 2470 Reference Manual
https://www.tek.com/en/manual/source-measure-units/model-2470-high-voltage-1-2400-graphical-series-sourcemeter
"""

# %% DEFINE IMPORTS AND Keithley2470Control CLASS
import pyvisa
import numpy as np
import time
import pandas as pd
import matplotlib.pyplot as plt
from enum import Enum
from typing import List

rm = pyvisa.ResourceManager()
print(rm.list_resources())

class BufferElements(Enum):
    """Enum class to define the buffer elements to be read from the Keithley 2470"""
    DATE = "The date when the data point was measured"
    FORMATTED = "The measured value as it appears on the front panel"
    FRACTIONAL = "The fractional seconds for the data point when the data point was measured"
    READING = "The measurement reading based on the [:SENSE[1]]:FUNCTION[:ON] setting; if no buffer elements are defined, this option is used"
    RELATIVE = "The relative time when the data point was measured"
    SECONDS = "The seconds in UTC (Coordinated Universal Time) format when the data point was measured"
    SOURCE = "The source value; if readback is ON, then it is the readback value, otherwise it is the programmed source value"
    SOURFORMATTED = "The source value as it appears on the display"
    SOURSTATUS = "The status information associated with sourcing. The values returned indicate the status of conditions such as overvoltage protection, source value reading, overtemperature condition, function level limitation, four-wire sense usage, and output status"
    SOURUNIT = "The unit of value associated with the source value"
    STATUS = "The status information associated with the measurement"
    TIME = "The time for the data point"
    TSTAMP = "The timestamp for the data point"
    UNIT = "The unit of measure associated with the measurement"# class BufferElements(Enum):


class Keithley2470Control:
    print("Keithley2470Control class initialized version 0.0.1")
    # class_verbose = False
    def __init__(self, 
                 address, 
                 terminal, 
                 timeout=20000, 
                 verbose=False):
        
        self.address = address
        self.instrument = rm.open_resource(self.address)
        self.instrument.timeout = timeout
        self.instrument.read_termination = "\n"
        self.instrument.write_termination = "\n"
        self.verbose = verbose
        self.output_state = "OFF" # OFF or ON
        self.running_voltage = 0
        self.running_current = 0
        self.buffer_table = pd.DataFrame()

        self._check_connection()
        self.reset()

        if terminal == "front":
            self.instrument.write(":ROUT:TERM FRON")
        else:
            self.instrument.write(":ROUT:TERM REAR")

        
    def _check_connection(self):
        idn = self.query("*IDN?")
        if idn:
            self._idn = idn
            print(f"Connected to {idn}.")
            self.beep(500, 0.5)
            self.beep(500*5/4, 0.5)
            self.beep(500*6/4, 0.5)
        else:
            self.disconnect()
            print("Instrument could not be identified.")

    ## METHODS ##
    def reset(self):
        print("Resetting the instrument")
        self.instrument.write("*RST;:STAT:PRES;:*CLS;")

    def beep(self, frequency, duration):
        self.instrument.write(f":SYST:BEEP {frequency:g}, {duration:g}")
        if self.verbose:
            print(f"Beeping at {frequency} Hz for {duration} seconds")

    def use_front_terminals(self):
        self.instrument.write(":ROUT:TERM FRON")

    def use_rear_terminals(self):
        self.instrument.write(":ROUT:TERM REAR")

    def enable_output(self):
        self.instrument.write(":OUTP ON")
        self.output_state = "ON"
    
    def disable_output(self):
        self.instrument.write(":OUTP OFF")
        self.output_state = "OFF"

    def disconnect(self) -> None:
        self.instrument.close()

    ## QUERY commands #
    def get_idn(self):
        return self.instrument.query("*IDN?")

    def write(self, command: str) -> None:
        self.instrument.write(command)
        if self.verbose:
            print(f"Sent: {command}")

    def query(self, command: str) -> str:
        if self.verbose:
            print(f"Query: {command}")
        return self.instrument.query(command)



    def initialize_instrument_settings(self, 
                                       current_limit=10e-6, 
                                       current_range= 10e-6,
                                       auto_range=False, 
                                       NPLC=1,
                                       averaging_state=True,
                                       averaging_count=100
                                       ):
        
        self.instrument.write(":SOURce:FUNCtion VOLTage")
        self.instrument.write(":SENSe:FUNCtion 'CURRent'") # must have the single quotes
        self.instrument.write(f":SOURce:VOLTage:ilimit {str(current_limit)}")
        self.instrument.write(f":SENSe:CURRent:NPLC {str(NPLC)}")

        if auto_range:
            self.instrument.write(":CURRent:RANGe:AUTO ON")  # Set current range to auto
        else:
            self.instrument.write(":CURRent:RANGe:AUTO OFF")
            self.instrument.write(f":CURRent:RANGe {str(current_range)}")

        if averaging_state: # Turn on averaging
            self.instrument.write(":SENSe:CURRent:AVERage ON")
            self.instrument.write(f":SENSe:CURRent:AVERage:COUNt {str(averaging_count)}")


    def number_of_readings(self, bufferName="defbuffer1"):
        return int(self.query(":TRAC:ACT? '{}'".format(bufferName)))

    def read_buffer(self, buffer_elements: List[BufferElements], bufferName="defbuffer1"):
        act = self.query(":TRAC:ACT? '{}'".format(bufferName))
        if act == "0":
            print("No data in buffer")
            return None
        else:
            element_names = [element.name for element in buffer_elements]
            return self.query(
                f":TRAC:DATA? 1, {int(act)}, '{bufferName}',{', '.join(element_names)}"
            )

    def get_buffer_dataframe(
        self,
        buffer_elements: List[BufferElements],
        bufferName="defbuffer1"
    ):

        if not all(isinstance(element, BufferElements) for element in buffer_elements):
            raise ValueError("All elements must be of type BufferElements")
        element_names = [element.name for element in buffer_elements]
        n_readings = self.number_of_readings(bufferName)
        raw_data = self.read_buffer(buffer_elements, bufferName)
        raw_data = raw_data.split(",")
        if raw_data is None or n_readings == 0:
            return None
        if len(raw_data) % len(buffer_elements) != 0:
            print("Data columns do not match the number of columns")
            return None

        self.buffer_table = pd.DataFrame()
        for i in range(len(buffer_elements)):
            data_parsed = raw_data[i :: len(buffer_elements)]
            self.buffer_table[element_names[i]] = data_parsed

        return self.buffer_table
    
    def set_voltage(self, target_voltage:float, range=1000):
        if range=="auto":
            self.instrument.write(":source:voltage:range:auto on")
        elif isinstance(range, (int, float)):
            self.instrument.write(":source:voltage:range:auto off")
            self.instrument.write(f":source:voltage:range {str(range)}")
        else:
            raise ValueError("Invalid range value. Use 'auto' or a number.")

        if isinstance(target_voltage, (int, float)):
            self.instrument.write(f":source:voltage {str(target_voltage)}")
            self.running_voltage = target_voltage

        if self.output_state == "OFF":
            self.enable_output()
        

    def ramp_voltage(self, target_voltage, step_size, step_delay):
        if self.running_voltage > target_voltage:
            while self.running_voltage > target_voltage:
                self.running_voltage -= step_size
                self.set_voltage(self.running_voltage)
                time.sleep(step_delay)
        elif self.running_voltage < target_voltage:
            while self.running_voltage < target_voltage:
                self.running_voltage += step_size
                self.set_voltage(self.running_voltage)
                time.sleep(step_delay)
        else:
            print("Target voltage reached")

    def set_current_range(self, current_range):
        pass

if __name__ == "__main__":
    pass
    # %% INSTANTIATE THE Keithley2470Control CLASS
    KEITHLEY_2470_ADDRESS = "USB0::0x05E6::0x2470::04625649::INSTR"
    keithley = Keithley2470Control(KEITHLEY_2470_ADDRESS, terminal="rear")

    #%%
    keithley.ramp_voltage(-50, step_size=2, step_delay=0.5)

    print(keithley.running_voltage)

    keithley.write(":READ?")
    keithley.disable_output()
    print(keithley.output_state)
    #%%
    keithley.set_voltage(-40)
    keithley.write(":READ?")

    #%%
    # print(keithley.query(":trace:actual? 'defbuffer1'"))

    # raw_data = keithley.read_buffer()
    # print(raw_data)

    table = keithley.get_buffer_dataframe()
    print(table)


    #%%

    # Initialize the measurement settings
    SOURCE = "VOLT"
    SENSE = "CURR"
    current_limit = 100e-6  # 100 uA
    current_range = 0.001  # 100 uA
    # Number of power line cycles (NPLC) to integrate the measurement
    # Lower NPLC => faster reading rates, increased noise.
    # Higher NPLC => lower reading noise, slower reading rates.
    # min NPLC = 0.01, max NPLC = 10
    NPLC = 0.1

    keithley.write(":SOUR:FUNC VOLT")
    keithley.write(":SENSE:FUNC CURR")
    keithley.write(":CURR:RANGE:AUTO ON")  # Set current range to auto
    # keithley.write(f":current:range {str(current_range)}")
    keithley.write(f":source:voltage:ilimit {str(current_limit)}")
    keithley.write(f":sense:current:nplc {str(NPLC)}")

    print("Starting the measurement")
    Voltages = np.arange(0, -201, -20)
    Currents = np.ones(len(Voltages))
    print(Voltages)
    for i, voltage in enumerate(Voltages):
        keithley.write(":source:voltage {}".format(voltage))
        keithley.write(":OUTP ON")
        time.sleep(1)
        reading = float(keithley.query(":READ?"))
        Currents[i] = reading
        # print(f"Voltage: {voltage} V")
        # print(f"Output: {reading}")
        # time.sleep(0.5)
        keithley.beep(300 + i * 20, 0.5)

    keithley.write(":OUTP OFF")

    # %%
    # columns = ["Relative time", "Source", "Source Unit", "Reading", "Reading Unit"]
    # df = keithley.get_buffer_dataframe(columns=columns)
    # # convert the columns to numeric
    # df["Relative time"] = pd.to_numeric(df["Relative time"])
    # df["Source"] = abs(pd.to_numeric(df["Source"]))
    # df["Reading"] = abs(pd.to_numeric(df["Reading"]))
    # print(df.info())
    # print(df)

    # df.plot(x="Source", y="Reading", kind="line", marker="o")
    # plt.xlabel("Voltage (V)")
    # plt.ylabel("Current (A)")
    # plt.title("IV Curve")
    # plt.show()

    # %% Close the instrument
    # keithley.disconnect()
    # print("Keithley 2470 closed")
