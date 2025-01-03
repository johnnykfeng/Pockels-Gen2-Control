import pyautogui
import time
import os
import toml
from datetime import datetime

pyautogui.FAILSAFE = False

def display_mouse_position():
    print("Press Ctrl-C to quit.")
    try:
        while True:
            x, y = pyautogui.position()
            positionStr = "X: " + str(x).rjust(4) + " Y: " + str(y).ljust(4)
            print(positionStr, end="")
            print("\b" * len(positionStr), end="", flush=True)
    except KeyboardInterrupt:
        print("\n")

class CameraGuiAutomation:
    def __init__(self):
        self.pause_time = 1.0
        self.mouse_speed = 0.1
        self.type_speed = 0.01
        self.screen_size = pyautogui.size()
        self.screen_number = 2

    def save_image_png(self, image_name, image_path=None):
        pyautogui.moveTo(-1830, 33, duration=self.mouse_speed)
        pyautogui.moveTo(-self.screen_size[0]//2, self.screen_size[1]//2, duration=self.mouse_speed)
        pyautogui.click(button='left')
        pyautogui.press('f4')
        if image_path is not None:
            pyautogui.moveTo(-1210, 100, duration=self.mouse_speed)
            pyautogui.click(button='left')
            pyautogui.typewrite(image_path, interval=self.type_speed)
        pyautogui.moveTo(-1420, 770, duration=self.mouse_speed)
        pyautogui.click(button='left')
        pyautogui.typewrite(image_name, interval=self.type_speed)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.3)
        pyautogui.press('y')

if __name__ == "__main__":
    image_path = r"C:\Users\10552\Downloads\autogui_test"
    image_name = "hello_world3.png"
    cam = CameraGuiAutomation()
    cam.save_image_png(image_name, image_path)

