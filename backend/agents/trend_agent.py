from backend.agents.base_agent import BaseAgent, PatientState
from datetime import datetime

class TrendAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="Trend_Agent")

    async def process(self, state: PatientState) -> PatientState:
        """
        يحسب اتجاه حركة السكر (Rising, Falling, Stable) بناءً على مشتقة التغير اللحظي dP/dt
        """
        history = state.historical_readings
        
        # نحتاج على الأقل قراءتين سابقتين لحساب الاتجاه بشكل مستقر (آخر 15 دقيقة تقريباً)
        if len(history) < 2:
            state.computed_trend = "STABLE"
            state.metrics["glucose_velocity"] = 0.0
            return state

        # جلب آخر قراءة من التاريخ والمقارنة مع الحالية
        last_reading = history[-1]
        
        # حساب الفارق اللحظي (mg/dL لكل دقيقة)
        time_diff_mins = (state.current_reading.timestamp - last_reading.timestamp).total_seconds() / 60.0
        
        # حماية ضد القسمة على صفر في حال تدفق بيانات خاطئ بنفس الطابع الزمني
        if time_diff_mins <= 0:
            time_diff_mins = 5.0 

        glucose_diff = state.current_reading.glucose_value - last_reading.glucose_value
        velocity = glucose_diff / time_diff_mins # mg/dL per minute
        
        state.metrics["glucose_velocity"] = round(velocity, 2)

        # التصنيف الطبي المعتمد للاتجاهات بناءً على السرعة (Velocity)
        if velocity > 2.0:
            state.computed_trend = "RAPIDLY_RISING"
        elif velocity > 1.0:
            state.computed_trend = "RISING"
        elif velocity < -2.0:
            state.computed_trend = "RAPIDLY_FALLING"
        elif velocity < -1.0:
            state.computed_trend = "FALLING"
        else:
            state.computed_trend = "STABLE"

        return state