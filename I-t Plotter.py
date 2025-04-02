import csv
import matplotlib.pyplot as plt
from tkinter import filedialog
from tkinter import Tk

def plot_data_from_csv():
    # Create a Tkinter root window and immediately hide it (so the file dialog isn't blocked by a window)
    root = Tk()
    root.withdraw()

    # Open a file dialog to select multiple CSV files
    csv_file_paths = filedialog.askopenfilenames(
        title="Select CSV files",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )

    if not csv_file_paths:  # If no files are selected, exit the function
        print("No files selected, exiting.")
        return

    # Loop through each selected CSV file and plot its data
    for csv_file_path in csv_file_paths:
        # Open the CSV file to read the sensor ID and temperature from the first and second row
        with open(csv_file_path, mode='r') as file:
            reader = csv.reader(file)

            # Read the first row to get the sensor ID (second column)
            first_row = next(reader)
            sensor_id = first_row[1]  # Sensor ID is in the second column of the first row

            # Read the second row to get the temperature (second column)
            second_row = next(reader)
            temperature = second_row[1]  # Temperature is in the second column of the second row

            # Skip the next 6 rows (3rd to 8th rows)
            for _ in range(6):
                next(reader)

            # Now let's read the data starting from the 9th row
            data = []
            for row in reader:
                # Extract x data from the 5th column (index 4) and y data from the 3rd column (index 2)
                x_value = float(row[4])  # x data is in the 5th column (index 4)
                y_value = float(row[2])  # y data is in the 3rd column (index 2)
                data.append([x_value, y_value])

        # Extract the x and y data
        x_data = [row[0] for row in data]
        y_data = [row[1] for row in data]

        # Normalize the x data to start at 0 (subtract the first value from all x values)
        x_data = [x - x_data[0] for x in x_data]

        # Create the plot and label it with the temperature
        plt.plot(x_data, y_data, label=f'{temperature}°C')  # Add temperature to the legend
        plt.xlabel('Time')  # Replace with the appropriate x-axis label
        plt.ylabel('Sensor Reading')  # Replace with the appropriate y-axis label

    # Set the plot title after processing all files
    plt.title(f'Current vs Time for {sensor_id}')

    # Display the legend to distinguish between different temperature readings
    plt.legend()

    # Display the grid
    plt.grid()

    # Show the plot with all selected data
    plt.show()

# Example usage
plot_data_from_csv()
