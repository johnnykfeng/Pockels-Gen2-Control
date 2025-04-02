from Devices.temperature_controller import TC720control
import It_manual_test_script as it
from time import sleep
from datetime import datetime
import os
import csv
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.logger import Logger
import logging


def create_directory_and_csv(path, dir_name, csv_filename, data, metadata):
    # Create the full path for the directory where the file will be stored
    full_path = os.path.join(path, dir_name)
    
    # If the directory doesn't exist, create it
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    
    # Define the path for the CSV file
    csv_file_path = os.path.join(full_path, csv_filename)
    
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write metadata keys and values in vertical format with '#' in front of the keys
        for key, value in metadata.items():
            writer.writerow([f"#{key}", value])  # Writing the key with '#' and the corresponding value in the second column
        
        # Add an empty row between metadata and data for better readability
        writer.writerow([])

        # Write the data to the CSV file (measurement results)
        if data:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


def run_experiment(sensor_id, temperatures, voltages, current_range, nplc, samples):
    temp_ctrl = TC720control('com6')
    for set_point in temperatures:

        if 10 <= set_point < 20:
            heat_multiplier = 0.75
            cool_multiplier = 0.75

        elif 20 <= set_point < 30:
            heat_multiplier = 0.10
            cool_multiplier = 0.10

        elif 30 <= set_point < 40:
            heat_multiplier = 0.15
            cool_multiplier = 0.15

        elif 40 <= set_point < 50:
            heat_multiplier = 0.30
            cool_multiplier = 0.30

        elif 50 <= set_point < 60:
            heat_multiplier = 0.75
            cool_multiplier = 0.75

        elif set_point >= 60:
            heat_multiplier = 1.00
            cool_multiplier = 1.00

        else:
            print("Don't be so cold... You'll get condensation")

        temp_ctrl.write_heat_multiplier(heat_multiplier)
        temp_ctrl.write_cool_multiplier(cool_multiplier)
        temp_ctrl.write_set_point(set_point)

        if temp_ctrl.read_output_enable() == 0:
            temp_ctrl.write_output_enable('1')

        print(f"Set point temperature: {temp_ctrl.read_set_point()}C")
        sleep(300)

        volt_ctrl = it.ItProcedure()
        volt_ctrl.startup()
        output_data = volt_ctrl.execute(voltages, current_range, nplc, samples)

        path = 'C:\Code\Pockels-Gen2-Control\TEST_DATA\I-t Data'
        dir_name = sensor_id
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        csv_filename = f'{set_point}C_{timestamp}.csv'

        metadata = {
            "Sensor ID": sensor_id, 
            "Temperature": set_point, 
            "Test Voltages": voltages,
            "Keithley Current Range (A)": current_range,
            "Keithley NPLC": nplc,
            "Samples per Voltage": samples
            }
                
        create_directory_and_csv(path, dir_name, csv_filename, output_data, metadata)

        print(f'{set_point}C Measurement Complete')

    temp_ctrl.write_output_enable('0')
        
    print("All Done :)")


class GUI(App):
    def build(self):

        Logger.setLevel(logging.CRITICAL)

        # Create a BoxLayout to hold all elements
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Create a ScrollView for the text inputs
        scroll_view = ScrollView(size_hint=(1, 0.8))
        input_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=500)
        
        # Define labels and corresponding input names
        labels = ["Sensor ID", "Temperatures", "Voltages", "Keithley Current Range (A)", "Keithley NPLC", "Samples per Voltage"]
        defaults = {
            "Sensor ID": "", 
            "Temperatures": "10, 20, 30, 40, 50, 60, 70, 80, 90", 
            "Voltages": "-100, -200, -300, -400, -500, -600, -700, -800, -900, -1000",
            "Keithley Current Range (A)": "10e-6",
            "Keithley NPLC": "0.01", 
            "Samples per Voltage": "2000"
        }
        self.inputs = []
        
        for i, label_text in enumerate(labels):
            label = Label(text=f"{label_text}: ", size_hint_y=None, height=30)
            text_input = TextInput(size_hint_y=None, height=30, multiline=False)
            text_input.text = defaults[label_text]
            input_layout.add_widget(label)
            input_layout.add_widget(text_input)
            self.inputs.append(text_input)

        scroll_view.add_widget(input_layout)
        layout.add_widget(scroll_view)
        
        # Create the Run button
        run_button = Button(text='Run', size_hint_y=None, height=50)
        run_button.bind(on_press=self.on_run_button_click)
        layout.add_widget(run_button)
        
        return layout

    def on_run_button_click(self, instance):
        # Get the text from each input and print it
        sensor_id = self.inputs[0].text
        temperatures = self.parse_int_list(self.inputs[1].text)
        voltages = self.parse_int_list(self.inputs[2].text)
        current_range = self.safe_float(self.inputs[3].text)
        keithley_nplc = self.safe_float(self.inputs[4].text)
        samples_per_voltage = self.safe_int(self.inputs[5].text)
        
        print(f"Sensor ID: {sensor_id}")
        print(f"Temperatures: {temperatures}")
        print(f"Voltages: {voltages}")
        print(f"Keithley Current Range (A): {current_range}")
        print(f"Keithley NPLC: {keithley_nplc}")
        print(f"Samples per Voltage: {samples_per_voltage}")
        run_experiment(sensor_id, temperatures, voltages, current_range, keithley_nplc, samples_per_voltage)

    def parse_list_input(self, input_text):
        """Helper method to parse comma-separated input into a list."""
        if input_text:
            return [item.strip() for item in input_text.split(',')]
        return []
    
    def safe_float(self, input_text):
        """Helper method to convert input text to a float, returns None if invalid."""
        try:
            return float(input_text)
        except ValueError:
            return None  # or you could return 0.0 or another default value if you prefer
    
    def parse_float_list(self, input_text):
        """Helper method to parse comma-separated input into a list of floats."""
        if input_text:
            try:
                return [float(item.strip()) for item in input_text.split(',')]
            except ValueError:
                return []  # If there is an error in conversion, return an empty list
        return []
    
    def safe_int(self, input_text):
        """Helper method to convert input text to an int, returns None if invalid."""
        try:
            return int(input_text)
        except ValueError:
            return None  # or you could return 0 or another default value if you prefer
    
    def parse_int_list(self, input_text):
        """Helper method to parse comma-separated input into a list of ints."""
        if input_text:
            try:
                return [int(item.strip()) for item in input_text.split(',')]
            except ValueError:
                return []  # If there is an error in conversion, return an empty list
        return []


if __name__ == "__main__":
    app = GUI()
    app.run()
