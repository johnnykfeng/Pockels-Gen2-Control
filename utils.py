from loguru import logger
import pyautogui
import time
import numpy as np

def countdown_timer(seconds, action_interval=300):
    """Countdown timer for specified seconds"""
    logger.warning("Countdown Timer: " + str(seconds) + " seconds")
    while seconds > 0:
        print(seconds, end=" ")
        print("\b" * 5, end="", flush=True)
        time.sleep(1)
        seconds -= 1
        if seconds % action_interval == 0 and seconds != 0:
            minutes = seconds // 60
            # seconds_remaining = seconds % 60
            print(f"{minutes} minutes remaining")
            pyautogui.press("win")
            pyautogui.typewrite("Don't Sleep!", interval=0.05)
            pyautogui.press("esc")

def voltages_log_space(min_voltage, max_voltage, data_points):
    """
    Generate a list of voltages in a logarithmic space between min_voltage and max_voltage.
    The list will have data_points number of elements.
    """
    near_zero = 0.01 # a number that is almost zero
    if min_voltage > max_voltage or min_voltage==max_voltage:
        raise ValueError(f"min_voltage ({min_voltage}) cannot be greater than or equal to max_voltage ({max_voltage})")
    
    if min_voltage < 0 and max_voltage > 0:
        negatives = -1 * np.geomspace(abs(min_voltage), near_zero, round(data_points / 2))
        positives = np.geomspace(near_zero, abs(max_voltage), round(data_points / 2))
        voltages = np.concatenate([negatives, positives])
    elif min_voltage < 0 and max_voltage <= 0:
        if max_voltage == 0:
            max_voltage = near_zero
        voltages = -1 * np.geomspace(abs(min_voltage), abs(max_voltage), data_points)
    elif min_voltage >= 0 and max_voltage >= 0:
        if min_voltage == 0:
            min_voltage = near_zero
        voltages = np.geomspace(min_voltage, max_voltage, data_points)
    return voltages