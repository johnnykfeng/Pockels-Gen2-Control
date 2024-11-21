# %%
from keithley2470control import Keithley2470Control
import pandas as pd
import time
import matplotlib.pyplot as plt

# %% CREATE AN INSTANCE OF Keithley2470Control
address = "USB0::0x05E6::0x2470::04625649::INSTR"
ktly = Keithley2470Control(address, 
                           terminal="rear", 
                           verbose=True)

# %%
ktly.ramp_voltage(-60, step_size=5, step_delay=0.5)
print(ktly.query(":READ?"))


# %%
