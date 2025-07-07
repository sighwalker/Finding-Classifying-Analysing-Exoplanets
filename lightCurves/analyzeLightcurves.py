import lightkurve as lk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from wotan import flatten
import batman
from scipy.optimize import curve_fit
import sys
import joblib # Import joblib for loading the model

# --- Configuration and Setup ---

# Print the Python executable path for debugging
print(f"DEBUG: Python executable: {sys.executable}\n")

# Get the absolute path of the directory containing the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Define the input directory where the downloaded light curve CSVs are stored
input_dir = '/home/sighw/codes/Finding-Classifying-Analysing-Exoplanets/lightScript/export'

# Define the output directory for plots and extracted parameters
output_dir = os.path.join(script_dir, 'analyzed_plots')

# Create the base output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Define the path for the extracted parameters CSV
parameters_csv_path = os.path.join(output_dir, 'extracted_features.csv')

# Define the path to the trained classifier model (updated name)
classifier_model_path = os.path.join(script_dir, '..', 'verifying', 'random_forest_exoplanet_classifier.joblib')

# Initialize the parameters CSV with headers if it doesn't exist
# Added 'classification' column for the model's prediction
if not os.path.exists(parameters_csv_path):
    with open(parameters_csv_path, 'w') as f:
        f.write("filename,period,t0,rp_rs,a_rs,inc,duration,depth,snr,classification\n")

print(f"--- Starting analysis of light curves from: {input_dir} ---\n")

# --- Load the pre-trained classifier model ---
try:
    classifier_model = joblib.load(classifier_model_path)
    print(f"Classifier model loaded from: {classifier_model_path}\n")
except FileNotFoundError:
    classifier_model = None
    print(f"Warning: Classifier model not found at {classifier_model_path}. Classification will be skipped.\n")
except Exception as e:
    classifier_model = None
    print(f"Error loading classifier model: {e}. Classification will be skipped.\n")

# --- Transit Model Function for curve_fit ---
def transit_model_for_fit(time, period, t0, rp_rs, a_rs, inc):
    params = batman.TransitParams()  # object to store transit parameters
    params.t0 = t0                    # time of inferior conjunction
    params.per = period               # orbital period
    params.rp = rp_rs                 # planet radius (in units of stellar radii)
    params.a = a_rs                   # semi-major axis (in units of stellar radii)
    params.inc = inc                  # orbital inclination (in degrees)
    params.ecc = 0.0                  # eccentricity (fixed for simplicity)
    params.w = 90.0                   # longitude of periastron (fixed for simplicity)
    params.limb_dark = "quadratic"    # limb darkening model
    params.u = [0.3, 0.2]             # limb darkening coefficients (fixed for simplicity)

    m = batman.TransitModel(params, time)
    return m.light_curve(params)

# --- Lightcurve Analysis Loop ---

# Walk through the input directory to find all CSV files, including in subfolders
for root, _, files in os.walk(input_dir):
    for filename in files:
        if filename.endswith('.csv'):
            file_path = os.path.join(root, filename)
            print(f"\n--- Analysing file: {filename} ---")

            classification_result = "N/A" # Default classification result
            extracted_snr = np.nan # Default SNR

            try:
                # Read the CSV file into a Pandas DataFrame
                df_lc = pd.read_csv(file_path)

                # Convert DataFrame to a Lightkurve LightCurve object
                lc = lk.LightCurve(time=df_lc['time'], flux=df_lc['flux'])

                # Remove NaNs before detrending
                lc = lc.remove_nans()

                # --- Advanced Detrending with Wotan ---
                flat_flux, trend_flux = flatten(lc.time.value, lc.flux.value,
                                                method='biweight', window_length=0.5,
                                                return_trend=True)

                # Create a new LightCurve object with the detrended flux
                detrended_lc = lk.LightCurve(time=lc.time.value, flux=flat_flux)

                # Periodogram analysis on the detrended light curve
                periodogram_lc = detrended_lc.to_periodogram(method="bls")
                time_period_lc = periodogram_lc.period_at_max_power
                extracted_snr = periodogram_lc.max_power # Use max_power as SNR proxy

                # Check if periodogram results are valid before folding
                if time_period_lc is None:
                    print(f"Could not determine period for {filename}. Skipping folding and plotting.\n")
                    continue

                # Estimate t0 (time of first transit) - for simplicity, use the time of minimum flux
                t0_estimate = detrended_lc.time[np.argmin(detrended_lc.flux)].value

                folded_lc = detrended_lc.fold(period=time_period_lc, t0=t0_estimate)

                # Extract x and y for fitting
                x_data = folded_lc.time.value
                y_data = folded_lc.flux.value

                # --- Initial Guesses for Batman Parameters for curve_fit ---
                initial_guesses = [
                    time_period_lc.value,  # period
                    t0_estimate,           # t0
                    (1.0 - np.min(y_data))**0.5, # rp_rs (rough estimate)
                    10.0,                  # a_rs (typical value, might need refinement)
                    89.0                   # inc (close to 90 for transiting)
                ]

                # Bounds for parameters
                bounds = (
                    [time_period_lc.value * 0.9, t0_estimate - 0.1, 0.01, 1.0, 80.0],
                    [time_period_lc.value * 1.1, t0_estimate + 0.1, 0.5, 50.0, 90.0]
                )

                # --- Fit Transit Model using curve_fit ---
                try:
                    popt, pcov = curve_fit(transit_model_for_fit, x_data, y_data, p0=initial_guesses, bounds=bounds)
                    fitted_period, fitted_t0, fitted_rp_rs, fitted_a_rs, fitted_inc = popt

                    # Generate model flux with fitted parameters
                    model_flux = transit_model_for_fit(x_data, *popt)

                    # Calculate duration and depth from fitted parameters
                    fitted_depth = fitted_rp_rs**2
                    transit_points = x_data[y_data < (1 - fitted_depth * 0.5)]
                    fitted_duration = np.max(transit_points) - np.min(transit_points) if len(transit_points) > 1 else 0.0

                    # --- Classification ---
                    if classifier_model:
                        # Create a feature vector for prediction
                        # Order: period, depth, duration, inc, rp_rs, snr
                        feature_vector = np.array([[fitted_period, fitted_depth, fitted_duration, fitted_inc, fitted_rp_rs, extracted_snr]])
                        
                        # Make prediction
                        prediction = classifier_model.predict(feature_vector)[0]
                        classification_result = "Exoplanet" if prediction == 1 else "False Positive"
                        print(f"Classification for {filename}: {classification_result}\n")

                    # Save extracted parameters and classification to CSV
                    with open(parameters_csv_path, 'a') as f:
                        f.write(f"{filename},{fitted_period},{fitted_t0},{fitted_rp_rs},{fitted_a_rs},{fitted_inc},{fitted_duration},{fitted_depth},{extracted_snr},{classification_result}\n")
                    print(f"Extracted parameters saved for {filename}.\n")

                except RuntimeError as e:
                    print(f"Could not fit transit model for {filename}: {e}\n")
                    model_flux = np.full_like(x_data, np.nan) # Use NaNs if fit fails
                    # Save a row with NaNs for failed fits and N/A classification
                    with open(parameters_csv_path, 'a') as f:
                        f.write(f"{filename},NaN,NaN,NaN,NaN,NaN,NaN,NaN,{extracted_snr},{classification_result}\n")

                # --- Plotting ---
                fig, ax = plt.subplots(figsize=(10, 6))
                folded_lc.plot(ax=ax, marker='.', linestyle='none', label='Detrended Folded Light Curve')
                ax.plot(x_data, model_flux, color='green', linewidth=2, label='Batman Transit Model')
                ax.set_title(f'Folded Light Curve with Transit Model for {filename.replace("_lightcurve.csv", "")}\nClassification: {classification_result}')
                ax.legend()
                plt.tight_layout()

                # Determine the mission subdirectory for saving the plot
                relative_path = os.path.relpath(file_path, input_dir)
                mission_subfolder = os.path.dirname(relative_path)

                plot_save_dir = os.path.join(output_dir, mission_subfolder)
                os.makedirs(plot_save_dir, exist_ok=True)

                plot_filename = os.path.join(plot_save_dir, filename.replace(".csv", ".png"))
                plt.savefig(plot_filename)
                print(f"Plot generated for {filename} and saved to {plot_save_dir}/\n")
                plt.close(fig)

            except KeyboardInterrupt:
                print(f"Analysis interrupted by user for {filename}.\n")
                break
            except Exception as e:
                print(f"Skipped {filename}. Error: {e}\n")
                continue

print("--- Analysis complete for all available light curves. ---\n")
