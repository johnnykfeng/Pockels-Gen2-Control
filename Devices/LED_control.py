from loguru import logger
import time
from ctypes import (
    c_uint32,
    c_int,
    c_double,
    create_string_buffer,
    byref,
    cdll,
)


class LEDController: 
    def __init__(self, verbose=False):
        logger.info("Initializing LED Controller")
        self.lib = cdll.LoadLibrary(
            r"C:\Program Files\Thorlabs\upSERIES\Drivers\Instr\bin\TLUP_64.dll"
        )

        # Counting upSeries devices.
        deviceCount = c_uint32()
        self.lib.TLUP_findRsrc(0, byref(deviceCount))
        if deviceCount.value > 0:
            logger.info(f"Found {deviceCount.value} upSeries devices")
        else:
            logger.error("No upSeries devices found")
            exit()
        print()

        # Reading model name and serial number of the first connected upSeries device.
        modelName = create_string_buffer(256)
        serialNumber = create_string_buffer(256)
        self.lib.TLUP_getRsrcInfo(0, 0, modelName, serialNumber, 0, 0)
        print("Connecting to this device:")
        print(
            "Model name: ",
            (modelName.value).decode(),
            ", Serial number: ",
            (serialNumber.value).decode(),
        )
        print()

        # Initializing the first connected upSeries device.
        upName = create_string_buffer(256)
        self.lib.TLUP_getRsrcName(0, 0, upName)
        self.handle = c_int(0)
        self.res = self.lib.TLUP_init(upName.value, 0, 0, byref(self.handle))

        self.current_setpoint = c_double()
        self.led_name = create_string_buffer(256)
        self.led_serial = create_string_buffer(256)
        self.current_limit = c_double()
        self.forward_voltage = c_double()
        self.wavelength = c_double()

        # Get LED info
        self.lib.TLUP_getLedInfo(
            self.handle,
            self.led_name,
            self.led_serial,
            byref(self.current_limit),
            byref(self.forward_voltage),
            byref(self.wavelength),
        )

        self.verbose = verbose

        logger.debug(
            f"Connected to device: {modelName.value.decode()} (SN: {serialNumber.value.decode()})"
        )

        logger.info("LED Controller initialization complete")

    def get_current_setpoint(self):
        """Get current LED current setpoint in mA"""
        logger.debug("Getting current setpoint")
        current = c_double()
        self.lib.TLUP_getLedCurrentSetpoint(self.handle, 0, byref(current))
        value = current.value * 1000
        logger.debug(f"Current setpoint: {value:.1f} mA")
        return value

    def set_current(self, current_ma):
        """Set LED current in mA"""
        logger.debug(f"Setting current to {current_ma} mA")
        try:
            current_a = current_ma * 0.001
            self.current_setpoint = c_double(current_a)
            self.lib.TLUP_setLedCurrentSetpoint(self.handle, self.current_setpoint)
            # Verify current was set
            self.lib.TLUP_getLedCurrentSetpoint(
                self.handle, 0, byref(self.current_setpoint)
            )
            if self.verbose:
                print(f"LED current set to {self.current_setpoint.value * 1000:.1f} mA")
            logger.info(f"Current set to {self.current_setpoint.value * 1000:.1f} mA")
        except Exception as e:
            logger.error(f"Error setting current: {e}")
            print(f"Error setting current: {e}")

    def turn_on(self):
        """Turn LED on"""
        logger.info("Turning LED on")
        self.lib.TLUP_switchLedOutput(self.handle, 1)
        if self.verbose:
            print("LED turned on")

    def turn_off(self):
        """Turn LED off"""
        logger.info("Turning LED off")
        self.lib.TLUP_switchLedOutput(self.handle, 0)
        if self.verbose:
            print("LED turned off")

    def print_parameters(self):
        """Print LED parameters"""
        logger.debug("Printing LED parameters")
        print("\nLED Parameters:")
        if self.wavelength.value != 0:
            print("EEPROM detected")
            print(f"LED Name: {self.led_name.value.decode()}")
            print(f"Serial Number: {self.led_serial.value.decode()}")
            print(f"Wavelength: {self.wavelength.value} nm")
            print(f"Current Limit: {self.current_limit.value * 1000:.1f} mA")
            print(f"Forward Voltage: {self.forward_voltage.value:.1f} V")
        else:
            print("No EEPROM detected")
        print(f"Current Setpoint: {self.current_setpoint.value * 1000:.1f} mA")


if __name__ == "__main__":
    led = LEDController()
    led.print_parameters()
    for i in range(100, 800, 100):
        print(f"Last current setpoint: {led.get_current_setpoint():.3f} mA")
        led.set_current(i)  # Set to 50mA
        led.turn_on()
        time.sleep(1)
        # led.turn_off()
        # time.sleep(1)
