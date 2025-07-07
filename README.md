# Finding-Classifying-Analysing-Exoplanets

## Overview
This project provides code to analyze light curve data from the MAST database using the `lightkurve` module. The primary goal is to process stellar light curves to identify and characterize potential exoplanets.

## Getting Started

### 1. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage project dependencies. This prevents conflicts with your system's Python packages.

```bash
python3 -m venv env
source env/bin/activate
```

### 2. Install Required Python Modules
With your virtual environment activated, install the necessary libraries using pip:

```bash
pip install pandas numpy lightkurve matplotlib
```

### 3. Run the Lightcurve Analysis Module
The core lightcurve analysis is performed by the `Lightkurve_ExoplanetProject_Array_Solved.py` script. This script will read data from `LightCurves/StarData_1.csv`, process it, and save the output (folded lightcurve data and plots) into the `LightCurves/export/` directory.

To run the script, ensure your virtual environment is activated and execute the following command from the project's root directory:

```bash
python LightCurves/Lightkurve_ExoplanetProject_Array_Solved.py
```

### Note on the Verifying Module
The `Verifying` module, which contains code for classifying exoplanets using neural networks, is currently out of scope for these instructions. You can explore it separately if needed.