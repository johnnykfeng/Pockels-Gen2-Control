"""
Python class to control the Keithley 2470 SourceMeter
Use the pyvisa library to communicate with the instrument
and raw SCPI commands to control the instrument

For SCPI commands, refer to the Keithley 2470 Reference Manual
https://www.tek.com/en/manual/source-measure-units/model-2470-high-voltage-1-2400-graphical-series-sourcemeter
"""

# %%
import pyvisa
import numpy as np
import time
import pandas as pd
import matplotlib.pyplot as plt

rm = pyvisa.ResourceManager()
print(rm.list_resources())


def data_parser(data, n_columns):
    pass


class Keithley2470Control:
    class_verbose = False

    def __init__(self, address, timeout=20000):
        self.address = address
        self.instrument = rm.open_resource(self.address)
        self.instrument.timeout = timeout
        self.instrument.read_termination = "\n"
        self.instrument.write_termination = "\n"

    def _check_connection(self):
        idn = self.query("*IDN?")
        if idn:
            self._idn = idn
            print(f"Connected to {idn}.")
        else:
            self.disconnect()
            print("Instrument could not be identified.")

    ## METHODS ##
    def reset(self):
        print("Resetting the instrument")
        self.instrument.write("*RST;:STAT:PRES;:*CLS;")

    def beep(self, frequency, duration, verbose=class_verbose):
        self.instrument.write(f":SYST:BEEP {frequency:g}, {duration:g}")
        if verbose:
            print(f"Beeping at {frequency} Hz for {duration} seconds")

    def use_front_terminals(self):
        print("Using front terminals")
        self.instrument.write(":ROUT:TERM FRON")

    def use_rear_terminals(self):
        print("Using rear terminals")
        self.instrument.write(":ROUT:TERM REAR")

    def disconnect(self) -> None:
        self.instrument.close()

    ## QUERY commands #
    def get_idn(self):
        return self.instrument.query("*IDN?")

    def write(self, command: str, verbose=class_verbose) -> None:
        self.instrument.write(command)
        if verbose:
            print(f"Sent: {command}")

    def query(self, command: str, verbose=class_verbose) -> str:
        if verbose:
            print(f"Query: {command}")
        return self.instrument.query(command)

    def number_of_readings(self):
        return int(self.query(":TRAC:ACT?"))

    def read_buffer(self, bufferName="defbuffer1"):
        act = self.query(":TRAC:ACT? '{}'".format(bufferName))
        if act == "0":
            print("No data in buffer")
            return None
        else:
            return self.query(
                f":TRAC:DATA? 1, {int(act)}, '{bufferName}',REL, SOUR, SOURUNIT, READ, UNIT"
            )

    def get_buffer_dataframe(
        self,
        columns=["Relative time", "Source", "Source Unit", "Reading", "Reading Unit"],
    ):
        n_readings = self.number_of_readings()
        raw_data = self.read_buffer()
        raw_data = raw_data.split(",")
        if raw_data is None or n_readings == 0:
            return None
        if len(raw_data) % len(columns) != 0:
            print("Data columns do not match the number of columns")
            return None

        df = pd.DataFrame()
        for c in range(len(columns)):
            data_parsed = raw_data[c :: len(columns)]
            df[columns[c]] = data_parsed

        return df


# if __name__ == "__main__":

# %%
KEITHLEY_2470_ADDRESS = "USB0::0x05E6::0x2470::04625649::INSTR"
keithley = Keithley2470Control(KEITHLEY_2470_ADDRESS)
# print(keithley.get_idn())
keithley._check_connection()
keithley.reset()
keithley.beep(500, 1)
keithley.use_rear_terminals()

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
columns = ["Relative time", "Source", "Source Unit", "Reading", "Reading Unit"]
df = keithley.get_buffer_dataframe(columns=columns)
# convert the columns to numeric
df["Relative time"] = pd.to_numeric(df["Relative time"])
df["Source"] = abs(pd.to_numeric(df["Source"]))
df["Reading"] = abs(pd.to_numeric(df["Reading"]))
print(df.info())
print(df)

df.plot(x="Source", y="Reading", kind="line", marker="o")
plt.xlabel("Voltage (V)")
plt.ylabel("Current (A)")
plt.title("IV Curve")
plt.show()

# %% Close the instrument
# keithley.disconnect()
# print("Keithley 2470 closed")
