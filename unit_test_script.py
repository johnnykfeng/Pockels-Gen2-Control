from Devices.temperature_controller import TC720control
import It_manual_test_script as it
from time import sleep

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
    sensor_id = input("Enter sensor ID: ")
    max_voltage = float(input("Enter maximum voltage: "))
    steps = int(input("Enter number of steps for ramp: "))
    data_points = int(input("Enter desired number of readings for each step: "))
    
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

        print(f"Set point temperature: {temp_ctrl.read_set_point()}C")
        sleep(300)

        volt_ctrl = it.ItProcedure()
        volt_ctrl.startup()
        volt_ctrl.execute(sensor_id, max_voltage, steps, data_points, set_point)


    temp_ctrl.write_output_enable('0')