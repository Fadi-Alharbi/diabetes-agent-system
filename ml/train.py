import pandas as pd
import numpy as np
import os
try:
    import shap
    SHAP_AVAILABLE = True
except Exception as e:
    print(f"Warning: SHAP import failed ({e}). SHAP explainability will be skipped.")
    SHAP_AVAILABLE = False
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

def create_features(df, forecast_horizon_mins=30):
    """
    Creates lag features for time series prediction.
    Assumes 5 minute intervals.
    """
    df = df.copy()
    steps_ahead = forecast_horizon_mins // 5
    
    # Lag features
    for i in range(1, 7): # up to 30 mins lag
        df[f'glucose_lag_{i}'] = df['glucose_value'].shift(i)
        
    # Velocity (first derivative)
    df['velocity'] = df['glucose_value'] - df['glucose_lag_1']
    
    # Target
    df['target'] = df['glucose_value'].shift(-steps_ahead)
    
    df = df.dropna()
    return df

def evaluate_models(file_path):
    print(f"\n--- Evaluating models on {file_path} ---")
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Prepare data for 30 min prediction
    df_features = create_features(df, forecast_horizon_mins=30)
    
    features = [col for col in df_features.columns if col.startswith('glucose_lag') or col == 'velocity']
    X = df_features[features]
    y = df_features['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
        "XGBoost": xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    }
    
    results = {}
    best_model = None
    best_mae = float('inf')
    
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        
        results[name] = {"MAE": mae, "RMSE": rmse}
        print(f"{name} - MAE: {mae:.2f}, RMSE: {rmse:.2f}")
        
        if mae < best_mae:
            best_mae = mae
            best_model = (name, model)
            
    print(f"Best Model: {best_model[0]}")
    
    # SHAP Explainability for best model
    # Note: Using a sample for SHAP to avoid long computation times in training script
    if SHAP_AVAILABLE and best_model[0] in ["Random Forest", "XGBoost"]:
        try:
            explainer = shap.TreeExplainer(best_model[1])
            shap_values = explainer.shap_values(X_test.iloc[:100])
            print(f"Generated SHAP values for top 100 test samples. Shape: {shap_values.shape}")
        except Exception as e:
            print(f"Failed to generate SHAP values: {e}")
        
    return best_model[1]

if __name__ == "__main__":
    # If the generator has finished, we can train on one of the datasets
    if os.path.exists('dataset_patient_A_high_carb.csv'):
        evaluate_models('dataset_patient_A_high_carb.csv')
    else:
        print("Dataset not found. Run simulator generator first.")
