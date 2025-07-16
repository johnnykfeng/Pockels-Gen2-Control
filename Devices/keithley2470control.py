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
import sys
sys.path.append(r"C:/Code/Pockels-Gen2-Control")
from utils import countdown_timer
from pathlib import Path
import json

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
    UNIT = "The unit of measure associated with the measurement"

class Keithley2470Control:
    print("Keithley2470Control class initialized version 0.0.1")
    # class_verbose = False
    def __init__(self, 
                 address, 
                 terminal, 
                 timeout=20000, 
                 verbose=False):
        
        self.address = address
        self.instrument = rm.open_resource(self.address) # initialize the instrument
        self.instrument.timeout = timeout
        self.instrument.read_termination = "\n"
        self.instrument.write_termination = "\n"
        self.verbose = verbose
        self.output_state = "OFF" # OFF or ON
        self.running_voltage = 0
        self.running_current = 0
        self.buffer_table = pd.DataFrame()
        self.default_buffer_columns = [
            BufferElements.DATE,
            BufferElements.TIME,
            BufferElements.READING,
            BufferElements.SOURCE,
        ]
        self.IV_data = pd.DataFrame()

        self._check_connection()
        self.reset()

        if terminal == "front":
            self.instrument.write(":ROUT:TERM FRON")
        else:
            self.instrument.write(":ROUT:TERM REAR")

    @staticmethod
    def voltages_log_space(
                           start_voltage:int, 
                            stop_voltage:int, 
                            data_points:int, 
                            near_zero=0.01,
                            round_decimal=None):
        """
        Generate a list of voltages in a logarithmic space between min_voltage and max_voltage.
        The list will have data_points number of elements.
        """
        # near_zero = 0.01 # a number that is almost zero
        if start_voltage < 0 and stop_voltage > 0:
            negatives = -1 * np.geomspace(abs(start_voltage), near_zero, round(data_points / 2))
            positives = np.geomspace(near_zero, abs(stop_voltage), round(data_points / 2))
            voltages = np.concatenate([negatives, positives])
        elif start_voltage < 0 and stop_voltage <= 0:
            if stop_voltage == 0:
                stop_voltage = near_zero
            voltages = -1 * np.geomspace(abs(start_voltage), abs(stop_voltage), data_points)
        elif start_voltage >= 0 and stop_voltage >= 0:
            if start_voltage == 0:
                start_voltage = near_zero
            voltages = np.geomspace(start_voltage, stop_voltage, data_points)
        elif stop_voltage < 0 and start_voltage >=0:
            voltages = -1 * np.geomspace(near_zero, abs(stop_voltage), data_points)

        if round_decimal is not None:
            return np.round(voltages, round_decimal)
        return voltages
    
    @staticmethod
    def voltages_neg_to_pos(
                            max_voltage=1100, 
                            data_points_per_side=10, 
                            higher_voltages_step=100, 
                            near_zero=0.1):
        voltages_A = np.geomspace(near_zero, 100, data_points_per_side)
        voltages_A = np.concatenate([voltages_A, 
                                    np.arange(200, max_voltage+1, higher_voltages_step)])
        voltages_B = voltages_A[::-1]
        voltages_pos = np.concatenate([voltages_A, voltages_B])
        voltages_neg = -1 * voltages_pos
        voltages = np.concatenate([voltages_neg, voltages_pos])
        return voltages
    
    @staticmethod
    def voltages_pos_to_neg(
                            max_voltage=1100, 
                            data_points_per_side=10, 
                            higher_voltages_step=100, 
                            near_zero=0.1):
        voltages_A = np.geomspace(near_zero, 100, data_points_per_side)
        voltages_A = np.concatenate([voltages_A, 
                                    np.arange(200, max_voltage+1, higher_voltages_step)])
        voltages_B = voltages_A[::-1]
        voltages_pos = np.concatenate([voltages_A, voltages_B])
        voltages_neg = -1 * voltages_pos
        voltages = np.concatenate([voltages_pos, voltages_neg])
        return voltages
    
    @staticmethod
    def voltages_zero_to_neg(max_voltage=1100, 
                         data_points_per_side=10, 
                         higher_voltages_step=100, 
                         near_zero=0.1):
        voltages_A = np.geomspace(near_zero, 100, data_points_per_side)
        voltages_A = np.concatenate([voltages_A, 
                                    np.arange(200, max_voltage+1, higher_voltages_step)])
        voltages_B = voltages_A[::-1]
        voltages = np.concatenate([voltages_A, voltages_B])
        return -1*voltages
    
    @staticmethod
    def voltages_zero_to_pos(max_voltage=1100, 
                             data_points_per_side=10, 
                             higher_voltages_step=100, 
                             near_zero=0.1):
        voltages_A = np.geomspace(near_zero, 100, data_points_per_side)
        voltages_A = np.concatenate([voltages_A, 
                                    np.arange(200, max_voltage+1, higher_voltages_step)])
        voltages_B = voltages_A[::-1]
        voltages = np.concatenate([voltages_A, voltages_B])
        return voltages

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
                                       averaging_count=100,
                                       auto_zero=True, # False for faster measurements
                                       source_readback=True, # False for faster measurements
                                       source_measure_delay=None
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

        if auto_zero:
            self.instrument.write(":SENSe:CURRent:AZERo ON")
        else:
            self.instrument.write(":SENSe:CURRent:AZERo OFF")

        if averaging_state: # Turn on averaging
            self.instrument.write(":SENSe:CURRent:AVERage ON")
            self.instrument.write(f":SENSe:CURRent:AVERage:COUNt {str(averaging_count)}")

        if not source_readback:
            self.instrument.write(":SOURce:VOLTage:READ:BACK OFF")
        else:
            self.instrument.write(":SOURce:VOLTage:READ:BACK ON")

        if source_measure_delay is not None:
            self.instrument.write(f":SOURce:VOLTage:DELay {str(source_measure_delay)}")


    def number_of_readings(self, bufferName="defbuffer1"):
        try:
            n_readings = int(self.query(":TRACe:ACTual? '{}'".format(bufferName)))
        except Exception as e:
            print(f"Error getting number of readings: {e}")
            return None
        else:
            return n_readings

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
        buffer_name="defbuffer1"
    ):

        if not all(isinstance(element, BufferElements) for element in buffer_elements):
            raise ValueError("All elements must be of type BufferElements")
        element_names = [element.name for element in buffer_elements]
        n_readings = self.number_of_readings(buffer_name)
        raw_data = self.read_buffer(buffer_elements, buffer_name)
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

        if target_voltage is not None:
            self.instrument.write("*WAI")
            self.instrument.write(f":source:voltage {str(target_voltage)}")
            self.running_voltage = target_voltage    

        if self.output_state == "OFF":
            self.enable_output()

    def read_current(self):
        return self.query(":SENSe:CURRent?")
        

    def ramp_voltage(self, target_voltage, step_size, step_delay):
        if self.running_voltage > target_voltage:
            while self.running_voltage > target_voltage:
                self.running_voltage -= step_size
                # self.instrument.write("*WAI")
                # self.instrument.write(f":SOURce:VOLTage {str(target_voltage)}")
                self.set_voltage(self.running_voltage)
                time.sleep(step_delay)
        elif self.running_voltage < target_voltage:
            while self.running_voltage < target_voltage:
                self.running_voltage += step_size
                # self.instrument.write("*WAI")
                # self.instrument.write(f":SOURce:VOLTage {str(target_voltage)}")
                self.set_voltage(self.running_voltage)
                time.sleep(step_delay)
        else:
            print("Target voltage reached")

    def basic_IV_measurement(self, voltages, buffer_name="defbuffer1"):
        for voltage in voltages:
            self.set_voltage(voltage)
            time.sleep(1)
            current = self.query(":READ? 'defbuffer1', READing")
            print(f"Voltage: {voltage}, Current: {current}")


    def get_last_buffer_dataframe(self, buffer_data, buffer_columns=None):
        """
        Args:
            buffer_data (str): The buffer data as a string
            buffer_columns (list): The columns to be included in the dataframe
        Returns:
            pd.DataFrame: The last row of the buffer data as a dataframe
        """
        buffer_data = buffer_data.split(",")
        row_df = pd.DataFrame()
        if buffer_columns is None:
            buffer_columns = self.default_buffer_columns
        for i in range(len(buffer_columns)):
            row_df[buffer_columns[i].name] = buffer_data[i :: len(buffer_columns)]
        return row_df
    
    def get_last_buffer_dict(self, buffer_data, buffer_columns=None):
        """
        Args:
            buffer_data (str): The buffer data as a string
            buffer_columns (list): The columns to be included in the dataframe
        Returns:
            dict: The last row of the buffer data as a dictionary
        """
        buffer_data = buffer_data.split(",")
        # print(f"buffer_data: {buffer_data}")
        row_dict = {}
        if buffer_columns is None:
            buffer_columns = self.default_buffer_columns
        for i in range(len(buffer_columns)):
            # row_dict[buffer_columns[i].name] = buffer_data[i :: len(buffer_columns)][-1]
            row_dict[buffer_columns[i].name] = buffer_data[i]
        # print(f"row_dict: {row_dict}")
        return row_dict
    
    def update_IV_data(self, voltage,buffer_columns=None):
        """
        Args:
            IV_data (pd.DataFrame): The IV data as a dataframe
            buffer_columns (list): The columns to be included in the dataframe
            **kwargs: Additional columns to be added to the dataframe
        Returns:
            pd.DataFrame: The updated IV data as a dataframe
        """
        if buffer_columns is None:
            buffer_columns = self.default_buffer_columns
        buffer_columns_string = ", ".join([col.name for col in buffer_columns])
        buffer_data = self.query(f":READ? 'defbuffer1', {buffer_columns_string}")
        buffer_dict = self.get_last_buffer_dict(buffer_data, buffer_columns)
        buffer_dict['SET_VOLTAGE'] = voltage
        self.IV_data = pd.concat([self.IV_data, pd.DataFrame([buffer_dict])], ignore_index=True)
        return self.IV_data
    
    def set_limit_and_range(self, voltage_range, current_limit):
        self.instrument.write(f":SOURCE:VOLTage:RANGe {str(voltage_range)}")
        self.instrument.write(f":SENSe:CURRent:RANGe {str(current_limit)}")
        self.instrument.write(f":SOURCE:VOLTage:ilimit {str(current_limit)}")

    def continuous_measurement_trigger_model(self, samples, buffer_name="defbuffer1"):
        """
        Load the ramp trigger model
        Args:
            samples (int): The number of samples to read from the buffer
        """
        self.instrument.write(":TRIGger:BLOCK:BUFFer:CLEar 1")
        self.instrument.write(":TRIGger:BLOCK:SOURce:STATe 2, ON")
        self.instrument.write(":TRIGger:BLOCK:DELay:CONStant 3, 0")
        self.instrument.write(f":TRIGger:BLOCK:MDIGitize 4, '{buffer_name}', 1")
        self.instrument.write(f":TRIGger:BLOCK:BRANch:COUNter 5, {samples}, 4")
        
    def load_shutoff_trigger_model(self, samples, buffer_name='defbuffer1'):
        """
        Load the shutoff trigger model
        The sequence of events is as follows:
        - Clear the bufferd
        - Digitize the buffer
        - Set the branch counter to half the number of samples
        - Disable the source
        - Set the delay to 0
        - Digitize the buffer
        - Set the branch counter to half the number of samples
        """
        self.instrument.write(":TRIGger:BLOCK:BUFFer:CLEar 1")
        self.instrument.write(":TRIGger:BLOCK:MDIGitize 2, 'defbuffer1', 1")
        self.instrument.write(":TRIGger:BLOCK:BRANch:COUNter 3, " + str(samples/2) + ", 2")
        self.instrument.write(":TRIGger:BLOCK:SOURce:STATe 4, OFF")
        self.instrument.write(":TRIGger:BLOCK:DELay:CONStant 5, 0")
        self.instrument.write(":TRIGger:BLOCK:MDIGitize 6, 'defbuffer1', 1")
        self.instrument.write(":TRIGger:BLOCK:BRANch:COUNter 7, " + str(samples/2) + ", 6")

    def config_buffer(self, points, delay=0, buffer_name="defbuffer1"):
        self.instrument.write(":STAT:PRES;*CLS;*SRE 1;:STAT:OPER:ENAB 512;")
        self.instrument.write(":STAT:OPER:MAP 0, 4918, 4917;:STAT:OPER:ENAB 1;*SRE 128")
        self.instrument.write(f":TRAC:CLEAR '{buffer_name}'")
        self.instrument.write(f":TRAC:FILL:MODE CONT, '{buffer_name}'")
        # self.instrument.write(f":TRIG:LOAD 'SimpleLoop', {points}")

    def advanced_IV_routine(self, 
                            voltages, 
                            source_measure_delay=5, 
                            NPLC=10, 
                            averaging_count=10,
                            camera_callback=None):
        """
        Perform an advanced IV measurement

        TODO:
        - add a callback function to capture camera images for Pockels
        """
        self.instrument.write(":SENSe:CURRent:AZERo ON")
        self.instrument.write(f":SENSe:CURRent:NPLC {str(NPLC)}")
        self.instrument.write(":SENSe:CURRent:AVERage ON")
        self.instrument.write(f":SENSe:CURRent:AVERage:COUNt {str(averaging_count)}")
        # self.instrument.write(f":SOURce:VOLTage:DELay {str(source_measure_delay)}")

        for idx, voltage in enumerate(voltages):

            print(f"\n--- Step {idx+1}/{len(voltages)} ---")

            voltage = np.round(voltage, 3)
            if abs(voltage) < 0.21:
                print("Setting limit and range to 0.2 V and 1e-7 A")
                self.set_limit_and_range(voltage_range=0.2, current_limit=1e-7)
            elif abs(voltage) < 2.1:
                print("Setting limit and range to 2 V and 1e-6 A")
                self.set_limit_and_range(voltage_range=2, current_limit=1e-7)
            elif abs(voltage) < 21:
                print("Setting limit and range to 20 V and 1e-5 A")
                self.set_limit_and_range(voltage_range=20, current_limit=1e-6)
            elif abs(voltage) < 210:
                print("Setting limit and range to 200 V and 1e-4 A")
                self.set_limit_and_range(voltage_range=200, current_limit=1e-5)
            elif abs(voltage) < 600:
                print("Setting limit and range to 600 V and 1e-3 A")
                self.set_limit_and_range(voltage_range=1000, current_limit=1e-4)
            else:
                print("Setting limit and range to 1000 V and 1e-3 A")
                self.set_limit_and_range(voltage_range=1000, current_limit=1e-3)

            if abs(voltage) > 200:
                self.instrument.write("*WAI")
                self.ramp_voltage(voltage, step_size=10, step_delay=0.5)
            else:
                self.instrument.write("*WAI")
                self.instrument.write(f":SOURce:VOLTage {str(voltage)}")

            if camera_callback is not None and voltage >= 100:
                camera_callback(voltage)

            self.running_voltage = voltage # update the running voltage attribute
            if self.output_state == "OFF":
                self.enable_output()

            time.sleep(source_measure_delay)
            self.instrument.write(":*WAI")
            self.update_IV_data(voltage=voltage, buffer_columns=None)
        
            print(self.IV_data.tail(1))

        self.ramp_voltage(0, step_size=25, step_delay=0.5)

        self.IV_data['READING'] = self.IV_data['READING'].astype(float)
        self.IV_data['SOURCE'] = self.IV_data['SOURCE'].astype(float)

        print("\nIV measurement complete!\n")
        return self.IV_data

if __name__ == "__main__":

    start_time = time.time()
    KEITHLEY_2470_ADDRESS = "USB0::0x05E6::0x2470::04625649::INSTR"
    ktly = Keithley2470Control(KEITHLEY_2470_ADDRESS, terminal="rear")

    # countdown_timer(seconds=30)
    # Negative Voltages
    # voltages_A = ktly.voltages_log_space(start_voltage=0, 
    #                                     stop_voltage=-100, 
    #                                     data_points=data_points,
    #                                     near_zero=0.1)
    # voltages_B = np.arange(-150, -1101, -50)
    # neg_voltages = np.concatenate([voltages_A, voltages_B])
    # print(f"Negative Voltages: \n{neg_voltages}")
    # IV_data_1 = ktly.advanced_IV_routine(neg_voltages, 
    #                                      source_measure_delay=source_measure_delay)
    # IV_data_1.to_csv(f"{sensor_id}_negative_IV_data.csv", index=False)

    # pos_voltages = neg_voltages * (-1.0)
    # print(f"Positive Voltages: \n{pos_voltages}")

    # IV_data_2 = ktly.advanced_IV_routine(pos_voltages, 
    #                                      source_measure_delay=source_measure_delay)
    # IV_data_2.to_csv(f"{sensor_id}_full_IV_data.csv", index=False)
       
    sensor_id = "D420144"
    datetime = time.strftime("%Y-%m-%d_%H-%M-%S")
    source_measure_delay = 10
    NPLC = 1
    averaging_count = 10
    num_ramp_cycles = 1
    suffix = "LTAB_Annealing_1"
    save_folder = Path(r"C:\Code\Pockels-Gen2-Control\TEST_DATA\I-V data")
    save_folder.mkdir(parents=True, exist_ok=True)
    file_name = f"{sensor_id}_{datetime}_{suffix}"

    # voltages_cycle = ktly.voltages_neg_to_pos(max_voltage=1100, 
    #                                     data_points_per_side=10, 
    #                                     higher_voltages_step=100, 
    #                                     near_zero=0.1)

    voltages_cycle = ktly.voltages_zero_to_neg(max_voltage=1100, 
                                         data_points_per_side=10, 
                                         higher_voltages_step=100, 
                                         near_zero=0.1)
    voltages = []
    for _ in range(num_ramp_cycles):
        voltages.extend(voltages_cycle)
    voltages = np.array(voltages)

    np.set_printoptions(suppress=True) # suppress scientific notation
    print(f"Voltages: \n{voltages}")
    print(f"Number of voltages: {len(voltages)}")
    input_response = input("Press N to stop program. Press Enter to continue: ")
    if input_response.lower() == "n":
        raise KeyboardInterrupt("User stopped program")

    try:
        IV_data = ktly.advanced_IV_routine(voltages, 
                                        source_measure_delay=source_measure_delay,
                                        NPLC=NPLC,
                                        averaging_count=averaging_count)
    except Exception as e:
        print(f"Error: {e}")
        ktly.disable_output()
        ktly.disconnect()
        raise e
    
    try:
        IV_save_path = save_folder / f"IV_data_{file_name}.csv"
        IV_data.to_csv(str(IV_save_path), index=False)
    except Exception as e:
        print(f"Error: {e}")
        ktly.disable_output()
        ktly.disconnect()
        raise e
    
    ktly.disable_output()
    ktly.disconnect()

    end_time = time.time()
    print(f"Total time of measurement: {(end_time - start_time)/60.0} minutes")

    settings_json = {
        "sensor_id": sensor_id,
        "datetime": datetime,
        "source_measure_delay": source_measure_delay,
        "NPLC": NPLC,
        "averaging_count": averaging_count,
        "num_ramp_cycles": num_ramp_cycles
    }

    try:
        json_save_path = save_folder / f"IV_settings_{file_name}.json"
        # json_save_path.mkdir(parents=True, exist_ok=True)
        with open(str(json_save_path), "w") as f:
            json.dump(settings_json, f)

    except Exception as e:
        print(f"Error: {e}")
        raise e
    




