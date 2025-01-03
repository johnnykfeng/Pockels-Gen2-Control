import os
import time
from ctypes import (
    c_uint32, c_int, c_double, c_bool,
    create_string_buffer, byref, cdll, c_char_p
)

#Loading DLL file.
lib = cdll.LoadLibrary(r"C:\Program Files\Thorlabs\upSERIES\Drivers\Instr\bin\TLUP_64.dll")

#Counting upSeries devices.
deviceCount = c_uint32()
lib.TLUP_findRsrc(0,byref(deviceCount))
if deviceCount.value > 0:
    print("Number of upSeries devices found: " + str(deviceCount.value))
else:
    print("No upSeries devices found.")
    exit()
print()

#Reading model name and serial number of the first connected upSeries device.
modelName = create_string_buffer(256)
serialNumber = create_string_buffer(256)
lib.TLUP_getRsrcInfo(0, 0, modelName, serialNumber, 0, 0)
print("Connecting to this device:")
print("Model name: ", (modelName.value).decode(), ", Serial number: ", (serialNumber.value).decode())
print()

#Initializing the first connected upSeries device.
upName = create_string_buffer(256)
lib.TLUP_getRsrcName(0, 0, upName)
upHandle=c_int(0)
res=lib.TLUP_init(upName.value, 0, 0, byref(upHandle))

#If the device is an upLED, this section is executed.
if (modelName.value).decode() == "upLED":

    #Enables the use of LEDs without EEPROM (non-Thorlabs or unmounted LEDs).
    print(lib.TLUP_setLedUseNonThorlabsLed(upHandle, 1))
    
    #Make sure the LED is switched off (0 = off, 1 = on).
    lib.TLUP_switchLedOutput(upHandle,0)

    #Get information about the connected LED.
    #!!! This only works for Thorlabs' Mounted LEDs with an EEPROM chip on the PCB.
    #!!! Third-party or unmounted LEDs do not have such a chip.
    currentSetpoint = c_double()
    LEDName = create_string_buffer(256)
    LEDSerialNumber = create_string_buffer(256)
    LEDCurrentLimit = c_double()
    LEDForwardVoltage = c_double()
    LEDWavelength = c_double(0)
    
    lib.TLUP_getLedInfo(upHandle, LEDName, LEDSerialNumber, byref(LEDCurrentLimit),
                        byref(LEDForwardVoltage), byref(LEDWavelength))

    #if section: LED with EEPROM chip is connected
    if LEDWavelength.value != 0:
        print("EEPROM on LED detected.")
        print("Connected LED:", (LEDName.value).decode(), ", serial number:", (LEDSerialNumber.value).decode(),", wavelength [nm]:",LEDWavelength.value)
        print("max LED current [A]:", LEDCurrentLimit.value, ", max forward voltage [V]:", LEDForwardVoltage.value)
        print()
        #Set the current setpoint in Ampere to 10% of the current limit of this LED.
        currentSetpoint = c_double((0.1) * LEDCurrentLimit.value)
        lib.TLUP_setLedCurrentSetpoint(upHandle,currentSetpoint)
        time.sleep(1)
        lib.TLUP_getLedCurrentSetpoint(upHandle,0, byref(currentSetpoint))
        print("LED current set to [A]:", currentSetpoint.value)
        print()

    #else section: LED without EEPROM chip is connected
    else:
        print("No EEPROM on LED detected.")
        #Ask user to enter LED current setpoint and check if input is correct.
        try:
            currentSetpoint = c_double(0.001 * float(input("Please enter LED current setpoint in mA: ")))
        except ValueError:  # Catches invalid number format
            print("Error: Incorrect input. Please do not use letters, only use numbers.")
            print("Code will be stopped.")
            exit()
        lib.TLUP_setLedCurrentSetpoint(upHandle, currentSetpoint)
        print("LED current set to", currentSetpoint.value*1000, "mA.")            

    
    #Switch the LED on, wait for 2 sec, then switch it off again.
    lib.TLUP_switchLedOutput(upHandle,1)
    print("Switch LED on.")
    print("Wait...")
    time.sleep(2)
    lib.TLUP_switchLedOutput(upHandle,0)
    print("Switch LED off.")
    
#If the device is an upTEMP, this section is executed.
elif (modelName.value).decode() == "upTEMP":
    print("upTEMP device detected.")

#If the device is neither an upLED nor an upTEMP, this section is executed.
else:
    print("upSeries device type is not yet supported by this example.")
    
#Connection to the upSeries device is closed.
lib.TLUP_close(upHandle)