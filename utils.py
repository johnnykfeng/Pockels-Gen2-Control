from loguru import logger
import pyautogui
import time
import numpy as np


def dont_sleep():
    pyautogui.press("win")
    pyautogui.typewrite("Don't Sleep!", interval=0.05)
    pyautogui.press("esc")


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

def voltages_log_space(start_voltage:int, 
                       stop_voltage:int, 
                       data_points:int, 
                       near_zero=0.01,
                       round_decimal=None):
    """
    Generate a list of voltages in a logarithmic space between min_voltage and max_voltage.
    The list will have data_points number of elements.
    """
    # near_zero = 0.01 # a number that is almost zero
    if start_voltage < 0 and stop_voltage > 0:
        negatives = -1 * np.geomspace(abs(start_voltage), near_zero, round(data_points / 2))
        positives = np.geomspace(near_zero, abs(stop_voltage), round(data_points / 2))
        voltages = np.concatenate([negatives, positives])
    elif start_voltage < 0 and stop_voltage <= 0:
        if stop_voltage == 0:
            stop_voltage = near_zero
        voltages = -1 * np.geomspace(abs(start_voltage), abs(stop_voltage), data_points)
    elif start_voltage >= 0 and stop_voltage >= 0:
        if start_voltage == 0:
            start_voltage = near_zero
        voltages = np.geomspace(start_voltage, stop_voltage, data_points)
    elif stop_voltage < 0 and start_voltage >=0:
        voltages = -1 * np.geomspace(near_zero, abs(stop_voltage), data_points)

    if round_decimal is not None:
        return np.round(voltages, round_decimal)
    return voltages

def voltages_dual_direction(min_voltage, max_voltage, data_points):
    """
    Generate a list of voltages in a logarithmic space between min_voltage and max_voltage.
    The list will have data_points number of elements. Then create a new list from max_voltage to min_voltage. 
    Then concatenate the two lists and return the result.
    """
    voltages = voltages_log_space(min_voltage, max_voltage, data_points)
    voltages = np.concatenate([voltages, -1 * voltages])
    return voltages


if __name__ == "__main__":
    dont_sleep()
    time.sleep(2)
    dont_sleep()
    time.sleep(2)
    dont_sleep()
    # voltages = voltages_log_space(min_voltage=-1000, max_voltage=1000, data_points=100)
    # print(voltages)
    # # import matplotlib.pyplot as plt
    # # plt.plot(voltages, '.-')
    # # plt.grid(True)
    # # plt.show()
    # voltages = voltages_dual_direction(min_voltage=-1000, max_voltage=1000, data_points=100)
    # print(voltages)
    # import matplotlib.pyplot as plt
    # plt.plot(voltages, '.-')
    # plt.grid(True)
    # plt.show()

