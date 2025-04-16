from Devices.temperature_controller import TC720control
import It_control as it
from time import sleep
from datetime import datetime
import os
os.environ["KIVY_NO_CONSOLELOG"] = "1"      # Turns off annoying logging
import csv
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.logger import Logger


# Function to save metadata and data to a CSV file
def save_to_csv(metadata, data, directory, filename):
    try:
        file_path = os.path.join(directory, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Open the CSV file for writing
        with open(file_path, mode='w', newline='') as file:

            writer = csv.writer(file)

            # Write metadata
            for key, value in metadata.items():
                writer.writerow([f"# {key}: {value}"])  # Write each metadata line
            
            # Write an empty row to separate metadata from data
            writer.writerow([])

            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
                
        print(f"Data and metadata have been saved to {file_path}")
    
    except Exception as e:
        print(f"An error occurred: {e}")


def run_experiment(sensor_id, temperatures, voltages, current_range, nplc, samples, cross_angle, parallel_angle, led_current):

    temp_ctrl = TC720control('com6')

    for set_point in temperatures:

        save_path = f"C:\Code\Pockels-Gen2-Control\TEST_OUTPUTS\{sensor_id}"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        csv_filename = f'{sensor_id}_{set_point}C_{timestamp}.csv'
        metadata = {
            "Sensor ID": sensor_id, 
            "Temperature": set_point, 
            "Test Voltages": voltages,
            "Keithley Current Range (A)": current_range,
            "Keithley NPLC": nplc,
            "Samples per Voltage": samples,
            "Cross Angle": cross_angle,
            "Parallel Angle": parallel_angle,
            "LED Current": led_current,
            }

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

        experiment = it.PockelsProcedure()
        experiment.startup(sensor_id, set_point, cross_angle, parallel_angle, led_current, save_path)
        It_data = experiment.execute_ramp_capture(save_path, timestamp, sensor_id, set_point, voltages, current_range, nplc, samples)

        save_path = os.path.join(save_path, "IT_DATA")
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        save_to_csv(metadata=metadata, data=It_data, directory=save_path, filename=csv_filename)

        print(f'{set_point}C Measurement Complete')

    temp_ctrl.write_output_enable('0')
        
    print("All Done :)")


class GUI(App):
    def build(self):
        # Create a BoxLayout to hold all elements
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Create a ScrollView for the text inputs
        scroll_view = ScrollView(size_hint=(0.95, 0.8), pos_hint={'center_x': 0.5})
        input_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=600, spacing=10)
        input_layout.bind(minimum_height=input_layout.setter('height'))
        
        # Define labels and corresponding input names
        labels = ["Sensor ID", "Temperatures", "Voltages", "Keithley Current Range (A)", "Keithley NPLC", "Samples per Voltage", 
                  "Cross Angle", "Parallel Angle", "LED Current"]
        defaults = {
            "Sensor ID": "", 
            "Temperatures": "10, 20, 30, 40, 50, 60, 70, 80, 90", 
            "Voltages": "-100, -200, -300, -400, -500, -600, -700, -800, -900, -1000",
            "Keithley Current Range (A)": "10e-6",
            "Keithley NPLC": "0.01", 
            "Samples per Voltage": "2000",
            "Cross Angle": "130",
            "Parallel Angle": "40",
            "LED Current": "100"
        }
        self.inputs = []
        
        for i, label_text in enumerate(labels):
            # Create a horizontal BoxLayout for each label-input pair
            row_layout = BoxLayout(size_hint_y=None, height=40, spacing=10)
            
            label = Label(
                text=f"{label_text}: ",
                size_hint_x=0.4,
                halign='right',
                valign='middle'
            )
            label.bind(size=label.setter('text_size'))
            
            text_input = TextInput(
                size_hint_x=0.6,
                multiline=False,
                padding=[10, 10, 10, 10],
                halign='center'
            )
            text_input.text = defaults[label_text]
            
            row_layout.add_widget(label)
            row_layout.add_widget(text_input)
            input_layout.add_widget(row_layout)
            self.inputs.append(text_input)

        scroll_view.add_widget(input_layout)
        layout.add_widget(scroll_view)
        
        # Create the Run button
        run_button = Button(
            text='Run',
            size_hint=(0.3, None),
            height=50,
            pos_hint={'center_x': 0.5}
        )
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
        cross_angle = self.safe_float(self.inputs[6].text)
        parallel_angle = self.safe_float(self.inputs[7].text)
        led_current = self.safe_float(self.inputs[8].text)
        
        print(f"Sensor ID: {sensor_id}")
        print(f"Temperatures: {temperatures}")
        print(f"Voltages: {voltages}")
        print(f"Keithley Current Range (A): {current_range}")
        print(f"Keithley NPLC: {keithley_nplc}")
        print(f"Samples per Voltage: {samples_per_voltage}")
        print(f"Cross Angle: {cross_angle}")
        print(f"Parallel Angle: {parallel_angle}")
        print(f"LED Current: {led_current}")
        run_experiment(sensor_id, temperatures, voltages, current_range, keithley_nplc, samples_per_voltage, cross_angle, parallel_angle, led_current)

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
