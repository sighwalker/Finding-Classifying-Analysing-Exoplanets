import lightkurve as lk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# --- Configuration and Setup ---

# Get the absolute path of the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct absolute paths for input and output files
data_file_path = os.path.join(script_dir, 'StarData_1.csv')
output_dir = os.path.join(script_dir, 'export')

# Create the output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

print(f"Analysing File-1")

# --- CSV Parsing ---
# The CSV has comment lines, a comma-separated header, and comma-separated data.
# We need to parse it carefully.

column_names = []
data_rows = []

with open(data_file_path, 'r') as f:
    for i, line in enumerate(f):
        if i == 4: # This is the 5th line (index 4), which is the header
            column_names = [col.strip() for col in line.strip().split(',')]
        elif i >= 5: # Data starts from the 6th line (index 5)
            data_rows.append([item.strip() for item in line.strip().split(',')])

# Create DataFrame from parsed data and assign column names
df = pd.DataFrame(data_rows, columns=column_names)

# Ensure 'ID' column is numeric and handle potential non-numeric entries
df['ID'] = pd.to_numeric(df['ID'], errors='coerce')
df.dropna(subset=['ID'], inplace=True) # Remove rows where ID could not be converted
tic_list = np.array(df['ID'], dtype=int) # Convert to integer array

print(f"Found {len(tic_list)} TIC IDs to analyze.")

# --- Lightcurve Analysis ---
for tic_id in tic_list:
    print(f"\nAnalyzing TIC ID: {tic_id}")
    try:
        # Search for the light curve
        # Using f'TIC {tic_id}' ensures the correct format for lightkurve search
        lc_search = lk.search_lightcurve(f'TIC {tic_id}', author="SPOC", exptime=120)
        
        if not lc_search:
            print(f"No light curves found for TIC {tic_id}. Skipping.")
            continue

        # Download, stitch, flatten, and remove outliers
        lc = lc_search.download().stitch().flatten(window_length=901).remove_outliers()

        # Create a periodogram to find the planet's period
        period = np.linspace(1, 20, 10000)
        bls = lc.to_periodogram(method='bls', period=period, frequency_factor=500)
        planet_x_period = bls.period_at_max_power
        planet_x_t0 = bls.transit_time_at_max_power

        # Fold the light curve at the found period
        folded_lc = lc.fold(period=planet_x_period, epoch_time=planet_x_t0)

        # Create a DataFrame with the folded light curve data
        # lightkurve objects can be directly converted to pandas DataFrames
        df_folded = folded_lc.to_pandas()

        # Save the DataFrame to a CSV file
        output_file_path = os.path.join(output_dir, f'Folded_Lightcurve_Data_{tic_id}.csv')
        df_folded.to_csv(output_file_path, index=False)

        print(f'Successfully processed and saved data for TIC {tic_id} to {output_file_path}')

        # --- Plotting (Optional, if you want to generate plots) ---
        # This part was in the original script, but lightkurve has built-in plotting.
        # If you want to use matplotlib directly, ensure data is numeric.
        # For simplicity, I'm removing the complex polyfit plotting from the original
        # and suggesting lightkurve's built-in plot or a simpler matplotlib plot.
        
        # Example of lightkurve's built-in plot:
        # folded_lc.plot()
        # plt.title(f'Folded Light Curve for TIC {tic_id}')
        # plt.savefig(os.path.join(output_dir, f'Folded_Lightcurve_Plot_{tic_id}.png'))
        # plt.close('all')

    except Exception as e:
        print(f"An error occurred for TIC ID {tic_id}: {e}")
