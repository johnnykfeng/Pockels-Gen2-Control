from Devices.thorlabs_rotation_mount import RotationMount
from Devices.camera_automation import CameraAutomation
from Devices.LED_control import LEDController
import time
import numpy as np

rotation_mount = RotationMount("27267316")
camera = CameraAutomation()
save_path = r"C:\Users\10552\Downloads\autogui_test"
led = LEDController()

if __name__ == "__main__":
    # Define the positions
    cross = 130
    parallel = 40
    rotation_mount.open_device()
    rotation_mount.home_device()
    rotation_mount.setup_conversion()

    led.set_current(100)
    led.turn_off()

    rotation_mount.move_to_position(parallel)
    camera.save_image_png(file_name="off_parallel.png", save_path=save_path)
    time.sleep(3)

    led.turn_on()
    camera.save_image_png(file_name="on_parallel.png", save_path=save_path)
    time.sleep(3)

    rotation_mount.move_to_position(cross)
    camera.save_image_png(file_name="on_cross.png", save_path=save_path)
    time.sleep(3)

    print(f'End Position: {rotation_mount.current_position}')
    # rotation_mount.home_device()
    rotation_mount.close_device()
    led.turn_off()
