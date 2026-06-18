# IMDCS Research Methodology and Experimental Design

## 1. Research Objectives
Current Continuous Glucose Monitoring (CGM) systems lack contextual awareness and explainability. They rely on rigid thresholds (e.g., alert if <70 mg/dL or >250 mg/dL). The **Intelligent Multi-Agent Diabetes Care System (IMDCS)** introduces a LangGraph-based multi-agent architecture to construct dynamic, personalized behavior profiles. 

The primary objectives are:
1. To predict glucose trajectories 30, 60, and 120 minutes into the future using advanced ML models (LSTM, XGBoost).
2. To isolate the personalized glycemic impact of specific meals and activities using a novel Food Impact Agent.
3. To provide Explainable AI (SHAP) rationales for clinical guidance to prevent "alarm fatigue".

## 2. Experimental Design
The system evaluates the multi-agent approach against traditional baselines using a realistic, profile-driven in-silico CGM Simulator.

### 2.1 Virtual Cohort
Five distinct virtual patient profiles were simulated over a 30-day period at 5-minute sampling intervals (N = 8,640 readings per patient):
- **Patient A (High Carb):** Frequent high-carbohydrate meals.
- **Patient B (Highly Active):** Intensive daily exercise leading to rapid glucose drops.
- **Patient C (Hypo-Prone):** Exaggerated sensitivity to insulin, frequent nocturnal hypoglycemia.
- **Patient D (Irregular Meals):** Chaotic eating schedule.
- **Patient E (Poor Adherence):** Infrequent insulin correction and sustained hyperglycemia.

### 2.2 System Configurations Evaluated
- **System A (Traditional CGM):** Threshold-based alerting only (Baseline).
- **System B (Prediction Only):** Standard XGBoost 30-minute forecasting without behavioral context.
- **System C (IMDCS):** The full proposed Multi-Agent architecture incorporating Food Impact profiling and SHAP explanations.

### 2.3 Evaluation Metrics
- **Time In Range (TIR):** Percentage of time glucose remains between 70-180 mg/dL.
- **Prediction Accuracy:** Mean Absolute Error (MAE) and Root Mean Square Error (RMSE) for ML models.
- **False Alarm Rate:** Number of non-actionable alerts generated per day.
- **Explainability Score:** Qualitative assessment of the SHAP-generated rationale.

## 3. Machine Learning Pipeline
The `PredictionAgent` evaluates multiple models:
- **Linear Regression:** Serves as a baseline linear trend estimator.
- **Random Forest:** Captures non-linear meal/insulin interactions.
- **XGBoost:** Provides high accuracy and handles missing data effectively.
- **LSTM (Long Short-Term Memory):** Captures temporal dependencies in circadian rhythms.

XGBoost was selected as the primary inference engine due to its balance of high accuracy and computational efficiency, paired with `TreeExplainer` from the SHAP library for real-time explainability.

## 4. Publication Strategy
This architecture and the comparative results generated from the virtual cohort will be formatted for submission to peer-reviewed AI healthcare journals (e.g., *Nature Medicine*, *Journal of Biomedical Informatics*, or *IEEE Transactions on Biomedical Engineering*).
