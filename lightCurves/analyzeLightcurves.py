import lightkurve as lk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Configuration and Setup ---

# Get the absolute path of the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct absolute paths for input and output files
data_file_path = os.path.join(script_dir, 'starData.csv')
output_dir = os.path.join(script_dir, 'export')

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

print(f"Analysing File-1")

# --- CSV Parsing ---
# Note that we skip the first 4 rows from any of the excel sheets as they are not important
df = pd.read_csv(data_file_path, skiprows=4)

# --- Lightcurve Analysis ---
for i in range(df.shape[0]):

    starstr = "TIC " + str(df.iloc[i, 0])
    print(f"Analysing index - {i}")

    try:
        initial = lk.search_lightcurve(starstr)  # Searching the data for the a given "starstr"
        rows = len(initial)
    except KeyboardInterrupt:
        print(f"Analysis interrupted by user for {starstr} on index {i}.")
        break # Exit the loop gracefully
    except Exception as e:
        print(f"{starstr}[all] skipped. Error: {e}")
        continue

    # This is the program to analyse each subset data of a particular "starstr"
    for row in range(rows):

        try:
            file1 = initial[row].download(quality_bitmask="default").remove_nans()
            temporary_file = file1.remove_outliers(sigma=4).flatten()
        except KeyboardInterrupt:
            print(f"Analysis interrupted by user for {starstr} on index {i}, subset {row}.")
            break # Exit the inner loop gracefully
        except Exception as e:
            print(f"{starstr}[{rows}] skipped for subset {row}. Error: {e}")
            continue

        # We use two seperate files to be analysed, as a result we get 2 figures for every subset
        # This is because the "to_periodogram" function does not do a good job in finding the accurate time period
        # The method we use does not guarentee a 100% accuracy either
        periodogram_file_1 = temporary_file.to_periodogram(method="bls")
        periodogram_file_2 = temporary_file.to_periodogram(method="bls", period=np.arange(1, 16, 0.01))

        time_period_file1 = periodogram_file_1.period_at_max_power
        time_period_file2 = periodogram_file_2.period_at_max_power

        # Check if periodogram results are valid before folding
        if time_period_file1 is None or time_period_file2 is None:
            print(f"Could not determine period for {starstr}. Skipping folding and plotting.")
            continue # Skip to next subset

        final_file_1 = temporary_file.fold(period=time_period_file1)
        final_file_2 = temporary_file.fold(period=time_period_file2)

        # Create a DataFrame with the folded light curve data
        df_folded = final_file_1.to_pandas()

        # Extract x and y for fitting
        x_data = final_file_1.time.value
        y_data = final_file_1.flux.value

        # Perform polynomial fit (degree 18, as in original code)
        z = np.polyfit(x_data, y_data, 18)
        f = np.poly1d(z)

        # Generate new x values for the fitted line
        x_new = np.linspace(x_data.min(), x_data.max(), 100)
        y_new = f(x_new)

        # --- Plotting ---
        ax = final_file_1.plot() # Get the axes object from lightkurve plot
        ax.plot(x_new, y_new, color='red', linewidth=2, label='Polynomial Fit') # Overlay the fitted line
        ax.set_title(f'Folded Light Curve for TIC {starstr}')
        ax.legend()
        plt.savefig(os.path.join(output_dir, starstr + f"[normal][index {i}].png"))  # Plot 1
        print(f"Plot generated for {starstr} (normal periodogram).")
        plt.close('all')
