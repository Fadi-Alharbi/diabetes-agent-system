from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

class GlucoseReadingDict(TypedDict):
    timestamp: datetime
    glucose_value: float

class BehavioralEventDict(TypedDict):
    timestamp: datetime
    event_type: str
    details: Dict[str, Any]

class PatientState(TypedDict):
    patient_id: str
    profile_type: str
    
    # Inputs
    current_reading: GlucoseReadingDict
    historical_readings: List[GlucoseReadingDict]
    recent_events: List[BehavioralEventDict]
    
    # Extracted / Computed metrics
    computed_trend: str
    glucose_velocity: float
    time_in_range_percent: float
    
    # Predictions
    predicted_glucose_30m: Optional[float]
    predicted_glucose_60m: Optional[float]
    predicted_glucose_120m: Optional[float]
    prediction_confidence: str           # LOW, MEDIUM, HIGH
    prediction_narrative_ar: str         # سرد التنبؤ بالعربية
    prediction_narrative_en: str         # Prediction narrative in English
    
    # Analysis & Insights
    risk_level: str
    behavioral_insights: List[str]
    food_impact_updates: List[Dict[str, Any]]
    
    # --- NEW: Comprehensive Patient Advice ---
    patient_advice: Dict[str, Any]       # النصائح الطبية المفصّلة للمريض
    action_steps: List[str]              # خطوات عملية مرقّمة
    severity_explanation: str            # شرح مبسّط لمستوى الخطورة
    prevention_tips: List[str]           # نصائح وقائية
    next_meal_suggestion: str            # اقتراح الوجبة القادمة
    
    # Outputs
    final_decision: Dict[str, Any]
    shap_explanations: Dict[str, Any]
