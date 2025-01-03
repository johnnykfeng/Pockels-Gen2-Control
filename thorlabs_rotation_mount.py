import time
import os
from ctypes import c_int, c_double, c_char_p, byref, cdll
# from ctypes import *


class RotationMount:
    def __init__(self, serial_num, lib_path=r"C:\Program Files\Thorlabs\Kinesis"):
        os.add_dll_directory(lib_path)
        self.lib = cdll.LoadLibrary("Thorlabs.MotionControl.KCube.DCServo.dll")  # loading dll
        self.serial_num = c_char_p(serial_num.encode())

    def open_device(self):
        if self.lib.TLI_BuildDeviceList() == 0:  # check is device list is built properly
            self.lib.CC_Open(self.serial_num)
            self.lib.CC_StartPolling(self.serial_num, c_int(200))

    def home_device(self):
        self.lib.CC_Home(self.serial_num)  # home device based on kinesis library
        time.sleep(1)

    # conversion from real units to device units
    def setup_conversion(self, steps_per_rev=1919.64186, gbox_ratio=1.0, pitch=1.0):
        STEPS_PER_REV = c_double(steps_per_rev)
        gbox_ratio = c_double(gbox_ratio)
        pitch = c_double(pitch)
        self.lib.CC_SetMotorParamsExt(self.serial_num, STEPS_PER_REV, gbox_ratio, pitch)

    def get_current_position(self):
        self.lib.CC_RequestPosition(self.serial_num)
        time.sleep(0.2)
        dev_pos = c_int(self.lib.CC_GetPosition(self.serial_num))
        real_pos = c_double()
        self.lib.CC_GetRealValueFromDeviceUnit(self.serial_num, dev_pos, byref(real_pos), 0)
        return real_pos.value

    def move_to_position(self, new_pos_real):
        new_pos_real = c_double(new_pos_real)
        new_pos_dev = c_int()
        self.lib.CC_GetDeviceUnitFromRealValue(self.serial_num, new_pos_real, byref(new_pos_dev), 0)
        self.lib.CC_SetMoveAbsolutePosition(self.serial_num, new_pos_dev)
        time.sleep(0.25)
        self.lib.CC_MoveAbsolute(self.serial_num)

    def close_device(self):
        self.lib.CC_Close(self.serial_num)


if __name__ == "__main__":
    rotation_mount = RotationMount("27267316")  # New device serial number
    rotation_mount.open_device()
    rotation_mount.home_device()
    rotation_mount.setup_conversion()
    print(f'Initial position: {rotation_mount.get_current_position()}')
    rotation_mount.move_to_position(130)
    # time.sleep(15)
    # print(f'Position after moving: {rotation_mount.get_current_position()}')  # Print current position

    # # rotation_mount.move_to_position(0)
    # time.sleep(10)

    # print(f'End Position: {rotation_mount.get_current_position()}')  # Print current position

    # rotation_mount.close_device()
