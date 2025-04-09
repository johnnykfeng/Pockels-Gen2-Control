from pymeasure.instruments.keithley.keithley2470 import Keithley2470
from pymeasure.adapters import VISAAdapter
from Devices.thorlabs_rotation_mount import RotationMount
from Devices.camera_automation import CameraAutomation
from Devices.LED_control import LEDController
from utils import countdown_timer
import os

class PockelsProcedure():
        
    def __init__(self):
        super().__init__()
        adapter = VISAAdapter("USB0::0x05E6::0x2470::04625649::INSTR")
        self.keithley = Keithley2470(adapter)
        self.rotation_mount = RotationMount("27267316")
        self.led = LEDController()
        self.camera = CameraAutomation()

    def startup(self, sensor_id, temperature, cross_angle, parallel_angle, led_current, save_path):
        # Keithley-specific startup code
        self.keithley.reset()
        self.keithley.use_rear_terminals()
        self.keithley.apply_voltage(compliance_current=105e-6)
        self.keithley.write(":CURRent:AZERo OFF")
        self.keithley.measure_current(nplc=0.01)
        self.keithley.write(":OUTPut:INTerlock:STATe OFF")
        self.keithley.stop_buffer()
        self.keithley.disable_buffer()

        # Rotation mount-specific startup code
        self.rotation_mount.open_device()
        self.rotation_mount.home_device()
        self.rotation_mount.setup_conversion()
        self.rotation_mount.move_to_position(parallel_angle)

        # LED-specific startup code
        self.led.set_current(led_current)
        self.led.turn_off()

        save_path = os.path.join(save_path, f"CAMERA_IMAGES")
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        self.rotation_mount.move_to_position(parallel_angle)
        self.camera.save_image_png(file_name=f"{sensor_id}_{temperature}C_calib_parallel_off.png", save_path=save_path)
        countdown_timer(3)

        self.led.turn_on()
        self.camera.save_image_png(file_name=f"{sensor_id}_{temperature}C_calib_parallel_on.png", save_path=save_path)
        countdown_timer(3)

        self.rotation_mount.move_to_position(cross_angle)
        self.camera.save_image_png(file_name=f"{sensor_id}_{temperature}C_calib_cross_on.png", save_path=save_path)
        countdown_timer(3)

    def execute(self, voltages, current_range, nplc, data_points, save_path, temperature, timestamp, sensor_id):

        save_path = os.path.join(save_path, f"CAMERA_IMAGES")
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        data = []
        self.keithley.current_nplc = nplc
        self.keithley.current_range = current_range
        self.keithley.beep(392, 1)
        self.keithley.enable_source()

        ### Perform Ramp Captures ###
        for voltage in voltages:
            print("Setting voltage to: " + str(voltage))

            load_ramp_trigger_model(self.keithley, data_points)

            self.keithley.config_buffer(points=data_points)

            self.keithley.source_voltage = voltage

            self.camera.save_image_png(file_name=f"{sensor_id}_{temperature}C_{abs(voltage)}V_{timestamp}.png", save_path=save_path)
            countdown_timer(3)

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

            for idx, current in enumerate(currents):
                line = {
                    'Buffer Index': idx,
                    'Voltage (V)': source_voltages[idx],
                    'Current (A)': current,
                    'Relative Time (s)': relative_timestamps[idx],
                    'Absolute Time': data_timestamps[idx]
                }
                data.append(line)

        ### Perform Shutoff Capture ###
        load_shutoff_trigger_model(self.keithley, data_points)
        self.keithley.config_buffer(points=data_points)

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

        for idx, current in enumerate(currents):
            line = {
                'Buffer Index': idx,
                'Voltage (V)': source_voltages[idx],
                'Current (A)': current,
                'Relative Time (s)': relative_timestamps[idx],
                'Absolute Time': data_timestamps[idx]
            }
            data.append(line)

        return data


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
    
