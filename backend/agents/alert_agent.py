from backend.agents.base_agent import BaseAgent, PatientState
import logging

logger = logging.getLogger("IMDCS_AlertAgent")

class AlertAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="Alert_Agent")
        # قاموس لمتابعة عدد القراءات لكل مريض منذ آخر تنبيه أُرسل له
        self.patient_tracks = {}
        # عدد القراءات التي يجب انتظارها قبل السماح بإرسال تنبيه جديد (Cooldown Window)
        # 4 قراءات تعني منع التنبيهات المتتالية المزعجة لمدة 20 دقيقة فسيولوجية تقريباً
        self.COOLDOWN_READINGS_COUNT = 4 

    async def process(self, state: PatientState) -> PatientState:
        """
        يتحكم في فلترة وإصدار التنبيهات النهائية ومنع إزعاج المريض (Alarm Fatigue Suppression).
        """
        pid = state.patient_id
        decision = state.final_decision
        
        # إذا كان المريض جديداً، نضع عداداً مرتفعاً للسماح بأول تنبيه فوراً
        if pid not in self.patient_tracks:
            self.patient_tracks[pid] = {"readings_since_last_alert": 99}
            
        self.patient_tracks[pid]["readings_since_last_alert"] += 1

        # التحقق مما إذا كان القرار الحالي يتطلب تنبيهاً حرجاً أو تحذيراً
        if decision.get("action_required") and decision.get("notification_type") in ["URGENT_ALERT", "WARNING"]:
            # إذا كان عدد القراءات منذ آخر تنبيه أقل من فترة الانتظار (Cooldown)
            if self.patient_tracks[pid]["readings_since_last_alert"] < self.COOLDOWN_READINGS_COUNT:
                # حجب التنبيه ووسمه بكائن الـ State لمنع الـ Alarm Fatigue
                state.final_decision["action_required"] = False
                state.final_decision["is_suppressed_by_agent"] = True
                logger.info(f"==> [Alert Agent] Alert suppressed for Patient {pid} to prevent Alarm Fatigue.")
            else:
                # مسموح بإطلاق التنبيه فسيولوجياً، نعيد تصفير العداد للمريض
                self.patient_tracks[pid]["readings_since_last_alert"] = 0
                state.final_decision["is_suppressed_by_agent"] = False
        else:
            state.final_decision["is_suppressed_by_agent"] = False

        return state