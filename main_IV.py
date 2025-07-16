# %% IMPORTS
from Devices.keithley2470control import Keithley2470Control
# from camera_control import CameraControl
import numpy as np
import pandas as pd
import time
import matplotlib.pyplot as plt
from utils import voltages_log_space

# %% CREATE AN INSTANCE OF Keithley2470Control
address = "USB0::0x05E6::0x2470::04625649::INSTR"
ktly = Keithley2470Control(address, 
                           terminal="rear", 
                           verbose=False)

ktly.initialize_instrument_settings(
    current_limit=1e-4,
    current_range=1e-4,
    auto_range=False,
    NPLC=1,
    averaging_state=True,
    averaging_count=10
)
# CREATE AN INSTANCE OF CameraControl
# url = "cam://0"
# cam = CameraControl(url)

# %%
# voltages_1 = np.arange(0, -801, -100)
# voltages_2 = np.arange(-900, -1101, -20)
# voltage_neg = np.concatenate([voltages_1, voltages_2])
# voltage_pos = -voltage_neg
# voltages = np.concatenate([voltage_neg, voltage_pos])
voltages = voltages_log_space(min_voltage=-1000, max_voltage=1000, data_points=100)
print(f"{voltages = }")
# %% 
current_readings = []
for i, voltage in enumerate(voltages):
    print(f"Setting voltage to {i}/{len(voltages)}: {voltage}")
    if abs(voltage) > 200: # use ramping for high voltages
        ktly.ramp_voltage(voltage, step_size=10, step_delay=0.5)
        time.sleep(2)
    else:
        ktly.set_voltage(voltage, range="auto")
        time.sleep(2)

    current_readings.append(ktly.query(":READ?"))
    
ktly.ramp_voltage(0, step_size=50, step_delay=0.5)
ktly.disable_output()
print("Measurement complete")
print(f"{current_readings = }")

# %% DATA PROCESSING
print("DATA PROCESSING")
current_readings = [float(i) for i in current_readings]
abs_current_readings = abs(np.array(current_readings))

sensor_id = "D448038"

# micrometer_position, compression = 6.5, 0
# micrometer_position, compression = 6.0, 0.5
micrometer_position, compression = 5.5, 1.0
# micrometer_position, compression = 5.0, 1.5
# contact_type = "ConductiveRubber"
contact_type = "PariposerSheet"

df = pd.DataFrame({
    "Sensor_ID": sensor_id,
    "Contact_Type": contact_type,
    # "Micrometer_Position (mm)": micrometer_position,
    # "Compression (mm)": compression,
    "Voltage (V)": voltages,
    "Current (A)": current_readings,
    "Absolute Current (A)": abs_current_readings
})

print(df.head(1))

# %%
print("PLOTTING")
# print(f"BNL Sensor {sensor_id}, compression {compression} mm, {contact_type} contact")
fig, ax = plt.subplots()
log_scale = True
if log_scale:
    ax.set_yscale('log')
    ax.plot(voltages, abs_current_readings, '-o')
else:
    ax.plot(voltages, abs_current_readings, 'o')
ax.set_xlabel("Voltage (V)")
ax.set_ylabel("Current (A)")
ax.set_title(f"Pockels Ref. {sensor_id}, compression {compression} mm, {contact_type}")
ax.grid(True, which='minor', linestyle='--', linewidth=0.5)
ax.grid(True, which='major', linestyle='-', linewidth=1)
plt.show()

# %%
print("SAVING DATA")
folder = "TEST_DATA\\Pockels_reference"
# df.to_csv(f"{folder}\\{sensor_id}_{contact_type}_{compression}mm.csv", index=False)
df.to_csv(f"{folder}\\{sensor_id}_CE_study.csv", index=False)

# %% CLOSE THE CAMERA AND DISCONNECT FROM THE INSTRUMENT
ktly.disable_output()
ktly.disconnect()
# cam.close_camera()
# %%