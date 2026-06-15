from backend.agents.base_agent import BaseAgent, PatientState
from backend.models.glucose import GlucoseReading
import numpy as np

class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="Data_Agent")
        # النطاق الطبيعي العالمي للسكر لمريض السكري (Target Range)
        self.TARGET_LOW = 70.0
        self.TARGET_HIGH = 180.0

    async def process(self, state: PatientState) -> PatientState:
        """
        يقوم بتنظيف القراءات وحساب المقاييس الإحصائية الحيوية مثل Time in Range
        """
        # 1. التحقق من سلامة القراءة الحالية (Sanity Check)
        current_val = state.current_reading.glucose_value
        if current_val < 30.0 or current_val > 500.0:
            # وسم القراءة كقراءة مشكوك فيها أو تحتاج فلترة في الـ metrics
            state.metrics["data_anomaly_detected"] = True
            # كإجراء حمائي، لا نوقف النظام بل نضع تنبيه علمي
        else:
            state.metrics["data_anomaly_detected"] = False

        # 2. حساب الـ Time in Range (TIR) إذا توفرت قراءات تاريخية كافية
        all_readings = state.historical_readings + [state.current_reading]
        glucose_values = [r.glucose_value for r in all_readings if 30.0 <= r.glucose_value <= 500.0]

        if glucose_values:
            in_range = sum(1 for v in glucose_values if self.TARGET_LOW <= v <= self.TARGET_HIGH)
            tir_percentage = (in_range / len(glucose_values)) * 100
            
            state.metrics["time_in_range_pct"] = round(tir_percentage, 2)
            state.metrics["mean_glucose"] = round(float(np.mean(glucose_values)), 2)
            state.metrics["glucose_variability_sd"] = round(float(np.std(glucose_values)), 2) if len(glucose_values) > 1 else 0.0
        else:
            state.metrics["time_in_range_pct"] = 100.0
            state.metrics["mean_glucose"] = current_val
            state.metrics["glucose_variability_sd"] = 0.0

        return state