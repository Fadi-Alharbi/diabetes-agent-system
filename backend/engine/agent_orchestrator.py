from backend.agents.base_agent import PatientState
from backend.agents.data_agent import DataAgent
from backend.agents.trend_agent import TrendAgent
from backend.agents.prediction_agent import PredictionAgent
from backend.agents.behavior_agent import BehaviorAgent
from backend.agents.risk_agent import RiskAgent
from backend.engine.decision_engine import DecisionEngine
from backend.agents.alert_agent import AlertAgent  # استيراد وكيل التنبيهات الذكي
import logging

# إعداد الـ Logger الخاص بالمحرك لتتبع التدفق الفسيولوجي بدقة
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IMDCS_Orchestrator")

class AgentOrchestrator:
    def __init__(self):
        """
        تهيئة وإعداد جميع الوكلاء السبعة (Core Analytic Agents + Meta-Agent)
        يتم الاحتفاظ بالكائنات في الذاكرة لضمان السرعة العالية وعدم إهلاك الموارد.
        """
        self.data_agent = DataAgent()
        self.trend_agent = TrendAgent()
        self.prediction_agent = PredictionAgent()
        self.behavior_agent = BehaviorAgent()
        self.risk_agent = RiskAgent()
        self.decision_engine = DecisionEngine()
        self.alert_agent = AlertAgent()  # تهيئة وكيل إدارة الإشعارات والـ Cooldown

    async def route_and_execute(self, state: PatientState) -> PatientState:
        """
        الـ Core Execution Pipeline:
        إدارة وتوجيه البيانات الطبية الحية عبر سلسلة من الوكلاء الأذكياء وحتى اتخاذ القرار النهائي والتحكم في إرساله.
        """
        logger.info(f"==> [Orchestrator] Starting Multi-Agent pipeline for Patient ID: {state.patient_id}")
        
        try:
            # 1. وكيل البيانات (التنظيف، فحص العينات، وحساب الـ TIR)
            state = await self.data_agent.process(state)
            
            # 2. وكيل الاتجاهات (حساب مشتقة التغير اللحظي والسرعة الحركية dP/dt)
            state = await self.trend_agent.process(state)
            
            # 3. وكيل التنبؤ (استشراف المستقبل القريب 30 دقيقة بمعامل كبح ذكي)
            state = await self.prediction_agent.process(state)
            
            # 4. وكيل السلوك (الربط السببي والتفسيري مع الكربوهيدرات والنشاط البدني والإنسولين)
            state = await self.behavior_agent.process(state)
            
            # 5. وكيل المخاطر (التصنيف الأمني لخطورة الحالة فسيولوجياً)
            state = await self.risk_agent.process(state)
            
            # 6. محرك القرار الـ Meta-Agent (صياغة التوجيه والتعليل المشروح الطبي بالكامل)
            logger.info("Executing: Decision_Engine (Meta-Agent Reasoning)...")
            state = await self.decision_engine.process(state)
            
            # 7. وكيل التنبيهات (كبح الـ Alarm Fatigue ومنع تكرار الإشعارات المتطابقة إلا بعد فترة Cooldown آمنة)
            logger.info("Executing: Alert_Agent (Alarm Fatigue Suppression)...")
            state = await self.alert_agent.process(state)
            
            # توثيق المخرجات النهائية النظيفة بعد انتهاء خط المعالجة
            logger.info(
                f"==> [Orchestrator] Core Pipeline Completed Successfully for: {state.patient_id} |\n"
                f"    [Glucose: {state.current_reading.glucose_value}] -> [Trend: {state.computed_trend}] -> [Predicted: {state.predicted_glucose_30m}] |\n"
                f"    [Risk Level: {state.risk_level}] -> [Alert Type: {state.final_decision['notification_type']}] |\n"
                f"    [Is Suppressed? {state.final_decision.get('is_suppressed_by_agent')}] -> [Guidance: {state.final_decision['clinical_guidance']}]"
            )
            
        except Exception as e:
            # عزل الأخطاء لضمان استقرار السيرفر الطبي في حال حدوث مشكلة برمجية مفاجئة
            logger.error(f"![Orchestrator Error] Failed to execute pipeline for patient {state.patient_id}: {str(e)}")
            raise e
            
        return state