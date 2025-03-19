import csv
import os
from time import sleep
import numpy as np
from pymeasure.instruments.keithley.keithley2470 import Keithley2470
from pymeasure.adapters import VISAAdapter

class ItProcedure():
        
    def __init__(self):
        super().__init__()
        adapter = VISAAdapter("USB0::0x05E6::0x2470::04625649::INSTR")
        self.keithley = Keithley2470(adapter)

    def startup(self):
        self.keithley.reset()
        self.keithley.use_rear_terminals()
        self.keithley.apply_voltage(compliance_current=105e-6)
        self.keithley.write(":CURRent:AZERo OFF")
        self.keithley.measure_current(nplc=0.01)
        self.keithley.write(":OUTPut:INTerlock:STATe OFF")
        self.keithley.stop_buffer()
        self.keithley.disable_buffer()

    def execute(self, sensor_id, max_voltage, steps, data_points, temperature):

        voltage_steps = np.linspace(0, max_voltage, steps+1)
        voltage_steps = iter(voltage_steps)
        next(voltage_steps)

        self.keithley.beep(392, 1)

        ### Perform Ramp Captures ###
        for voltage in voltage_steps:
            print("Setting voltage to: " + str(voltage))

            load_ramp_trigger_model(self.keithley, data_points)

            self.keithley.config_buffer(points=data_points)
            self.keithley.current_range = 100e-6

            self.keithley.source_voltage = voltage
            self.keithley.start_buffer()
            self.keithley.wait_for_buffer()

            currents = self.keithley.buffer_data

            data_timestamps = []
            relative_timestamps = [0]
            for idx in range(1, data_points + 1):
                self.keithley.write(":TRACe:DATA? %d, %d, 'defbuffer1', TSTamp" % (idx, idx))
                t = self.keithley.read()
                t = t.split(" ")[1]
                t_h = float(t.split(":")[0])
                t_m = float(t.split(":")[1])
                t_s = float(t.split(":")[2])
                t = t_h * 3600 + t_m * 60 + t_s
                data_timestamps.append(t)
                if idx >= 2:
                    relative_timestamps.append(data_timestamps[idx-1] - data_timestamps[0])
            print("Approximate sampling frequency: %.1f HZ" % (1 / (relative_timestamps[-1] / data_points)))

            source_voltages = []
            for idx in range(1, data_points + 1):
                self.keithley.write(":TRACe:DATA? %d, %d, 'defbuffer1', SOURce" % (idx, idx))
                v = float(self.keithley.read())
                source_voltages.append(v)

            data = []
            for idx, current in enumerate(currents):
                line = {
                    'Buffer Index': idx,
                    'Voltage (V)': source_voltages[idx],
                    'Current (A)': current,
                    'Time (s)': relative_timestamps[idx]
                }
                data.append(line)

            if voltage > -1000:
                voltage_tag = '0' + str(int(abs(voltage)))
            elif voltage == -1000:
                voltage_tag = str(int(abs(voltage)))

            path = 'C:\Code\Pockels-Gen2-Control\TEST_DATA\I-t Data'
            dir_name = sensor_id
            csv_filename = f'{temperature}C_{voltage_tag}V_ramp.csv'
            create_directory_and_csv(path, dir_name, csv_filename, data)

        ### Perform Shutoff Capture ###
        load_shutoff_trigger_model(self.keithley, data_points)
        self.keithley.config_buffer(points=data_points)
        self.keithley.current_range = 100e-6

        self.keithley.beep(392, 1)
        self.keithley.source_voltage = voltage
        self.keithley.start_buffer()
        self.keithley.wait_for_buffer()

        print("Measurement finished")
        self.keithley.disable_source()
        self.keithley.shutdown()
        self.keithley.triad(392, 0.25)
        self.keithley.beep(784, 0.5)

        currents = self.keithley.buffer_data

        data_timestamps = []
        relative_timestamps = [0]
        for idx in range(1, data_points + 1):
            self.keithley.write(":TRACe:DATA? %d, %d, 'defbuffer1', TSTamp" % (idx, idx))
            t = self.keithley.read()
            t = t.split(" ")[1]
            t_h = float(t.split(":")[0])
            t_m = float(t.split(":")[1])
            t_s = float(t.split(":")[2])
            t = t_h * 3600 + t_m * 60 + t_s
            data_timestamps.append(t)
            if idx >= 2:
                relative_timestamps.append(data_timestamps[idx-1] - data_timestamps[0])
        print("Approximate sampling frequency: %.1f HZ" % (1 / (relative_timestamps[-1] / data_points)))

        source_voltages = []
        for idx in range(1, data_points + 1):
            self.keithley.write(":TRACe:DATA? %d, %d, 'defbuffer1', SOURce" % (idx, idx))
            v = float(self.keithley.read())
            source_voltages.append(v)

        data = []
        for idx, current in enumerate(currents):
            line = {
                'Buffer Index': idx,
                'Voltage (V)': source_voltages[idx],
                'Current (A)': current,
                'Time (s)': relative_timestamps[idx]
            }
            data.append(line)

        path = 'C:\Code\Pockels-Gen2-Control\TEST_DATA\I-t Data'
        dir_name = sensor_id
        csv_filename = f'{temperature}C_shutoff.csv'
        create_directory_and_csv(path, dir_name, csv_filename, data)
        
        print("All Done :)")


def load_ramp_trigger_model(keithley, data_points):
    keithley.write(":TRIGger:BLOCK:BUFFer:CLEar 1")
    keithley.write(":TRIGger:BLOCK:SOURce:STATe 2, ON")
    keithley.write(":TRIGger:BLOCK:DELay:CONStant 3, 0")
    keithley.write(":TRIGger:BLOCK:MDIGitize 4, 'defbuffer1', 1")
    keithley.write(":TRIGger:BLOCK:BRANch:COUNter 5, " + str(data_points) + ", 4")

def load_shutoff_trigger_model(keithley, data_points):
    keithley.write(":TRIGger:BLOCK:BUFFer:CLEar 1")
    keithley.write(":TRIGger:BLOCK:MDIGitize 2, 'defbuffer1', 1")
    keithley.write(":TRIGger:BLOCK:BRANch:COUNter 3, " + str(data_points/2) + ", 2")
    keithley.write(":TRIGger:BLOCK:SOURce:STATe 4, OFF")
    keithley.write(":TRIGger:BLOCK:DELay:CONStant 5, 0")
    keithley.write(":TRIGger:BLOCK:MDIGitize 6, 'defbuffer1', 1")
    keithley.write(":TRIGger:BLOCK:BRANch:COUNter 7, " + str(data_points/2) + ", 6")

def create_directory_and_csv(path, dir_name, csv_filename, data):
    full_path = os.path.join(path, dir_name)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    
    csv_file_path = os.path.join(full_path, csv_filename)
    
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
