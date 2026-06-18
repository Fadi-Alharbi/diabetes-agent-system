"""
IMDCS Core Engine — FastAPI Backend
====================================
النسخة المتكاملة مع الحساس الافتراضي المدمج وخط أنابيب الوكلاء الشامل.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uvicorn
import logging
import asyncio

from backend.core.state import PatientState
from backend.core.workflow import app_graph
from backend.services.virtual_sensor import sensor_manager, VirtualCGMSensor
from simulator.patient_profiles import get_profile, get_all_profiles, PATIENT_PROFILES

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("IMDCS_Main")

app = FastAPI(
    title="Intelligent Multi-Agent Diabetes Care System (IMDCS)",
    version="3.0.0",
    description="Research & Production Ready Multi-Agent Diabetes Core Engine with Embedded Virtual CGM Sensor"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════
#  Pipeline Callback — يُنفَّذ لكل قراءة من الحساس
# ═══════════════════════════════════════════════════════════════

def run_agent_pipeline(
    patient_id: str,
    reading: dict,
    history: list,
    events: list,
    profile_type: str = "unknown"
) -> dict:
    """
    ينفّذ خط أنابيب الوكلاء (LangGraph) لقراءة واحدة.
    يُستدعى من الحساس الافتراضي أو من الـ REST API.
    """
    initial_state = {
        "patient_id": patient_id,
        "profile_type": profile_type,
        "current_reading": reading,
        "historical_readings": history[-50:],  # آخر 50 قراءة
        "recent_events": events[-20:],         # آخر 20 حدث
        "computed_trend": "",
        "glucose_velocity": 0.0,
        "time_in_range_percent": 0.0,
        "predicted_glucose_30m": None,
        "predicted_glucose_60m": None,
        "predicted_glucose_120m": None,
        "prediction_confidence": "LOW",
        "prediction_narrative_ar": "",
        "prediction_narrative_en": "",
        "risk_level": "LOW",
        "behavioral_insights": [],
        "food_impact_updates": [],
        "patient_advice": {},
        "action_steps": [],
        "severity_explanation": "",
        "prevention_tips": [],
        "next_meal_suggestion": "",
        "final_decision": {},
        "shap_explanations": {}
    }
    
    try:
        final_state = app_graph.invoke(initial_state)
        return final_state
    except Exception as e:
        logger.error(f"Pipeline error for {patient_id}: {e}")
        return initial_state


# ═══════════════════════════════════════════════════════════════
#  Startup Event — تشغيل الحساسات الافتراضية
# ═══════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """عند بدء السيرفر: إنشاء وتشغيل الحساسات الافتراضية للمرضى الخمسة"""
    logger.info("═" * 60)
    logger.info("  IMDCS Core Engine v3.0 — Starting Up")
    logger.info("═" * 60)
    
    # تعيين خط الأنابيب
    sensor_manager.set_pipeline(run_agent_pipeline)
    
    # إنشاء حساسات للمرضى الخمسة
    for pid, profile in PATIENT_PROFILES.items():
        sensor_manager.create_sensor(pid, profile)
        logger.info(f"  ✅ Created sensor for Patient {pid} ({profile['profile_type']})")
    
    # تشغيل جميع الحساسات (كل 3 ثوانٍ)
    sensor_manager.start_all(interval_sec=3.0)
    logger.info("")
    logger.info("  🚀 All 5 virtual sensors are now streaming!")
    logger.info("═" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """عند إيقاف السيرفر: إيقاف جميع الحساسات"""
    sensor_manager.stop_all()
    logger.info("🛑 All sensors stopped.")


# ═══════════════════════════════════════════════════════════════
#  REST API Endpoints
# ═══════════════════════════════════════════════════════════════

# --- Root ---
@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": "IMDCS Core Engine v3.0",
        "framework": "LangGraph + Embedded Virtual CGM Sensor",
        "supported_agents": [
            "DataAgent", "TrendAgent", "PredictionAgent (EWMA)",
            "FoodImpactAgent", "BehaviorAgent", "RiskAgent",
            "RecommendationAgent (Comprehensive Bilingual)"
        ],
        "active_sensors": len([s for s in sensor_manager.sensors.values() if s.is_running]),
        "total_patients": len(sensor_manager.sensors)
    }


# --- Sensor Management ---
@app.get("/sensor/status")
def get_all_sensor_status():
    """جلب حالة جميع الحساسات"""
    return {
        "sensors": sensor_manager.get_all_statuses(),
        "total": len(sensor_manager.sensors),
        "active": len([s for s in sensor_manager.sensors.values() if s.is_running])
    }


@app.get("/sensor/{patient_id}/status")
def get_sensor_status(patient_id: str):
    """جلب حالة حساس مريض محدد"""
    sensor = sensor_manager.get_sensor(patient_id)
    if not sensor:
        raise HTTPException(404, f"Sensor for patient {patient_id} not found")
    return sensor.get_status()


@app.post("/sensor/start/{patient_id}")
async def start_sensor(patient_id: str, interval_sec: float = 3.0):
    """تشغيل حساس لمريض"""
    sensor = sensor_manager.get_sensor(patient_id)
    if not sensor:
        # Create a new sensor with default profile
        profile = get_profile(patient_id)
        sensor = sensor_manager.create_sensor(patient_id, profile)
    
    sensor.start(run_agent_pipeline, interval_sec)
    return {"status": "started", "patient_id": patient_id}


@app.post("/sensor/stop/{patient_id}")
async def stop_sensor(patient_id: str):
    """إيقاف حساس لمريض"""
    sensor = sensor_manager.get_sensor(patient_id)
    if not sensor:
        raise HTTPException(404, f"Sensor for patient {patient_id} not found")
    sensor.stop()
    return {"status": "stopped", "patient_id": patient_id}


@app.post("/sensor/event/{patient_id}")
async def inject_sensor_event(
    patient_id: str,
    event_type: str,
    carbs_g: Optional[int] = None,
    food_name: Optional[str] = None,
    units: Optional[int] = None,
    duration_min: Optional[int] = None,
    intensity: Optional[float] = None
):
    """حقن حدث سلوكي في حساس مريض"""
    sensor = sensor_manager.get_sensor(patient_id)
    if not sensor:
        raise HTTPException(404, f"Sensor for patient {patient_id} not found")
    
    details = {}
    if event_type == "meal":
        details = {"carbs_g": carbs_g or 60, "food_name": food_name or "Meal"}
    elif event_type == "insulin":
        details = {"units": units or 5}
    elif event_type == "exercise":
        details = {"duration_min": duration_min or 30, "intensity": intensity or 1.0}
    
    sensor.inject_event(event_type, details)
    return {"status": "event_injected", "event_type": event_type, "details": details}


# --- Patient Dashboard ---
@app.get("/patients/{patient_id}/dashboard")
async def get_dashboard(patient_id: str):
    """جلب بيانات لوحة التحكم الكاملة لمريض (للـ React frontend)"""
    sensor = sensor_manager.get_sensor(patient_id)
    if not sensor:
        return {"status": "no_data", "patient_id": patient_id}
    
    return sensor.get_dashboard_data()


@app.get("/patients/{patient_id}/full-analysis")
async def get_full_analysis(patient_id: str):
    """جلب التحليل الكامل مع النصائح الطبية المفصّلة"""
    sensor = sensor_manager.get_sensor(patient_id)
    if not sensor:
        raise HTTPException(404, f"Patient {patient_id} not found")
    
    latest = sensor.latest_analysis
    dashboard = sensor.get_dashboard_data()
    
    return {
        "dashboard": dashboard,
        "full_analysis": {
            "patient_advice": latest.get("patient_advice", {}),
            "action_steps": latest.get("action_steps", []),
            "severity_explanation": latest.get("severity_explanation", ""),
            "prevention_tips": latest.get("prevention_tips", []),
            "next_meal_suggestion": latest.get("next_meal_suggestion", ""),
            "prediction_narrative_ar": latest.get("prediction_narrative_ar", ""),
            "prediction_narrative_en": latest.get("prediction_narrative_en", ""),
            "prediction_confidence": latest.get("prediction_confidence", ""),
            "food_impact_updates": latest.get("food_impact_updates", []),
            "behavioral_insights": latest.get("behavioral_insights", []),
        }
    }


@app.get("/patients/all/overview")
async def get_all_patients_overview():
    """نظرة عامة على جميع المرضى"""
    overview = []
    for pid, sensor in sensor_manager.sensors.items():
        data = sensor.get_dashboard_data()
        overview.append({
            "patient_id": pid,
            "name": data.get("name", ""),
            "name_ar": data.get("name_ar", ""),
            "glucose": data.get("glucose"),
            "risk": data.get("risk"),
            "riskClass": data.get("riskClass"),
            "trend": data.get("trendText"),
            "tir": data.get("tir"),
            "status": data.get("status"),
            "profile_type": data.get("profile_type"),
        })
    return {"patients": overview}


# --- Legacy Manual Stream (backward compatibility) ---
class GlucoseReading(BaseModel):
    patient_id: str
    timestamp: datetime
    glucose_value: float

class BehavioralEvent(BaseModel):
    patient_id: str
    timestamp: datetime
    event_type: str
    details: Dict[str, Any]


@app.post("/glucose/stream")
async def receive_glucose_stream(reading: GlucoseReading):
    """Legacy endpoint for manual glucose streaming"""
    result = run_agent_pipeline(
        patient_id=reading.patient_id,
        reading=reading.model_dump(),
        history=[],
        events=[],
        profile_type="manual"
    )
    
    return {
        "status": "success",
        "patient_id": result["patient_id"],
        "timestamp": reading.timestamp,
        "current_glucose": reading.glucose_value,
        "analysis": {
            "computed_trend": result["computed_trend"],
            "velocity": result["glucose_velocity"],
            "predicted_glucose_30m": result["predicted_glucose_30m"],
            "predicted_glucose_60m": result["predicted_glucose_60m"],
            "predicted_glucose_120m": result["predicted_glucose_120m"],
            "risk_level": result["risk_level"],
            "behavioral_insights": result["behavioral_insights"],
            "food_impact_updates": result["food_impact_updates"]
        },
        "advice": {
            "patient_advice": result.get("patient_advice", {}),
            "action_steps": result.get("action_steps", []),
            "severity_explanation": result.get("severity_explanation", ""),
            "prevention_tips": result.get("prevention_tips", []),
            "next_meal_suggestion": result.get("next_meal_suggestion", ""),
            "prediction_narrative_ar": result.get("prediction_narrative_ar", ""),
            "prediction_narrative_en": result.get("prediction_narrative_en", ""),
        },
        "decision": result["final_decision"]
    }


@app.post("/glucose/event")
async def record_behavioral_event(event: BehavioralEvent):
    """Legacy endpoint for recording behavioral events"""
    sensor = sensor_manager.get_sensor(event.patient_id)
    if sensor:
        sensor.inject_event(event.event_type, event.details)
    
    return {
        "status": "event_recorded",
        "patient_id": event.patient_id,
        "event_type": event.event_type,
    }


# ═══════════════════════════════════════════════════════════════
#  WebSocket — البث الحي
# ═══════════════════════════════════════════════════════════════

@app.websocket("/ws/live/{patient_id}")
async def websocket_live(websocket: WebSocket, patient_id: str):
    """WebSocket endpoint for live glucose streaming"""
    await websocket.accept()
    
    sensor = sensor_manager.get_sensor(patient_id)
    if not sensor:
        await websocket.send_json({"error": f"Patient {patient_id} not found"})
        await websocket.close()
        return
    
    sensor.add_subscriber(websocket)
    logger.info(f"WebSocket client connected for patient {patient_id}")
    
    try:
        while True:
            # Keep connection alive, receive any client messages
            data = await websocket.receive_text()
            # Client can send events through WebSocket too
            if data:
                import json
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "inject_event":
                        sensor.inject_event(
                            msg.get("event_type", "meal"),
                            msg.get("details", {})
                        )
                except Exception:
                    pass
    except WebSocketDisconnect:
        sensor.remove_subscriber(websocket)
        logger.info(f"WebSocket client disconnected for patient {patient_id}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)