# %%
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# %%
temp_calib = pd.read_csv(r'C:\Users\10552\OneDrive - Redlen Technologies\Code\Pockels-Gen2-Control\Data_Processing\temp_calib.csv')

def calibrate_temp(temp_1: float):
    """
    Convert temperature from 1 to 2 using the calibration data.
    """
    calibrated_temp = temp_calib['temp_2'][temp_calib['temp_1'] == temp_1].values[0]
    return calibrated_temp


data_path = r"C:\Users\10552\OneDrive - Redlen Technologies\Code\Pockels-Gen2-Control\TEST_DATA\RampAllTemp"
# %%
all_dfs = []
for temperature in range(10, 71, 10):

    csv_files = [f for f in os.listdir(data_path) if f.startswith(f"{temperature}C") and f.endswith(".csv")]
    # Rearrange the file with -1000V in the filename to be last in the list
    csv_files.sort(key=lambda x: '-1000.0V' in x)
    # print(csv_files)
    # Create a list to store dataframes
    dfs = []

    for file in csv_files:
        # print(file)
        voltage = file.split("_")[1].split(".")[0]
        if voltage != "shutoff":
            df = pd.read_csv(os.path.join(data_path, file))
            df["Voltage_str"] = voltage
            df["Temperature"] = temperature
            calibrated_temp = calibrate_temp(temperature)
            df["Temperature_calibrated"] = calibrated_temp
            dfs.append(df)

    # Concatenate all dataframes and reset index
    combined_df = pd.concat(dfs, ignore_index=True)
    all_dfs.append(combined_df)

    # Plot time vs Current of combined_df
    plt.figure(figsize=(10, 6))
    for voltage in combined_df['Voltage_str'].unique():
        df_subset = combined_df[combined_df['Voltage_str'] == voltage]
        df_subset = df_subset[(df_subset['Time (s)'] >= 0) & (df_subset['Time (s)'] <= 0.5)]
        plt.plot(df_subset['Time (s)'], df_subset['Current (A)'], marker='.', linestyle='-', label=voltage)
    plt.xlabel('Time')
    plt.ylabel('Current (A)')
    # plt.yscale('log')  # Set y-axis to logarithmic scale
    plt.title(f'Current vs Time at {calibrated_temp}C')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'I-T_{temperature}C.png')
    plt.show()

combined_all_dfs = pd.concat(all_dfs, ignore_index=True)

combined_all_dfs.to_csv('combined_all_dfs.csv', index=True)

# %%
def invert_current(current: list):
    """
    Invert the current. Set the negative current values after inversion to 1e-10.
    """
    current = np.array(current)
    current = -1.0*current
    current[current < 0] = 1e-10
    return current

def log_current(current: list):
    """
    Logarithmically scale the current. Bypass the negative current values.
    """
    current = np.array(current)
    log_current = np.zeros_like(current)
    mask = current >= 0
    log_current[mask] = np.log10(current[mask])
    return log_current

# %% Aggregate stabilized IV data

big_df = pd.read_csv(r'C:\Users\10552\OneDrive - Redlen Technologies\Code\Pockels-Gen2-Control\Data_Processing\combined_all_dfs.csv')
df_stable = big_df[big_df['Time (s)'] > 3.0]
df_stable['inverted_current'] = df_stable['Current (A)']*-1
df_stable['abs_voltage'] = df_stable['Voltage (V)'].abs()

# Plot the voltage vs current of df_subset
temperature_list = big_df['Temperature_calibrated'].unique()
voltage_list = big_df['Voltage_str'].unique()
voltage_list = [float(voltage) for voltage in voltage_list]
abs_voltage_list = [abs(voltage) for voltage in voltage_list]

new_df = pd.DataFrame()

for temperature in temperature_list:
    average_current_list = []
    for voltage in voltage_list:
        df_subset = big_df[(big_df['Temperature_calibrated'] == temperature)\
            & (big_df['Voltage_str'] == voltage)\
                & (big_df['Time (s)'] > 3.0)]
        average_current = df_subset['Current (A)'].mean()
        average_current_list.append(average_current)

    inverted_current_list = invert_current(average_current_list)
    # log_current_list = log_current(inverted_current_list)
    new_df = pd.concat([new_df, pd.DataFrame({'Temperature_calibrated': temperature, 'abs_voltage': abs_voltage_list, 'average_current': average_current_list, 'inverted_current': inverted_current_list})], ignore_index=True)
            
new_df.to_csv('Stabilized_IV_data.csv', index=False)


# %% Plot from new_df

new_df = pd.read_csv(r'C:\Users\10552\OneDrive - Redlen Technologies\Code\Pockels-Gen2-Control\Data_Processing\Stabilized_IV_data.csv')

temperature_list = new_df['Temperature_calibrated'].unique()
colors = plt.cm.jet(np.linspace(0, 1, len(temperature_list)))

plt.figure(figsize=(10, 6))
for i, temperature in enumerate(temperature_list):
    df_subset = new_df[new_df['Temperature_calibrated'] == temperature]
    plt.plot(df_subset['abs_voltage'], df_subset['inverted_current'], marker='.', linestyle='-', color=colors[i], label=f"{temperature}C")

# plt.yscale('log')
plt.xlabel('abs Voltage (V)')
plt.ylabel('abs Current (A)')
# plt.yscale('log')
plt.title('abs Current vs abs Voltage')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# %% Current vs Temperature per Voltage

new_df = pd.read_csv(r'C:\Users\10552\OneDrive - Redlen Technologies\Code\Pockels-Gen2-Control\Data_Processing\Stabilized_IV_data.csv')

voltage_array = np.array(new_df['abs_voltage'].unique())
colors = plt.cm.viridis(np.linspace(0, 1, len(voltage_array)))
# colors = plt.cm.viridis(np.linspace(1, 0, len(voltage_array))) # Reverse the color map

# Plot current vs temperature for each voltage_str
plt.figure(figsize=(10, 6))
for i, voltage in enumerate(voltage_array):
    df_subset = new_df[new_df['abs_voltage'] == voltage]
    temperature_array = np.array(df_subset['Temperature']) + 273.15 # Convert to Kelvin
    inverted_temperature = 1.0/temperature_array
    plt.plot(inverted_temperature, df_subset['inverted_current'], marker='.', linestyle='-', color=colors[i], label=f"{voltage}V")

plt.xlabel('1/Temperature (1/K)')
plt.ylabel('abs Current (A)')
plt.yscale('log')
plt.title('Current vs Temperature per Voltage')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


# %%
from scipy.optimize import curve_fit

new_df = pd.read_csv(r'C:\Users\10552\OneDrive - Redlen Technologies\Code\Pockels-Gen2-Control\Data_Processing\Stabilized_IV_data.csv')

def arrhenius_fit(temperature: np.array, Ea: float, offset: float):
    """
    Fit the current vs temperature data to the Arrhenius equation.
    """
    # Convert temperature to Kelvin
    k = 8.617333262145e-5 # eV/K
    temperature = np.array(temperature) + 273.15
    current_array = np.exp(Ea/(k*temperature)) + offset
    return current_array

def arrhenius_fit_log(inverted_temperature: np.array, Ea: float, offset: float):
    """
    Fit the current vs temperature data to the Arrhenius equation.
    """
    # Convert temperature to Kelvin
    k = 8.617333262145e-5 # eV/K
    log_current = -(Ea/k)*(inverted_temperature) + offset
    return log_current

def r_square(y_data: np.array, y_fit: np.array):
    """
    Calculate the R-square value.
    """
    ss_res = np.sum((y_data - y_fit) ** 2)
    ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
    return 1 - (ss_res / ss_tot)

voltage_array = np.array(new_df['abs_voltage'].unique())
calibrated_temperature_array = np.array(new_df['Temperature_calibrated'].unique())
print(f"Calibrated temperature array: {calibrated_temperature_array}")

# activation_energies = pd.DataFrame(columns=['Voltage', 'Ea_fit', 'offset_fit', 'r_square'])
activation_energies = pd.DataFrame()
colors = plt.cm.tab10(np.linspace(0, 1, len(voltage_array)))

plt.figure(figsize=(10, 6))
for i, voltage in enumerate(voltage_array):
    df_subset = new_df[(new_df['abs_voltage'] == voltage)\
        & (new_df['Temperature_calibrated'] > 20)\
            ]
    temperature_array = np.array(df_subset['Temperature_calibrated']) + 273.15 # Convert to Kelvin
    inverted_temperature = 1.0/temperature_array
    current_array = np.array(df_subset['inverted_current'])
    log_current_array = np.log(current_array)
    
    # Fit the data to the Arrhenius equation
    popt, pcov = curve_fit(arrhenius_fit_log, inverted_temperature, log_current_array, p0=[1.0, 15])
    Ea = np.round(popt[0], 3)
    offset = np.round(popt[1], 2)
    r_square_value = r_square(log_current_array, arrhenius_fit_log(inverted_temperature, Ea, offset))
    print(f"Ea for {voltage}V: {Ea:.3f} eV, offset: {offset:.2f}, R-square: {r_square_value:.3f}")
    data_row = pd.DataFrame({'Voltage': [voltage], 'Ea_fit': [Ea], 'offset_fit': [offset], 'r_square': [r_square_value]})
    activation_energies = pd.concat([activation_energies, data_row], ignore_index=True, axis=0)

    plt.plot(inverted_temperature, log_current_array, marker='.',  label=f"{voltage}V",
             color=colors[i]
             )
    plt.plot(inverted_temperature, arrhenius_fit_log(inverted_temperature, Ea, offset), linestyle='--', 
             color=colors[i]
             )

activation_energies.to_csv('Activation_energy_by_voltage_above_20C.csv', index=False)

# plt.yscale('log')
plt.xlabel('1/Temperature (1/K)')
plt.ylabel('ln(Current)')
plt.title('ln(Current) vs 1/Temperature above 20C')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()



# %%
