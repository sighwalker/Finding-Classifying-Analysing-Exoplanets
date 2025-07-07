#!/usr/bin/env python3
import lightkurve as lk
import pandas as pd
import os
import shutil

def download_and_save_lightcurve(target_name, base_output_dir='/home/sighw/codes/Finding-Classifying-Analysing-Exoplanets/lightScript/export'):
    """
    Searches for and downloads ALL light curve data for a given target star
    using lightkurve, then saves each light curve's time and flux to a separate CSV file
    within a mission-specific subdirectory.

    Args:
        target_name (str): The name or ID of the star to search for (e.g., 'Kepler-186', 'TIC 395002097').
        base_output_dir (str): The base directory to save the downloaded light curve data.
    """
    print(f"Searching for light curves for {target_name}...")
    try:
        search_result = lk.search_lightcurve(target_name)

        if not search_result:
            print(f"No light curves found for {target_name}. Please check the name/ID and try again.")
            return

        print(f"Found {len(search_result)} light curves. Downloading all of them...")
        lcs = search_result.download_all()

        if lcs is None or len(lcs) == 0:
            print(f"Failed to download any light curves for {target_name}.")
            return

        # Ensure the base output directory exists
        os.makedirs(base_output_dir, exist_ok=True)

        print(f"Saving {len(lcs)} light curves...")
        for i, lc in enumerate(lcs):
            if lc is None:
                print(f"Skipping empty light curve {i+1}/{len(lcs)}.")
                continue

            # Determine the mission and create a mission-specific subdirectory
            mission = lc.meta.get('MISSION', 'UNKNOWN').replace(' ', '_')
            mission_output_dir = os.path.join(base_output_dir, mission)
            os.makedirs(mission_output_dir, exist_ok=True)

            # Generate a unique filename for each light curve
            unique_id = ""
            if hasattr(lc, 'filename') and lc.filename:
                unique_id = os.path.splitext(os.path.basename(lc.filename))[0]
            else:
                campaign_info = ""
                if 'QUARTER' in lc.meta:
                    campaign_info = f"Q{lc.meta['QUARTER']}"
                elif 'SECTOR' in lc.meta:
                    campaign_info = f"S{lc.meta['SECTOR']}"
                elif 'CAMPAIGN' in lc.meta:
                    campaign_info = f"C{lc.meta['CAMPAIGN']}"
                unique_id = f"{mission}_{campaign_info}_{lc.targetid}"

            clean_target_name = target_name.replace(' ', '_').replace('-', '_')

            output_filename = os.path.join(mission_output_dir, f"{clean_target_name}_{unique_id}_lightcurve.csv")

            lc_df = pd.DataFrame({
                'time': lc.time.value,
                'flux': lc.flux.value
            })

            lc_df.to_csv(output_filename, index=False)
            print(f"  Saved {os.path.basename(output_filename)} to {mission_output_dir}")

        print(f"Successfully saved all {len(lcs)} light curves for {target_name}.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    predefined_targets = [
        "Kepler-186",
        "TRAPPIST-1",
        "KIC 8462852", # Boyajian's Star
        "TIC 395002097", # A TESS target
        "WASP-12b"
    ]

    print("\n--- Light Curve Downloader ---")
    print("Choose a star from the list below, or enter your own:")
    for i, target in enumerate(predefined_targets):
        print(f"{i+1}. {target}")
    print("0. Enter a custom star name/ID")

    while True:
        choice = input(f"Enter your choice (0-{len(predefined_targets)}): ")
        try:
            choice_int = int(choice)
            if choice_int == 0:
                target = input("Enter custom star name/ID: ")
                if target:
                    break
                else:
                    print("Custom target cannot be empty. Please try again.")
            elif 1 <= choice_int <= len(predefined_targets):
                target = predefined_targets[choice_int - 1]
                break
            else:
                print("Invalid choice. Please enter a number within the range.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    if target:
        download_and_save_lightcurve(target_name=target)
    else:
        print("No target selected. Exiting.")