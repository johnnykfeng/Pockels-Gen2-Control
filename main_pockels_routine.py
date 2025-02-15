from Devices.thorlabs_rotation_mount import RotationMount
from Devices.camera_automation import CameraAutomation
from Devices.LED_control import LEDController
from Devices.keithley2470control import Keithley2470Control
from utils import countdown_timer

import time
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

rotation_mount = RotationMount("27267316")
camera = CameraAutomation()
# save_path = r"C:\Users\10552\Downloads\pockels_run"
sensor_id = "D366359"
date = time.strftime("%Y-%m-%d")
version = "A"
save_path = f"C:\\Code\\Pockels-Gen2-Control\\CAMERA_IMAGES\\{sensor_id}_{date}_{version}"
led = LEDController()
KEITHLEY_2470_ADDRESS = "USB0::0x05E6::0x2470::04625649::INSTR"
keithley = Keithley2470Control(KEITHLEY_2470_ADDRESS, terminal="rear")

if __name__ == "__main__":
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    # Define the positions
    cross = 130
    parallel = 40
    rotation_mount.open_device()
    rotation_mount.home_device()
    rotation_mount.setup_conversion()

    # led.set_current(100)
    led.set_current(200)
    led.turn_off()

    rotation_mount.move_to_position(parallel)
    camera.save_image_png(file_name="calib_parallel_off.png", save_path=save_path)
    countdown_timer(3)

    led.turn_on()
    camera.save_image_png(file_name="calib_parallel_on.png", save_path=save_path)
    countdown_timer(3)

    rotation_mount.move_to_position(cross)
    camera.save_image_png(file_name="calib_cross_on.png", save_path=save_path)
    countdown_timer(3)

    # == START MEASUREMENT WITH HIGH VOLTAGE BIAS == #
    keithley.initialize_instrument_settings(
        current_limit=10e-6,
        current_range=10e-6,
        auto_range=False,
        NPLC=1,
        averaging_state=True,
        averaging_count=10
    )

    current_readings = []
    voltages = np.arange(0, -1101, -100)
    for voltage in voltages:
        keithley.ramp_voltage(voltage, step_size=10, step_delay=0.5)
        time.sleep(2)
        current_readings.append(keithley.query(":READ?"))
        camera.save_image_png(file_name=f"bias_{abs(voltage)}V_xray_0mA.png", 
                              save_path=None)
        countdown_timer(3)
    
    keithley.ramp_voltage(0, step_size=50, step_delay=1) # ramp down to 0V
    keithley.disable_output()


    print("Measurement complete")
    # rotation_mount.home_device()
    rotation_mount.close_device()
    led.turn_off()
    keithley.disconnect()


    print(f"{current_readings = }")
    df = pd.DataFrame({"Voltage": voltages, "Current": current_readings})
    df.to_csv(f"{save_path}\pockels_current_readings.csv", index=False)

    # plt.plot(voltages, current_readings)
    # plt.xlabel("Voltage (V)")
    # plt.ylabel("Current (A)")
    # plt.title("Current vs Voltage")
    # plt.savefig(f"{save_path}\pockels_current_vs_voltage.png")
    # plt.show()

