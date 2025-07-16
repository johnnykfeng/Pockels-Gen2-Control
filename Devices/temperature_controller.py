import time
import serial
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import countdown_timer

class TC720control:

    print("TC720control class initialized version 0.0.1")

    def __init__(self, COMport):
        self.ser = serial.Serial(COMport, 230400, timeout=1)
        
        # Command lists
        self.woec   =   ['*','3','0','0','0','0','0','0','0','\r']  # Write Output Enable Command
        self.roec   =   ['*','6','4','0','0','0','0','0','0','\r']  # Read Output Enable Command
        self.rt1c   =   ['*','0','1','0','0','0','0','0','0','\r']  # Read Temperature 1 Command
        self.rt2c   =   ['*','0','4','0','0','0','0','0','0','\r']  # Read Temperature 2 Command
        self.wspc   =   ['*','1','c','0','0','0','0','0','0','\r']  # Write Set Point Command
        self.rspc   =   ['*','5','0','0','0','0','0','0','0','\r']  # Read Set Point Command
        self.wpbc   =   ['*','1','d','0','0','0','0','0','0','\r']  # Write Proportional Bandwidth Command
        self.wigc   =   ['*','1','e','0','0','0','0','0','0','\r']  # Write Integral Gain Command
        self.wdgc   =   ['*','1','f','0','0','0','0','0','0','\r']  # Write Derivative Gain Command
        self.whmc   =   ['*','3','4','0','0','0','0','0','0','\r']  # Write Heat Multiplier Command
        self.wcmc   =   ['*','3','3','0','0','0','0','0','0','\r']  # Write Cool Multiplier Command
        self.buf    =   [0,0,0,0,0,0,0,0,0,0,0,0,0]               # Serial buffer  

    def hexc2dec(self, bufp):
        # Convert hex string (bufp) to decimal
        newval = 0
        divvy = 4096
        for pn in range(1, 5):
            vally = ord(bufp[pn])
            if(vally < 97):
                subby = 48
            else:
                subby = 87
            newval += ((ord(bufp[pn]) - subby) * divvy)
            divvy /= 16
            if(newval > 32767):
                newval = newval - 65536
        return newval

    def calculate_checksum(self, command):
        # Exclude stx and etx characters from the sum
        command_without_stx_etx = command[1:-3]  # Excluding the stx (start) and etx (end)
        # print(f"Command without stx and stx: {command_without_stx_etx}")
        
        # Calculate the sum of ASCII values
        total_sum = sum(ord(c) for c in command_without_stx_etx)
        # print(f"Sum of command bytes (excluding stx and etx): {total_sum}")
        
        # Calculate checksum: sum all bytes, take least significant byte (mod 256)
        checksum = total_sum % 256
        # print(f"Calculated checksum (mod 256): {checksum}")
        
        # Convert checksum to a two-character hex string
        checksum_hex = hex(checksum)[2:].zfill(2)  # Ensures it fits into two digits
        # print(f"Checksum in hex: {checksum_hex}")
        
        return checksum_hex

    def write_output_enable(self, state):
        # Convert temperature from decimal form to hexadecimal
        hex_num = hex(int((state * 100)))[2:].zfill(4)

        # Isolate digits of hex number
        hex_digits = list(state)

        # Substitute indices 3, 4, 5, 6 of wspc with the four hex digits
        for i in range(min(len(hex_digits), 4)):
            self.woec[3 + i] = hex_digits[i]

        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.woec)
        
        # Update the third and second to last digits of the command with the checksum
        self.woec[-3:-1] = list(checksum)

        # Debugging: print the final command being sent
        # print("Sending Write Output Enable Command: ", ''.join(self.woec))
        
        # Write each character with a 4ms delay
        for char in self.woec:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read response from controller to clear serial buffer
        for pn in range(0,8):
            self.buf[pn] = self.ser.read(1)

        time.sleep(0.1)
        return

    def read_output_enable(self):
        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.roec)
        
        # Update the third and second to last digits of the command with the checksum
        self.roec[-3:-1] = list(checksum)
        
        # Debugging: print the final command being sent
        # print("Sending Read Output Enable Command: ", ''.join(self.roec))
        
        # Write each character with a 4ms delay
        for char in self.roec:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read temperature from sensor 1
        for pn in range(0, 8):
            self.buf[pn] = self.ser.read(1)

        # Convert the temperature into decimal form using hexc2dec
        outEnb = int(self.hexc2dec(self.buf))

        time.sleep(0.1)
        return outEnb

    def read_temp1(self):
        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.rt1c)
        
        # Update the third and second to last digits of the command with the checksum
        self.rt1c[-3:-1] = list(checksum)
        
        # Debugging: print the final command being sent
        # print("Sending Read Temperature 1 Command: ", ''.join(self.rt1c))
        
        # Write each character with a 4ms delay
        for char in self.rt1c:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read temperature from sensor 1
        for pn in range(0, 8):
            self.buf[pn] = self.ser.read(1)

        # Convert the temperature into decimal form using hexc2dec
        temp1 = self.hexc2dec(self.buf) / 100.0

        time.sleep(0.1)
        return temp1

    def read_temp2(self):
        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.rt2c)
        
        # Update the third and second to last digits of the command with the checksum
        self.rt2c[-3:-1] = list(checksum)
        
        # Debugging: print the final command being sent
        # print("Sending Read Temperature 2 Command: ", ''.join(self.rt2c))
        
        # Write each character with a 4ms delay
        for char in self.rt2c:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read Temperature from sensor 2
        for pn in range(0, 8):
            self.buf[pn] = self.ser.read(1)

        # Convert the temperature into decimal form using hexc2dec
        temp2 = self.hexc2dec(self.buf) / 100.0

        time.sleep(0.1)
        return temp2

    def write_set_point(self, sPoint):

        '''
        
        '''
        # Convert temperature from decimal form to hexadecimal
        hex_num = hex(int((sPoint * 100)))[2:].zfill(4)

        # Isolate digits of hex number
        hex_digits = list(hex_num)

        # Substitute indices 3, 4, 5, 6 of wspc with the four hex digits
        for i in range(min(len(hex_digits), 4)):
            self.wspc[3 + i] = hex_digits[i]

        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.wspc)
        
        # Update the third and second to last digits of the command with the checksum
        self.wspc[-3:-1] = list(checksum)

        # Debugging: print the final command being sent
        # print("Sending Write Set Point Command: ", ''.join(self.wspc))
        
        # Write each character with a 4ms delay
        for char in self.wspc:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read response from controller to clear serial buffer
        for pn in range(0,8):
            self.buf[pn] = self.ser.read(1)

        time.sleep(0.1)
        return

    def read_set_point(self):
        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.rspc)
        
        # Update the third and second to last digits of the command with the checksum
        self.rspc[-3:-1] = list(checksum)

        # Debugging: print the final command being sent
        # print("Sending Read Set Point Command: ", ''.join(self.rspc))
        
        # Write each character with a 4ms delay
        for char in self.rspc:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read response (assuming the setpoint value is returned)
        for pn in range(0, 8):
            self.buf[pn] = self.ser.read(1)

        # Convert the response into decimal form using hexc2dec
        set_point = self.hexc2dec(self.buf) / 100.0

        time.sleep(0.1)
        return set_point

    def write_proportional_bandwidth(self, pBand):
        # Convert proportional bandwidth from decimal form to hexadecimal
        hex_num = hex(int((pBand * 100)))[2:].zfill(4)

        # Isolate digits of hex number
        hex_digits = list(hex_num)

        # Substitute indices 3, 4, 5, 6 of wpbc with the four hex digits
        for i in range(min(len(hex_digits), 4)):
            self.wpbc[3 + i] = hex_digits[i]

        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.wpbc)
        
        # Update the third and second to last digits of the command with the checksum
        self.wpbc[-3:-1] = list(checksum)

        # Debugging: print the final command being sent
        # print("Sending Write Proportional Bandwidth Command: ", ''.join(self.wpbc))
        
        # Write each character with a 4ms delay
        for char in self.wpbc:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read response from controller to clear serial buffer
        for pn in range(0,8):
            self.buf[pn] = self.ser.read(1)

        time.sleep(0.1)
        return

    def write_integral_gain(self, iGain):
        # Convert integral gain from decimal form to hexadecimal
        hex_num = hex(int((iGain * 100)))[2:].zfill(4)

        # Isolate digits of hex number
        hex_digits = list(hex_num)

        # Substitute indices 3, 4, 5, 6 of wigc with the four hex digits
        for i in range(min(len(hex_digits), 4)):
            self.wigc[3 + i] = hex_digits[i]

        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.wigc)
        
        # Update the third and second to last digits of the command with the checksum
        self.wigc[-3:-1] = list(checksum)

        # Debugging: print the final command being sent
        # print("Sending Write Integral Gain Command: ", ''.join(self.wigc))
        
        # Write each character with a 4ms delay
        for char in self.wigc:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read response from controller to clear serial buffer
        for pn in range(0,8):
            self.buf[pn] = self.ser.read(1)

        time.sleep(0.1)
        return

    def write_derivative_gain(self, dGain):
        # Convert derivative gain from decimal form to hexadecimal
        hex_num = hex(int((dGain * 100)))[2:].zfill(4)

        # Isolate digits of hex number
        hex_digits = list(hex_num)

        # Substitute indices 3, 4, 5, 6 of wdgc with the four hex digits
        for i in range(min(len(hex_digits), 4)):
            self.wdgc[3 + i] = hex_digits[i]

        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.wdgc)
        
        # Update the third and second to last digits of the command with the checksum
        self.wdgc[-3:-1] = list(checksum)

        # Debugging: print the final command being sent
        # print("Sending Write Derivative Gain Command: ", ''.join(self.wdgc))
        
        # Write each character with a 4ms delay
        for char in self.wdgc:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read response from controller to clear serial buffer
        for pn in range(0,8):
            self.buf[pn] = self.ser.read(1)

        time.sleep(0.1)
        return

    def write_heat_multiplier(self, hMult):
        # Convert heat multiplier from decimal form to hexadecimal
        hex_num = hex(int((hMult * 100)))[2:].zfill(4)

        # Isolate digits of hex number
        hex_digits = list(hex_num)

        # Substitute indices 3, 4, 5, 6 of whmc with the four hex digits
        for i in range(min(len(hex_digits), 4)):
            self.whmc[3 + i] = hex_digits[i]

        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.whmc)
        
        # Update the third and second to last digits of the command with the checksum
        self.whmc[-3:-1] = list(checksum)

        # Debugging: print the final command being sent
        # print("Sending Write Heat Multiplier Command: ", ''.join(self.whmc))
        
        # Write each character with a 4ms delay
        for char in self.whmc:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read response from controller to clear serial buffer
        for pn in range(0,8):
            self.buf[pn] = self.ser.read(1)

        time.sleep(0.1)
        return

    def write_cool_multiplier(self, cMult):
        # Convert cool multiplier from decimal form to hexadecimal
        hex_num = hex(int((cMult * 100)))[2:].zfill(4)

        # Isolate digits of hex number
        hex_digits = list(hex_num)

        # Substitute indices 3, 4, 5, 6 of wcmc with the four hex digits
        for i in range(min(len(hex_digits), 4)):
            self.wcmc[3 + i] = hex_digits[i]

        # Calculate the checksum for the command
        checksum = self.calculate_checksum(self.wcmc)
        
        # Update the third and second to last digits of the command with the checksum
        self.wcmc[-3:-1] = list(checksum)

        # Debugging: print the final command being sent
        # print("Sending Write Cool Multiplier Command: ", ''.join(self.wcmc))
        
        # Write each character with a 4ms delay
        for char in self.wcmc:
            self.ser.write(char.encode())  # Send each byte
            time.sleep(0.004)  # 4ms delay between each byte

        # Read response from controller to clear serial buffer
        for pn in range(0,8):
            self.buf[pn] = self.ser.read(1)

        time.sleep(0.1)
        return
    
    def set_temperature(self, temperature, wait_time=180):
        """Set temperature setpoint and wait for stabilization.

        Sets the temperature controller setpoint and automatically configures appropriate 
        heat/cool multipliers based on the target temperature. Enables output if not already
        enabled and waits for temperature to stabilize.

        Args:
            temperature (float): Target temperature setpoint in Celsius
            wait_time (int, optional): Time in seconds to wait for temperature stabilization. 
                                     Defaults to 180 seconds.
        """
        if 10 <= temperature < 20:
            heat_multiplier = 0.75
            cool_multiplier = 0.75

        elif 20 <= temperature < 30:
            heat_multiplier = 0.10
            cool_multiplier = 0.10

        elif 30 <= temperature < 40:
            heat_multiplier = 0.15
            cool_multiplier = 0.15

        elif 40 <= temperature < 50:
            heat_multiplier = 0.30
            cool_multiplier = 0.30

        elif 50 <= temperature < 60:
            heat_multiplier = 0.75
            cool_multiplier = 0.75

        elif temperature >= 60:
            heat_multiplier = 1.00
            cool_multiplier = 1.00
        else:
            print("Don't be so cold... You'll get condensation")

        self.write_heat_multiplier(heat_multiplier)
        self.write_cool_multiplier(cool_multiplier)
        self.write_set_point(temperature)

        if self.read_output_enable() == 0:
            self.write_output_enable('1')

        # print(f"Set point temperature: {self.read_set_point()}C")
        # print(f"Waiting {wait_time} seconds for temperature to stabilize")
        countdown_timer(wait_time)

        return {'set_point': self.read_set_point(), 
                'output_enable': self.read_output_enable(), 
                'read_temp1': self.read_temp1(), 
                'read_temp2': self.read_temp2()}


if __name__ == "__main__":
    TC = TC720control("com6")
    print(TC.read_temp1())
    print(TC.read_temp2())
    print(TC.read_set_point())
    print(TC.read_output_enable())

    # print(TC.set_temperature(temperature=25, wait_time=120))
 
