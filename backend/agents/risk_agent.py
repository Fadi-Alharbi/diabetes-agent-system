from backend.agents.base_agent import BaseAgent, PatientState
import logging

logger = logging.getLogger("IMDCS_RiskAgent")

class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="Risk_Agent")
        
        # العتبات الطبية القياسية لإدارة مخاطر السكري (mg/dL)
        self.CRITICAL_LOW = 55.0
        self.HYPO_THRESHOLD = 70.0
        self.HYPER_THRESHOLD = 250.0
        self.CRITICAL_HIGH = 300.0

    async def process(self, state: PatientState) -> PatientState:
        """
        يصنف مستوى الخطورة الحالية والمستقبلية (LOW, MEDIUM, HIGH, CRITICAL)
        بناءً على دمج الحالة اللحظية مع التنبؤ لـ 30 دقيقة القادمة.
        """
        current_val = state.current_reading.glucose_value
        predicted_val = state.predicted_glucose_30m if state.predicted_glucose_30m is not None else current_val
        
        risk = "LOW"
        
        # 1. تقييم حالات الهبوط (Hypoglycemia) - وهي الخطورة الأعلى طبياً لحركية السكر
        if current_val <= self.CRITICAL_LOW or predicted_val <= self.CRITICAL_LOW:
            risk = "CRITICAL"
        elif current_val <= self.HYPO_THRESHOLD or predicted_val <= self.HYPO_THRESHOLD:
            risk = "HIGH"
            
        # 2. تقييم حالات الارتفاع (Hyperglycemia)
        elif current_val >= self.CRITICAL_HIGH or predicted_val >= self.CRITICAL_HIGH:
            risk = "CRITICAL"
        elif current_val >= self.HYPER_THRESHOLD or predicted_val >= self.HYPER_THRESHOLD:
            risk = "HIGH"
            
        # 3. تقييم التغيرات السريعة الحادة حتى لو كانت الأرقام داخل النطاق مؤقتاً
        else:
            velocity = state.metrics.get("glucose_velocity", 0.0)
            if abs(velocity) > 2.0: # تغير أسرع من 2 mg/dL في الدقيقة
                risk = "MEDIUM"
            else:
                risk = "LOW"

        # حفظ النتيجة في الـ Shared State
        state.risk_level = risk
        
        logger.info(f"Patient {state.patient_id} - Risk Level Evaluated: [{state.risk_level}] (Current: {current_val}, Predicted: {predicted_val})")
        return state