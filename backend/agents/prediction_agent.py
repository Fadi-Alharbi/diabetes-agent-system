from backend.agents.base_agent import BaseAgent, PatientState
import logging

logger = logging.getLogger("IMDCS_PredictionAgent")

class PredictionAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="Prediction_Agent")
        # أفق التنبؤ الطبي القياسي (30 دقيقة)
        self.PREDICTION_HORIZON_MINS = 30.0

    async def process(self, state: PatientState) -> PatientState:
        current_glucose = state.current_reading.glucose_value
        velocity = state.metrics.get("glucose_velocity", 0.0)

        # إضافة معامل كبح (Damping Factor = 0.5) لحماية التنبؤ الخطي من القفزات اللحظية الحادة
        # P(t + Δt) = G(t) + (v * Δt * damping)
        damping_factor = 0.5
        predicted_value = current_glucose + (velocity * self.PREDICTION_HORIZON_MINS * damping_factor)

        state.metrics["prediction_method"] = "Damped_Linear_Extrapolation"

        # حماية الحدود الفسيولوجية للتنبؤ
        predicted_value = max(40.0, min(predicted_value, 450.0))
        state.predicted_glucose_30m = round(predicted_value, 1)
        
        return state