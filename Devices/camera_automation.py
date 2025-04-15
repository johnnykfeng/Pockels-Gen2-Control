from loguru import logger
import pyautogui
import time
import os


# save_path_position = (-1210, 100)
save_path_position = (345, 100)
# file_name_position = (-1420, 770)
file_name_position = (350, 410)
record_button_position = (860, 230)
recording_file_name_position = (1550, 320)


pyautogui.FAILSAFE = False

def display_mouse_position():
    logger.info("Starting mouse position display. Press Ctrl-C to quit.")
    try:
        while True:
            x, y = pyautogui.position()
            positionStr = f"X: {str(x).rjust(4)} Y: {str(y).ljust(4)}"
            print(positionStr, end="")
            print("\b" * len(positionStr), end="", flush=True)
    except KeyboardInterrupt:
        logger.info("Mouse position display stopped by user")
        print("\n")

class CameraAutomation:
    def __init__(self):
        logger.info("Initializing CameraAutomation")
        self.pause_time = 1.0
        self.mouse_speed = 0.1
        self.type_speed = 0.01
        self.screen_size = pyautogui.size()
        self.screen_number = 2
        self.screen_center = (self.screen_size[0]//2, self.screen_size[1]//2)
        # logger.debug(f"Screen size: {self.screen_size}, Screen center: {self.screen_center}")

    def save_image_png(self, file_name, save_path=None):
        logger.info(f"Saving image as PNG - Filename: {file_name}, Path: {save_path}")
        
        pyautogui.click(x=self.screen_center[0]/2, y=self.screen_center[1], button='left', duration=1)
        # logger.debug(f"Screen center: {self.screen_center}")
        
        pyautogui.press('f4')
        
        if save_path is not None:
            # logger.debug(f"Setting save path to: {save_path}")
            pyautogui.click(save_path_position, button='left', duration=0.5, interval=self.mouse_speed)
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.typewrite(save_path, interval=self.type_speed)
            pyautogui.press('enter')
        
        # logger.debug("Setting filename")
        pyautogui.click(file_name_position, button='left', duration=self.mouse_speed, clicks=1)
        pyautogui.typewrite(file_name, interval=self.type_speed)
        time.sleep(0.3)
        pyautogui.press('enter')
        time.sleep(0.3)
        pyautogui.press('y')
        logger.success(f"Image saved successfully as {file_name}")

    def save_recording_xvi(self, file_name, save_path=None):
        logger.info(f"Saving recording as XVI - Filename: {file_name}, Path: {save_path}")

        save_location = os.path.join(save_path, file_name)

        pyautogui.click(recording_file_name_position, button='left', duration=0.5, interval=self.mouse_speed)
        pyautogui.typewrite(save_location, interval=self.type_speed)
        time.sleep(0.3)
        pyautogui.click(record_button_position, button='left', duration=0.5, interval=self.mouse_speed)


if __name__ == "__main__":
    
    # save_path = r"C:\Users\10552\Downloads\autogui_test"
    # file_name = "hello_world3.png"
    # # logger.info(f"Starting automation with file: {file_name} at path: {save_path}")
    
    # cam = CameraAutomation()
    # cam.save_image_png(file_name, save_path=save_path)

    display_mouse_position()

