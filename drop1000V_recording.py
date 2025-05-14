from Devices.temperature_controller import TC720control
import It_control as it
from time import sleep
from datetime import datetime
import os
os.environ["KIVY_NO_CONSOLELOG"] = "1"      # Turns off annoying logging

from Devices.camera_automation import CameraAutomation
from Devices.keithley2470control import Keithley2470Control

cam = CameraAutomation()
ktly = Keithley2470Control("USB0::0x05E6::0x2470::04625649::INSTR", "REAR")
ktly.initialize_instrument_settings(current_limit=10e-6, 
                                    current_range=10e-6, 
                                    auto_range=False, 
                                    NPLC=1, 
                                    averaging_state=False)
TC = TC720control("com6")

save_folder = r"C:\Program Files\Xeneth\Data\Drop1000V_T-dependent_study\M78439-A0_AnodeRemade"
def routine_drop_voltage_record(temperature, target_voltage=-1000):

    file_name = f"Drop1000V_T{temperature}C.xvi"
    file_path = os.path.join(save_folder, file_name)
    print(f"1. Type Recording File Path: {file_path}")
    cam.type_recording_file_path(file_path)
    cam.start_capturing_button_click()
    cam.record_button_click()
    print("2. Click Record Button")
    sleep(0.25)

    ktly.disable_output()
    print("3. Output OFF")
    sleep(1.0)

    ktly.enable_output()
    print("4. Output ON")
    sleep(1.0)

    ktly.set_voltage(0)
    print("5. Voltage Set to 0")
    sleep(1.0)

    ktly.set_voltage(target_voltage)
    print(f"6. Voltage Set to {target_voltage}")
    sleep(5.0)


target_voltage = -1000
sleep(0.5)
ktly.enable_output()
print(f"0. Ramp Voltage to {target_voltage}V")
ktly.ramp_voltage(target_voltage, 10, 0.5)
print("0.1 Done ramping voltage")
sleep(5)

for temperature in [10, 20, 30, 40, 50, 60, 70, 80]:
    TC.set_temperature(temperature=temperature, wait_time=180)
    sleep(1.0)
    routine_drop_voltage_record(temperature=temperature, 
                                target_voltage=target_voltage)

print("Recording over")
ktly.ramp_voltage(0, 10, 0.3)
ktly.disable_output()
ktly.disconnect()
print("--- Keithley 2470 closed ---")

print(TC.set_temperature(temperature=25, wait_time=60))

