# %% IMPORTS
from keithley2470control import Keithley2470Control
from camera_control import CameraControl
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt

# %% CREATE AN INSTANCE OF Keithley2470Control
address = "USB0::0x05E6::0x2470::04625649::INSTR"
ktly = Keithley2470Control(address, 
                           terminal="rear", 
                           verbose=True)

ktly.initialize_instrument_settings()
# %% CREATE AN INSTANCE OF CameraControl
url = "cam://0"
cam = CameraControl(url)


# %%
current_readings = []
for voltage in np.arange(0, -1001, -100):
    print(f"Setting voltage to {voltage}")
    ktly.ramp_voltage(voltage, step_size=10, step_delay=0.5)
    cam.start_capture()
    frame = cam.get_frame()
    cam.save_as_bin(frame, f"CAMERA_IMAGES\\test_image_{voltage}V.bin")
    cam.stop_capture()
    current_readings.append(ktly.query(":READ?"))
    
print("Measurement complete")
print(f"{current_readings = }")
cam.close_camera()
ktly.disable_output()
ktly.disconnect()

# %%
