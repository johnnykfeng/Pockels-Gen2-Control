from Devices.temperature_controller import TC720control
import time
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
os.environ["KIVY_NO_CONSOLELOG"] = "1"      # Turns off annoying logging

from Devices.camera_automation import CameraAutomation
from Devices.keithley2470control import Keithley2470Control, BufferElements

cam = CameraAutomation()
ktly = Keithley2470Control("USB0::0x05E6::0x2470::04625649::INSTR", "REAR")
ktly.initialize_instrument_settings(current_limit=10e-6, 
                                    current_range=10e-6, 
                                    auto_range=False, 
                                    NPLC=10, 
                                    averaging_state=False,
                                    auto_zero=True,
                                    source_measure_delay=0.1,
                                    source_readback=True)
TC = TC720control("com6")

# save_folder = r"C:\Program Files\Xeneth\Data\Drop1000V_T-dependent_study\M78439-A0_AnodeRemade"

buffer_columns = [
    BufferElements.DATE,
    BufferElements.TIME,
    BufferElements.READING,
    BufferElements.SOURCE]

def get_buffer_dataframe(buffer_data, buffer_columns=buffer_columns):
    buffer_data = buffer_data.split(",") # Split the buffer data string into a list
    buffer_dataframe = pd.DataFrame()
    for i in range(len(buffer_columns)):
        buffer_dataframe[buffer_columns[i].name] = buffer_data[i :: len(buffer_columns)]
    return buffer_dataframe

def update_IV_data(IV_data, buffer_columns=buffer_columns):
    buffer_columns_string = ", ".join([col.name for col in buffer_columns])
    buffer_data = ktly.query(f":READ? 'defbuffer1', {buffer_columns_string}")
    buffer_dataframe = get_buffer_dataframe(buffer_data, buffer_columns)
    buffer_dataframe['TEC_temperature'] = TC.read_temp1()
    IV_data = pd.concat([IV_data, buffer_dataframe], ignore_index=True)
    return IV_data

def routine_low_temp_annealing(temperature, temp_ramp_time_min, annealing_time_min, target_voltage=-1000):

    IV_data = pd.DataFrame()

    print(f"\n1. Ramp Voltage to {target_voltage}V")
    ktly.ramp_voltage(target_voltage, step_size=10, step_delay=0.5)

    time.sleep(10)
    print("\n1.1. Initial current measurements")
    for _ in range(3):
        ktly.write("*WAI")
        IV_data = update_IV_data(IV_data)
        print(f"Keithley buffer data: \n{IV_data.iloc[-1]}")
        time.sleep(10)

    print(f"\n2. Ramp temperature to {temperature}C for {temp_ramp_time_min} minutes")
    TC.set_temperature(temperature=temperature, wait_time=temp_ramp_time_min*60)

    start_time = time.time()
    print(f"\n3. Annealing for {annealing_time_min} minutes at {temperature}C")
    while time.time() - start_time < annealing_time_min * 60:
        print("--- Take measurement ---")
        IV_data = update_IV_data(IV_data)
        print(f"Keithley buffer data: \n{IV_data.iloc[-1]}")
        time.sleep(10) 

    print(f"\nTotal annealing time: {((time.time() - start_time)/60.0):.2f} minutes")

    print("\n4. Going back to room temperature 23C")
    TC.set_temperature(temperature=23, 
                       wait_time = annealing_time_min*60)
    TC.write_output_enable('0') # Turn off TEC power

    print("\n5. Take more current measurements at room temperature")
    for _ in range(3):
        ktly.write("*WAI")
        IV_data = update_IV_data(IV_data)
        print(f"Keithley buffer data: \n{IV_data.iloc[-1]}")
        time.sleep(10)

    return IV_data

IV_data = routine_low_temp_annealing(temperature=30, 
                            temp_ramp_time_min=1, 
                            annealing_time_min=2, 
                            target_voltage=-1000)
print(IV_data)

save_folder = Path(r"TEST_DATA/Low_temp_annealing")
save_folder.mkdir(parents=True, exist_ok=True)
sensor_id = "DXXXXX"
save_path = save_folder / f"{sensor_id}_IV_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
IV_data.to_csv(save_path, index=True)

print("Annealing over. Voltage ramping to 0V")
ktly.ramp_voltage(0, 10, 0.3)
ktly.disable_output()
ktly.disconnect()
print("--- Keithley 2470 closed ---")

