# Code responsible for the layout and operation of the interface screen
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
import time
import os
os.environ["KIVY_NO_CONSOLELOG"] = "1" # Turns off annoying logging

defaults = {
    "sensor_id": "D418775",
    "save_path": "C:\\Users\\10552\\OneDrive - Redlen Technologies\\R&D-UVic Team - Data\\POCKELS\\New_optical_alignment_D418775_2025-05-20_A",
    "include_calibrations": True,
    "hv_initial": "-100",
    # "hv_initial": "700",
    "hv_final": "-1000",
    "hv_step": "-100",
    "comet_currents": "0",
    # "comet_currents": "1, 2, 3, 4, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25",
    "comet_voltage": "120",
    "led_current": "100",
    "cross_position": "135",
    "parallel_position": "45",
    "pause_time": "20",
    "invert_voltage": False,
}


class Gui(App):
    def build(self):
        self.layout = FloatLayout(
            # size_hint=(1, 1),
            size=(500, 800)

        )

        # redlen logo
        logo_path = "images/redlen_logo.jpg"
        image = Image(source=logo_path, size_hint=(None, None), size=(200, 125))
        image.pos_hint = {"x": 0.005, "top": 1}

        # title label
        title_label = Label(
            text="Pockels Experiment",
            font_size=30,
            # size_hint=(1, 1),
            # size=(500, 80),
        )
        title_label.pos_hint = {
            "center_x": 0.5,
            "top": 0.1,
        }  # center label at top

        centered_layout = BoxLayout(
            orientation="vertical", size_hint=(0.7, 0.9), 
            # size=(500, 300)
        )
        centered_layout.pos_hint = {"center_x": 0.45, "center_y": 0.50}

        # grid Layout
        centered_grid = GridLayout(
            cols=2,
            row_force_default=True,
            row_default_height=30,
            col_force_default=True,
            col_default_width=300,
            spacing=12.5,
        )

        # sensor id
        centered_grid.add_widget(Label(text="Sensor ID: ", font_size=20))
        self.sensor_id = TextInput(text=defaults["sensor_id"], multiline=False)
        centered_grid.add_widget(self.sensor_id)

        # save path
        centered_grid.add_widget(Label(text="Save Path: ", font_size=20))
        self.save_path = TextInput(text=defaults["save_path"], multiline=False)
        centered_grid.add_widget(self.save_path)

        # calibration checkbox
        calibration_checkbox_layout = BoxLayout(orientation="horizontal", spacing=10)
        self.calibration_checkbox1 = CheckBox(active=defaults["include_calibrations"], group="calibration")
        calibration_checkbox_layout.add_widget(self.calibration_checkbox1)
        calibration_checkbox_layout.add_widget(Label(text="Yes"))
        self.calibration_checkbox2 = CheckBox(active=(not defaults["include_calibrations"]), group="calibration")
        calibration_checkbox_layout.add_widget(self.calibration_checkbox2)
        calibration_checkbox_layout.add_widget(Label(text="No"))

        centered_grid.add_widget(Label(text="Include Calibrations? ", font_size=20))
        centered_grid.add_widget(calibration_checkbox_layout)

        # LED current
        centered_grid.add_widget(Label(text="LED Current (mA): ", font_size=20))
        self.led_current = TextInput(text=defaults["led_current"], width=10)
        centered_grid.add_widget(self.led_current)

        # HV initial
        centered_grid.add_widget(Label(text="HV initial (V): ", font_size=20))
        self.hv_initial = TextInput(text=defaults["hv_initial"], multiline=True)
        centered_grid.add_widget(self.hv_initial)

        # HV final
        centered_grid.add_widget(Label(text="HV final (V): ", font_size=20))
        self.hv_final = TextInput(text=defaults["hv_final"], multiline=True)
        centered_grid.add_widget(self.hv_final)

        # HV step
        centered_grid.add_widget(Label(text="HV step (V): ", font_size=20))
        self.hv_step = TextInput(text=defaults["hv_step"], multiline=True)
        centered_grid.add_widget(self.hv_step)

        # Invert Voltage?
        centered_grid.add_widget(Label(text="Invert Voltage? ", font_size=20))
        self.invert_voltage = CheckBox(active=defaults["invert_voltage"], group="invert_voltage")
        centered_grid.add_widget(self.invert_voltage)

        # x-ray currents -- seperated commas
        centered_grid.add_widget(Label(text="X-Ray Currents(mA): ", font_size=20))
        self.comet_currents = TextInput(
            text=defaults["comet_currents"], multiline=False
        )
        centered_grid.add_widget(self.comet_currents)

        # x-ray voltage
        centered_grid.add_widget(Label(text="X-Ray Voltage (V): ", font_size=20))
        self.comet_voltage = TextInput(text=defaults["comet_voltage"], multiline=False)
        centered_grid.add_widget(self.comet_voltage)

        # polarizer parallel position
        centered_grid.add_widget(
            Label(text="Polarizer Parallel Position (°): ", font_size=20)
        )
        self.parallel_position = TextInput(
            text=defaults["parallel_position"], multiline=False
        )
        centered_grid.add_widget(self.parallel_position)

        # polarizer cross position
        centered_grid.add_widget(
            Label(text="Polarizer Cross Position (°): ", font_size=20)
        )
        self.cross_position = TextInput(
            text=defaults["cross_position"], multiline=False
        )
        centered_grid.add_widget(self.cross_position)

        # pause time in between measurements
        centered_grid.add_widget(Label(text="Pause Time (seconds): ", font_size=20))
        self.pause_time = TextInput(text=defaults["pause_time"], multiline=False)
        centered_grid.add_widget(self.pause_time)

        # submit button
        submit = Button(
            text="Start", font_size=20, size_hint=(None, None), size=(200, 50)
        )
        submit.pos_hint = {"center_x": 0.5, "bottom": 0.1}
        submit.bind(on_press=self.press)

        centered_layout.add_widget(centered_grid)
        self.layout.add_widget(image)
        self.layout.add_widget(title_label)
        self.layout.add_widget(centered_layout)
        self.layout.add_widget(submit)

        return self.layout

    def on_submit(self, instance):
        Clock.schedule_once(self.press)

    def press(self, dt):
        try:
            # get the values from text inputs and checkbox
            self.led_current = float(self.led_current.text)
            self.hv_initial = int(self.hv_initial.text)
            self.hv_final = int(self.hv_final.text)
            self.hv_step = int(self.hv_step.text)
            self.comet_currents = list(map(float, self.comet_currents.text.split(",")))
            self.comet_voltage = float(self.comet_voltage.text)
            self.cross_position = float(self.cross_position.text)
            self.parallel_position = float(self.parallel_position.text)
            self.calibration_checkbox = (
                "Yes" if self.calibration_checkbox1.active else "No"
            )
            self.invert_voltage = self.invert_voltage.active
            self.pause_time = float(self.pause_time.text)
        except ValueError:
            raise ValueError(
                "One of your inputs could not be converted to a number. Make sure all your inputs are valid."
            )

        # clear all widgets from the layout
        self.layout.clear_widgets()

        # add new widgets for automated test details screen
        title_label = Label(
            text="Automated Test Details",
            font_size=30,
            size_hint=(None, None),
            size=(500, 80),
        )
        title_label.pos_hint = {"center_x": 0.5, "top": 0.97}
        self.layout.add_widget(title_label)

        # create measurements text based on user inputs
        measurements_text = ""
        if self.calibration_checkbox == "Yes":
            # measurements_text += "0V Crossed\n0V Parallel\nDark Parallel\n"
            measurements_text += "calib_parallel_off\ncalib_parallel_on\ncalib_cross_on\n"            
        for current in self.comet_currents:
            if self.invert_voltage:
                for hv in range(
                    -self.hv_initial, -self.hv_final - self.hv_step, -self.hv_step
                ):
                    measurements_text += f"bias_{hv}V_xray_{int(current)}mA\n"
            else:
                for hv in range(
                    self.hv_initial, self.hv_final + self.hv_step, self.hv_step
                ):
                    measurements_text += f"bias_{hv}V_xray_{int(current)}mA\n"

        # add measurements label
        measurements_label = Label(
            text=measurements_text,
            font_size=20,
            size_hint=(None, None),
            size=(500, 400),
        )
        measurements_label.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.layout.add_widget(measurements_label)

        # add "Begin Test" button
        begin_test_button = Button(
            text="Begin Test", font_size=20, size_hint=(None, None), size=(200, 50)
        )
        begin_test_button.pos_hint = {"center_x": 0.5, "bottom": 0.1}
        begin_test_button.bind(on_release=App.get_running_app().stop)
        self.layout.add_widget(begin_test_button)

    def stop(self, *args):
        print("Stopping app")
        super().stop(*args)


if __name__ == "__main__":
    # collect information to be used when running the code
    gui = Gui()
    gui.run()

    params = {}
    params["led_current"] = gui.led_current
    params["hv_initial"] = gui.hv_initial
    params["hv_final"] = gui.hv_final
    params["hv_step"] = gui.hv_step
    params["invert_voltage"] = gui.invert_voltage
    params["comet_currents"] = gui.comet_currents
    params["comet_voltage"] = gui.comet_voltage
    params["cross_position"] = gui.cross_position
    params["parallel_position"] = gui.parallel_position
    params["calibration_checkbox"] = gui.calibration_checkbox
    params["pause_time"] = gui.pause_time

    # print(f"LED Current: {gui_values['led_current']}")
    # print(f"HV Initial: {gui_values['hv_initial']}")
    # print(f"HV Final: {hv_final}")
    # print(f"HV Step: {hv_step}")
    # print(f"Comet Currents: {comet_currents}")
    # print(f"Comet Voltage: {comet_voltage}")
    # print(f"Cross Position: {cross_position}")
    # print(f"Parallel Position: {parallel_position}")
    # print(f"Calibration Checkbox: {calibration_checkbox}")
    # print(f"Pause Time: {pause_time}")
    print(f"Params: {params}")
    time.sleep(1)
    gui.stop()

    import numpy as np
    
    if params["invert_voltage"]:
        hv_initial, hv_final, hv_step = -params["hv_initial"], -params["hv_final"], -params["hv_step"]
    else:
        hv_initial, hv_final, hv_step = params["hv_initial"], params["hv_final"], params["hv_step"]
    hv_voltage = np.arange(hv_initial, hv_final + hv_step, hv_step)
    print(f"HV Voltage: {hv_voltage}")
    print(f"HV Voltage Type: {type(hv_voltage[0])}")
