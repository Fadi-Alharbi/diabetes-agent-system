from fastapi import FastAPI, HTTPException
from backend.models.glucose import GlucoseReading, BehavioralEvent
from backend.agents.base_agent import PatientState
from backend.engine.agent_orchestrator import AgentOrchestrator
from typing import Dict, List
import uvicorn

app = FastAPI(
    title="Intelligent Multi-Agent Diabetes Care System (IMDCS)",
    version="1.0.0",
    description="Research & Production Ready Multi-Agent Diabetes Core Engine"
)

# الذاكرة الحية للمريض (محاكاة لقاعدة البيانات في الرام لمنع التعقيد حالياً)
db_glucose_history: Dict[str, List[GlucoseReading]] = {}
db_event_history: Dict[str, List[BehavioralEvent]] = {}

# تهيئة المايسترو (Orchestrator)
orchestrator = AgentOrchestrator()

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "system": "IMDCS Core Engine",
        "supported_agents": ["Data", "Trend", "Prediction", "Behavior", "Risk", "Decision_Meta_Agent"]
    }

@app.post("/glucose/stream")
async def receive_glucose_stream(reading: GlucoseReading):
    """
    نقطة الدخول الرئيسية (Live Ingestion Endpoint) لاستقبال قراءات الـ CGM اللحظية
    """
    pid = reading.patient_id
    
    # 1. تهيئة السجلات في الذاكرة للمريض الجديد
    if pid not in db_glucose_history:
        db_glucose_history[pid] = []
    if pid not in db_event_history:
        db_event_history[pid] = []
        
    historical_data = db_glucose_history[pid]
    recent_events = db_event_history[pid]
    
    # 2. بناء كائن الـ Shared State الموحد وضخ البيانات الحالية فيه
    current_state = PatientState(
        patient_id=pid,
        current_reading=reading,
        historical_readings=list(historical_data), # إرسال نسخة من التاريخ للوكلاء
        recent_events=list(recent_events)
    )
    
    # 3. إطلاق الـ Multi-Agent Pipeline للمعالجة واتخاذ القرار فوراً
    processed_state = await orchestrator.route_and_execute(current_state)
    
    # 4. حفظ القراءة الحالية في الذاكرة التاريخية للمرة القادمة
    db_glucose_history[pid].append(reading)
    
    # 5. إرجاع استجابة JSON طبية شاملة (تصلح للـ Frontend أو النشر البحثي كـ Output Sample)
    return {
        "status": "success",
        "patient_id": processed_state.patient_id,
        "timestamp": reading.timestamp,
        "current_glucose": reading.glucose_value,
        "analysis": {
            "computed_trend": processed_state.computed_trend,
            "predicted_glucose_30m": processed_state.predicted_glucose_30m,
            "risk_level": processed_state.risk_level,
            "metrics": processed_state.metrics,
            "behavioral_insights": processed_state.behavioral_insights
        },
        "decision": processed_state.final_decision
    }

@app.post("/glucose/event")
async def record_behavioral_event(event: BehavioralEvent):
    """
    تسجيل حدث سلوكي حي موازٍ (وجبة، حقن إنسولين، رياضة) لربطه فسيولوجياً بحركة السكر
    """
    pid = event.patient_id
    if pid not in db_event_history:
        db_event_history[pid] = []
        
    db_event_history[pid].append(event)
    return {
        "status": "event_recorded",
        "patient_id": pid,
        "event_type": event.event_type,
        "total_logged_events": len(db_event_history[pid])
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)