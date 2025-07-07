import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
features_path = os.path.join(script_dir, 'exoplanetFeatures.csv')
labels_path = os.path.join(script_dir, 'exoplanetLabels.csv')
model_save_path = os.path.join(script_dir, 'random_forest_exoplanet_classifier.joblib')

print("--- Training Advanced Exoplanet Classifier (Random Forest) ---")

# Load data
try:
    features_df = pd.read_csv(features_path)
    labels_df = pd.read_csv(labels_path)
except FileNotFoundError:
    print(f"Error: Make sure {features_path} and {labels_path} exist.")
    exit()

# Define the specific features to use for training
# Corrected column names to match exoplanetFeatures.csv exactly
selected_features = [
    'OrbitalPeriod[days',
    'TransitDepth[ppm',
    'TransitDuration[hrs',
    'ImpactParamete',
    'PlanetaryRadius[Earthradii',
    'TransitSignal-to-Nois'
]

# Select only the desired features
X = features_df[selected_features]
y = labels_df.iloc[:, 0] # Assuming the first column is the label

# Handle missing values (NaNs) - crucial for StandardScaler
# For simplicity, we'll fill NaNs with the mean of the column.
# A more robust approach might involve imputation or dropping rows/columns.
X = X.fillna(X.mean())

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create a pipeline with StandardScaler and RandomForestClassifier
print("Training RandomForestClassifier model with StandardScaler pipeline...")
model = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
])

model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print(f"Model Accuracy: {accuracy:.2f}")
print("Classification Report:")
print(report)

# Save the trained model
joblib.dump(model, model_save_path)
print(f"Trained model saved to: {model_save_path}")

print("--- Classifier Training Complete ---")