# Finding-Classifying-Analysing-Exoplanets

## Overview
This project focuses on finding, classifying, and analyzing exoplanets. It involves advanced light curve data acquisition, sophisticated preprocessing, and machine learning for characterization.

## Getting Started

### 1. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage project dependencies. This prevents conflicts with your system's Python packages.

```bash
python3 -m venv env
source env/bin/activate
```

### 2. Install Required Python Modules
With your virtual environment activated, install the necessary libraries using pip. This project now utilizes `lightkurve`, `pandas`, `numpy`, `matplotlib`, `wotan`, `batman-package`, `scikit-learn`, and `joblib`.

```bash
pip install pandas numpy lightkurve matplotlib wotan batman-package scikit-learn joblib
```

### 3. Data Acquisition (`lightScript`)
This module handles advanced light curve data acquisition from astronomical archives. It uses `lightkurve` to search for and download all available light curves for a selected target star (e.g., Kepler, TESS missions). Downloaded CSV files are automatically organized into mission-specific subfolders within `/lightScript/export/`.

To download data, run the script and follow the prompts:

```bash
./lightScript/download_lightcurves.py
```

### 4. Light Curve Analysis and Preprocessing (`lightCurves`)
This module processes the downloaded light curve data. It performs advanced detrending using the `wotan` library to remove stellar variability and instrumental noise. It then conducts Box-Least Squares (BLS) periodogram analysis, folds the light curves, and generates plots of the folded light curves with polynomial fits. These plots are saved into organized mission-specific subfolders within `/lightCurves/analyzed_plots/`.

To run the analysis, ensure your virtual environment is activated and execute the following command from the project's root directory:

```bash
python lightCurves/analyzeLightcurves.py
```

### 5. Exoplanet Classification (`verifying`)
This module contains resources for exoplanet classification and verification. It includes `exoplanetFeatures.csv` and `exoplanetLabels.csv` as input data.

#### Training the Classifier
Before running the analysis, you need to train the exoplanet classifier. This script uses a subset of features from `exoplanetFeatures.csv` to train a Random Forest model and saves it for later use.

```bash
python verifying/train_classifier.py
```

#### Integrated Classification
The `lightCurves/analyzeLightcurves.py` script now integrates this classification. After extracting features from each light curve, it loads the trained model from `verifying/random_forest_exoplanet_classifier.joblib` and predicts whether the light curve corresponds to an "Exoplanet" or a "False Positive". The classification result is included in the output CSV and the generated plots.
