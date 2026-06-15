from backend.agents.base_agent import BaseAgent, PatientState
from datetime import datetime, timezone
import logging

logger = logging.getLogger("IMDCS_BehaviorAgent")

class BehaviorAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="Behavior_Agent")
        # النطاق الزمني الطبي المعتبر لتأثير الأحداث القريبة (ساعتان)
        self.LOOKBACK_WINDOW_MINS = 120.0

    async def process(self, state: PatientState) -> PatientState:
        """
        يربط حركة السكر والاتجاه الحالي بالأحداث السلوكية الأخيرة (الطعام، الإنسولين، الرياضة)
        لتقديم تفسير طبي مدعوم بالسياق (Explainable AI).
        """
        state.behavioral_insights = [] # إعادة تهيئة الرؤى للقراءة الحالية
        current_time = state.current_reading.timestamp
        trend = state.computed_trend
        velocity = state.metrics.get("glucose_velocity", 0.0)

        if not state.recent_events:
            state.behavioral_insights.append("لم يتم تسجيل أي أحداث سلوكية أو حيوية مؤخراً. التغيرات قد تكون ناتجة عن عوامل هرمونية أو أساسية بالمنظم.")
            return state

        for event in state.recent_events:
            # حساب الفارق الزمني بين الحدث السلوكي والقراءة الحالية
            time_diff = (current_time - event.timestamp).total_seconds() / 60.0
            
            # معالجة الأحداث التي تقع ضمن نافذة التأثير الطبي (آخر ساعتين)
            if 0 <= time_diff <= self.LOOKBACK_WINDOW_MINS:
                if event.event_type == "meal":
                    carbs = event.details.get("carbs_g", 0)
                    if "RISING" in trend:
                        state.behavioral_insights.append(
                            f"الارتفاع الحالي متوقع نتيجة لتناول وجبة تحتوي على {carbs} جرام كربوهيدرات قبل {int(time_diff)} دقيقة."
                        )
                    elif "FALLING" in trend and time_diff > 90:
                        state.behavioral_insights.append(
                            f"بدأ مفعول الوجبة السابقة ({carbs}g كربوهيدرات) بالانحسار بعد مرور {int(time_diff)} دقيقة."
                        )

                elif event.event_type == "insulin":
                    units = event.details.get("units", 0)
                    if "FALLING" in trend:
                        state.behavioral_insights.append(
                            f"الهبوط الحالي يتماشى مع ذروة نشاط جرعة الإنسولين المحقونة ({units} وحدات) قبل {int(time_diff)} دقيقة."
                        )
                    elif "RISING" in trend and time_diff < 15:
                        state.behavioral_insights.append(
                            f"تم حقن الإنسولين مؤخراً ({units} وحدات)، لكن تأثيره الفسيولوجي يحتاج إلى 15-20 دقيقة ليبدأ في خفض السكر."
                        )

                elif event.event_type == "exercise":
                    intensity = event.details.get("intensity", "moderate")
                    if "FALLING" in trend:
                        state.behavioral_insights.append(
                            f"زيادة حساسية الخلايا للإنسولين واستهلاك الطاقة نتيجة ممارسة رياضة بجهد ({intensity}) منذ {int(time_diff)} دقيقة."
                        )

        # حالة حمائية إذا وجدت أحداث ولكن لم تطابق الاتجاه الحالي بشكل مباشر
        if not state.behavioral_insights:
            state.behavioral_insights.append("توجد أحداث مسجلة مؤخراً، ولكن المنحنى الحركي للسكر يتأثر بعوامل فيزيولوجية أخرى حالياً.")

        logger.info(f"Patient {state.patient_id} - Behavior Insights generated: {len(state.behavioral_insights)} items.")
        return state