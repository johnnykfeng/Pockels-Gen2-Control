from Devices.temperature_controller import TC720control
import time
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
os.environ["KIVY_NO_CONSOLELOG"] = "1"      # Turns off annoying logging

from Devices.camera_automation import CameraAutomation
from Devices.keithley2470control import Keithley2470Control, BufferElements
from utils import countdown_timer, dont_sleep

cam = CameraAutomation()
ktly = Keithley2470Control("USB0::0x05E6::0x2470::04625649::INSTR", "REAR")
ktly.initialize_instrument_settings(current_limit=100e-6, 
                                    current_range=100e-6, 
                                    auto_range=False, 
                                    NPLC=10, 
                                    averaging_state=False,
                                    auto_zero=True,
                                    source_measure_delay=0.1,
                                    source_readback=True)
TC = TC720control("com6")

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

def routine_low_temp_annealing_with_bias(temperature, 
                               temp_ramp_up_time_min,
                               temp_ramp_down_time_min,
                               annealing_time_min, 
                               target_voltage=-1000,
                               camera_save_path=None,
                               root_path=None,
                               idx=0):

    IV_data = pd.DataFrame()
    # ------- 1. Ramp Voltage to target_voltage -------
    print(f"\n1. Ramp Voltage to {target_voltage}V")
    ktly.ramp_voltage(target_voltage, step_size=10, step_delay=0.5)
    cam.save_image_png_typewrite(file_name=f"bias_{target_voltage}V_before_annealing",
                                 save_path=camera_save_path)

    time.sleep(10)
    print("\n1.1. Initial current measurements")
    for _ in range(3):
        ktly.write("*WAI")
        IV_data = update_IV_data(IV_data)
        print(f"{IV_data.iloc[-1].values}")
        time.sleep(10)

    # ------- 2. Ramp temperature to target_temperature -------
    print(f"\n2. Ramp temperature to {temperature}C for {temp_ramp_up_time_min} minutes")
    TC.set_temperature(temperature=temperature, 
                       wait_time = temp_ramp_up_time_min*60)
    cam.save_image_png_typewrite(file_name=f"bias_{target_voltage}V_start_annealing_{temperature}C")

    # ------- 3. Annealing Procedure -------
    start_time = time.time()
    print(f"\n3. Annealing for {annealing_time_min} minutes at {temperature}C")
    while time.time() - start_time < annealing_time_min * 60:
        print("--- Take measurement ---")
        IV_data = update_IV_data(IV_data)
        print(f"{IV_data.iloc[-1].values}")
        time.sleep(300) # 5 minutes
        dont_sleep()
    cam.save_image_png_typewrite(file_name=f"bias_{target_voltage}V_end_annealing_{temperature}C")
    print(f"\nTotal annealing time: {((time.time() - start_time)/60.0):.2f} minutes")


    # ------- 4. Ramp down temperature to room temperature 25C -------
    print("\n4. Ramp down temperature to room temperature 25C")
    TC.set_temperature(temperature=25, 
                       wait_time = temp_ramp_down_time_min*60)
    TC.write_output_enable('0') # Turn off TEC power

    # ------- 5. Take more current measurements at room temperature -------
    print("\n5. Take more current measurements at room temperature")
    for _ in range(3):
        ktly.write("*WAI")
        IV_data = update_IV_data(IV_data)
        print(f"{IV_data.iloc[-1].values}")
        time.sleep(10)
    cam.save_image_png_typewrite(file_name=f"bias_{target_voltage}V_after_annealing")
    cam.save_image_png_typewrite(file_name=f"bias_{target_voltage}V_25C_cycle_{idx+1}",
                                 save_path=root_path)

    return IV_data

def routine_low_temp_annealing_no_bias(temperature, 
                               temp_ramp_time_min, 
                               annealing_time_min, 
                               camera_save_path,
                               target_voltage=-1000):

    IV_data = pd.DataFrame()

    print(f"\n1. Ramp Voltage to {target_voltage}V")
    ktly.ramp_voltage(target_voltage, step_size=10, step_delay=0.5)
    cam.save_image_png_typewrite(file_name=f"bias_{target_voltage}V_before_annealing",
                                 save_path=camera_save_path)

    time.sleep(10)
    print("\n1.1. Initial current measurements")
    for _ in range(3):
        ktly.write("*WAI")
        IV_data = update_IV_data(IV_data)
        print(f"{IV_data.iloc[-1].values}")
        time.sleep(10)

    ktly.ramp_voltage(0, 10, 0.3) # Ramp voltage to 0V
    print(f"\n2. Ramp temperature to {temperature}C for {temp_ramp_time_min} minutes")
    TC.set_temperature(temperature=temperature, 
                       wait_time = temp_ramp_time_min*60)

    start_time = time.time()
    print(f"\n3. Annealing for {annealing_time_min} minutes at {temperature}C")
    countdown_timer(annealing_time_min*60)
    print(f"\nTotal annealing time: {((time.time() - start_time)/60.0):.2f} minutes")

    print("\n4. Going back to room temperature 25C")
    TC.set_temperature(temperature=25, 
                       wait_time = temp_ramp_time_min*60)
    TC.write_output_enable('0') # Turn off TEC power

    print("\n5. Take more current measurements at room temperature")
    ktly.ramp_voltage(target_voltage, step_size=10, step_delay=0.5)
    for _ in range(3):
        ktly.write("*WAI")
        IV_data = update_IV_data(IV_data)
        print(f"{IV_data.iloc[-1].values}")
        time.sleep(10)
    cam.save_image_png_typewrite(file_name=f"bias_{target_voltage}V_after_annealing")

    return IV_data


if __name__ == "__main__":
    for idx in range(11,30):
        print(f"Round {idx+1} starting")
        # ------- 1. Set up camera save path -------
        root_path = r"R:\Pockels_data\NEXT GEN POCKELS\LTAB_2025-06-17\D420144_day2"
        camera_save_path = Path(root_path) / f"round_{idx+1}"
        camera_save_path.mkdir(parents=True, exist_ok=True)

        IV_data = routine_low_temp_annealing_with_bias(
                                    temperature=75, 
                                    temp_ramp_up_time_min=2,
                                    temp_ramp_down_time_min=3,
                                    annealing_time_min=60, 
                                    target_voltage=-1000,
                                    camera_save_path=str(camera_save_path),
                                    root_path=str(root_path),
                                    idx=idx)
        
        print(f"Round {idx+1} IV data: \n{IV_data}")

        sensor_id = "D420144"
        save_path = camera_save_path / f"{sensor_id}_Annealing_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        IV_data.to_csv(save_path, index=True)
        IV_data.to_csv(f"{root_path}\IV_data_cycle_{idx+1}.csv", index=True)

    print("Annealing over. Voltage ramping to 0V")
    ktly.ramp_voltage(0, 10, 0.3)
    ktly.disable_output()
    ktly.disconnect()
    print("--- Keithley 2470 closed ---")

