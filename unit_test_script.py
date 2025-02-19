from Devices.temperature_controller import TC720control
import time
import csv

if __name__ == "__main__":

    set_points = {
        10: {"heat_multiplier": 0.75, "cool_multiplier": 0.75, "proportional_bandwidth": 4.50, "integral_gain": 1.40, "derivative_gain": 9.20},
        20: {"heat_multiplier": 0.10, "cool_multiplier": 0.10, "proportional_bandwidth": 4.50, "integral_gain": 1.40, "derivative_gain": 9.20},
        30: {"heat_multiplier": 0.15, "cool_multiplier": 0.15, "proportional_bandwidth": 4.50, "integral_gain": 1.40, "derivative_gain": 9.20},
        40: {"heat_multiplier": 0.30, "cool_multiplier": 0.30, "proportional_bandwidth": 4.50, "integral_gain": 1.40, "derivative_gain": 9.20},
        50: {"heat_multiplier": 0.75, "cool_multiplier": 0.75, "proportional_bandwidth": 4.50, "integral_gain": 1.40, "derivative_gain": 9.20},
        60: {"heat_multiplier": 1.00, "cool_multiplier": 1.00, "proportional_bandwidth": 4.50, "integral_gain": 1.40, "derivative_gain": 9.20},
        70: {"heat_multiplier": 1.00, "cool_multiplier": 1.00, "proportional_bandwidth": 4.50, "integral_gain": 1.40, "derivative_gain": 9.20}
    }

    temp_ctrl = TC720control('com6')

    for set_point in set_points:
        heat_multiplier = set_points[set_point]["heat_multiplier"]
        cool_multiplier = set_points[set_point]["cool_multiplier"]
        proportional_bandwidth = set_points[set_point]["proportional_bandwidth"]
        integral_gain = set_points[set_point]["integral_gain"]
        derivative_gain = set_points[set_point]["derivative_gain"]

        temp_ctrl.write_proportional_bandwidth(proportional_bandwidth)
        temp_ctrl.write_integral_gain(integral_gain)
        temp_ctrl.write_derivative_gain(derivative_gain)
        temp_ctrl.write_heat_multiplier(heat_multiplier)
        temp_ctrl.write_cool_multiplier(cool_multiplier)
        temp_ctrl.write_set_point(set_point)

        if temp_ctrl.read_output_enable() == 0:
            temp_ctrl.write_output_enable('1')

        print(f"Set point: {temp_ctrl.read_set_point()}")
        
        with open(f'temp_gradient_{set_point}.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Time (s)', 'Temperature 1 (C)', 'Temperature 2 (C)'])

            for i in range(900):
                temp1 = temp_ctrl.read_temp1()
                temp2 = temp_ctrl.read_temp2()
                print(f"Time: {i}, Temperature 1: {temp1}, Temperature 2: {temp2}")
                writer.writerow([i, temp1, temp2])
                time.sleep(1)

    temp_ctrl.write_output_enable('0')