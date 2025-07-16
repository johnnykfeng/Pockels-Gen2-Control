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
from pathlib import Path


rotation_mount = RotationMount("27267316")
camera = CameraAutomation()
stabilization_time = 5
# save_path = r"C:\Users\10552\Downloads\pockels_run"
# wafer_id = "D410886"
sensor_id = "Training"
datetime = time.strftime("%Y-%m-%d_%H-%M-%S")
trial = "A"

root_folder = Path(r"R:\Pockels_data\NEXT GEN POCKELS\Training\trial_2")
sub_folder = Path(f"{sensor_id}_{datetime}")

save_path = root_folder / sub_folder
led = LEDController()
KEITHLEY_2470_ADDRESS = "USB0::0x05E6::0x2470::04625649::INSTR"
keithley = Keithley2470Control(KEITHLEY_2470_ADDRESS, terminal="rear")

if __name__ == "__main__":
    if not os.path.exists(str(save_path)):
        print(f"Creating directory: {save_path}")
        os.makedirs(str(save_path))
    # Define the positions
    cross = 45
    parallel = 135
    rotation_mount.open_device()
    # rotation_mount.home_device()
    rotation_mount.setup_conversion()

    # led.set_current(100)
    led.set_current(500)
    led.turn_off()

    rotation_mount.move_to_position(parallel)
    print("Waiting for 5 seconds for parallel position")
    time.sleep(5)
    camera.save_image_png_typewrite(file_name="calib_parallel_off.png", 
                                    save_path=str(save_path))
    countdown_timer(3)

    led.turn_on()
    camera.save_image_png_typewrite(file_name="calib_parallel_on.png")
    countdown_timer(3)

    rotation_mount.move_to_position(cross)
    camera.save_image_png_typewrite(file_name="calib_cross_on.png")
    countdown_timer(3)

    # == START MEASUREMENT WITH HIGH VOLTAGE BIAS == #
    keithley.initialize_instrument_settings(
        current_limit=100e-6,
        current_range=100e-6,
        auto_range=False,
        NPLC=1,
        averaging_state=True,
        averaging_count=10
    )

    current_readings = []
    voltages = np.arange(-100, -1101, -100)
    for voltage in voltages:
        print(f"Start ramp to {abs(voltage)}V bias")
        keithley.ramp_voltage(voltage, step_size=10, step_delay=0.5)
        print("Waiting for 10 seconds for High Voltage to stabilize")
        countdown_timer(stabilization_time)
        current_readings.append(keithley.query(":READ?"))
        camera.save_image_png_typewrite(file_name=f"cross_{abs(voltage)}V_xray_0mA.png", 
                              save_path=None)
        # rotation_mount.move_to_position(parallel)
        # camera.save_image_png_typewrite(file_name=f"parallel_{abs(voltage)}V_xray_0mA.png", 
        #                       save_path=None)
        # rotation_mount.move_to_position(cross)
        countdown_timer(3)
    
    keithley.ramp_voltage(0, step_size=50, step_delay=1) # ramp down to 0V
    keithley.disable_output()


    print("Measurement complete")
    # rotation_mount.home_device()
    rotation_mount.close_device()
    led.turn_off()
    keithley.disconnect()

    current_readings_float = [float(reading) for reading in current_readings]
    current_readings_float = np.array(current_readings_float)
    print(f"{current_readings_float = }")


    IV_save_path = os.path.join(save_path, "IV_data")
    if not os.path.exists(IV_save_path):
        os.makedirs(IV_save_path)
    df = pd.DataFrame({"Voltage": voltages, "Current": current_readings_float})
    df.to_csv(f"{IV_save_path}\pockels_current_readings.csv", index=False)


    # Plot the IV curve
    fig, ax = plt.subplots()
    ax.plot(abs(voltages), abs(current_readings_float), '-o')
    ax.set_xlabel("abs(Voltage) (V)")
    ax.set_ylabel("abs(Current) (A)")
    ax.set_title("IV Curve")
    ax.grid(True)
    fig.savefig(f"{IV_save_path}\IV_plot.png")

    fig2, ax2 = plt.subplots()
    ax2.plot(abs(voltages), abs(current_readings_float), '-o')
    ax2.set_xlabel("abs(Voltage) (V)")
    ax2.set_ylabel("abs(Current) (A)")
    ax2.set_title("IV Curve")
    ax2.grid(True)
    ax2.set_yscale('log')
    fig2.savefig(f"{IV_save_path}\IV_plot_log.png")

    fig.show()
    fig2.show()

