"""
الحساس الافتراضي المدمج (Embedded Virtual CGM Sensor)
=====================================================
يعمل كـ background task داخل FastAPI ويضخ القراءات مباشرة
في خط أنابيب الوكلاء بدون HTTP، مع بث حي عبر WebSocket.
"""

import asyncio
import math
import random
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict

logger = logging.getLogger("IMDCS_VirtualSensor")


class VirtualCGMSensor:
    """
    حساس CGM افتراضي يحاكي قراءات السكر الحية لمريض معين.
    يعمل في خلفية الـ event loop ويضخ النتائج مباشرة.
    """

    def __init__(self, patient_id: str, profile: dict):
        self.patient_id = patient_id
        self.profile = profile
        self.profile_type = profile.get("profile_type", "type_2")

        # Baseline glucose
        self.current_glucose = profile.get("baseline_glucose", 120.0)
        self.time_step = 0
        self.active_events: List[Dict[str, Any]] = []

        # History storage
        self.glucose_history: List[Dict[str, Any]] = []
        self.event_history: List[Dict[str, Any]] = []
        self.analysis_history: List[Dict[str, Any]] = []

        # Latest analysis from the agent pipeline
        self.latest_analysis: Dict[str, Any] = {}

        # Control
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

        # WebSocket subscribers
        self._subscribers: Set[Any] = set()

    def add_subscriber(self, ws):
        """إضافة WebSocket subscriber للبث الحي"""
        self._subscribers.add(ws)

    def remove_subscriber(self, ws):
        """إزالة subscriber"""
        self._subscribers.discard(ws)

    async def _broadcast(self, data: dict):
        """بث البيانات لكل الـ subscribers"""
        dead = set()
        for ws in self._subscribers:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self._subscribers -= dead

    def inject_event(self, event_type: str, details: dict):
        """حقن حدث سلوكي (وجبة، إنسولين، رياضة) في الحساس"""
        event = {
            "type": event_type,
            "details": details,
            "elapsed_time": 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.active_events.append(event)
        self.event_history.append({
            "patient_id": self.patient_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details
        })
        logger.info(f"[Sensor {self.patient_id}] Event injected: {event_type} -> {details}")

    def _calculate_next_glucose(self) -> float:
        """حساب القراءة التالية مع محاكاة فسيولوجية واقعية"""
        self.time_step += 1

        # الموجة اليومية (Circadian Rhythm)
        circadian_wave = 4 * math.sin(self.time_step / 6)
        noise = random.uniform(-3.0, 3.0)

        dynamic_change = 0.0
        profile = self.profile

        for event in self.active_events[:]:
            event["elapsed_time"] += 5
            t = event["elapsed_time"]

            if event["type"] == "meal":
                carbs = event["details"].get("carbs_g", 50)
                multiplier = profile.get("meal_multiplier", 1.0)
                if t <= 120:
                    dynamic_change += multiplier * (carbs / 8) * math.sin(math.pi * t / 120)
                else:
                    self.active_events.remove(event)

            elif event["type"] == "insulin":
                units = event["details"].get("units", 5)
                multiplier = profile.get("insulin_multiplier", 1.0)
                if t <= 180:
                    dynamic_change -= multiplier * (units * 2.2) * math.sin(math.pi * t / 180)
                else:
                    self.active_events.remove(event)

            elif event["type"] == "exercise":
                duration = event["details"].get("duration_min", 30)
                intensity = event["details"].get("intensity", 1.0)
                multiplier = profile.get("exercise_multiplier", 1.0)
                if t <= duration:
                    dynamic_change -= (3.0 * intensity * multiplier)
                else:
                    self.active_events.remove(event)

        self.current_glucose += circadian_wave + dynamic_change + noise
        self.current_glucose = max(35.0, min(self.current_glucose, 450.0))
        return round(self.current_glucose, 1)

    def _trigger_auto_events(self):
        """إطلاق أحداث تلقائية بناءً على ملف تعريف المريض"""
        auto = self.profile.get("auto_events", {})

        # --- Meals ---
        meal_interval = auto.get("meal_interval")
        if meal_interval == "random":
            chance = auto.get("meal_random_chance", 0.05)
            if random.random() < chance:
                carbs_range = auto.get("meal_carbs_range", [40, 80])
                carbs = random.randint(carbs_range[0], carbs_range[1])
                self.inject_event("meal", {
                    "carbs_g": carbs,
                    "food_name": auto.get("meal_food", "Snack")
                })
        elif meal_interval and self.time_step % meal_interval == 0:
            self.inject_event("meal", {
                "carbs_g": auto.get("meal_carbs", 60),
                "food_name": auto.get("meal_food", "Meal")
            })

        # --- Insulin ---
        insulin_interval = auto.get("insulin_interval")
        if insulin_interval == "random":
            chance = auto.get("insulin_random_chance", 0.025)
            if random.random() < chance:
                units_range = auto.get("insulin_units_range", [3, 6])
                units = random.randint(units_range[0], units_range[1])
                self.inject_event("insulin", {"units": units})
        elif insulin_interval and self.time_step % insulin_interval == 0:
            # Check if there's a chance factor (poor adherence)
            chance = auto.get("insulin_chance", 1.0)
            if random.random() < chance:
                self.inject_event("insulin", {
                    "units": auto.get("insulin_units", 5)
                })

        # --- Exercise ---
        exercise_interval = auto.get("exercise_interval")
        if exercise_interval and self.time_step % exercise_interval == 0:
            self.inject_event("exercise", {
                "duration_min": auto.get("exercise_duration", 30),
                "intensity": auto.get("exercise_intensity", 1.0)
            })

    async def _run_loop(self, pipeline_callback, interval_sec: float = 3.0):
        """
        حلقة القراءة الرئيسية — تعمل في الخلفية.
        pipeline_callback: دالة تُنفّذ خط الأنابيب وتعيد النتيجة
        """
        logger.info(f"🚀 [Sensor {self.patient_id}] Started — Profile: {self.profile_type}, Interval: {interval_sec}s")
        self.is_running = True

        while self.is_running:
            try:
                glucose_val = self._calculate_next_glucose()
                now = datetime.now(timezone.utc)

                reading = {
                    "patient_id": self.patient_id,
                    "timestamp": now.isoformat(),
                    "glucose_value": glucose_val
                }

                # حفظ القراءة في التاريخ
                self.glucose_history.append(reading)

                # تنفيذ خط أنابيب الوكلاء
                if pipeline_callback:
                    try:
                        result = await asyncio.to_thread(
                            pipeline_callback,
                            self.patient_id,
                            reading,
                            self.glucose_history.copy(),
                            self.event_history.copy(),
                            self.profile_type
                        )
                        self.latest_analysis = result
                        self.analysis_history.append(result)

                        # Keep only last 500 analyses
                        if len(self.analysis_history) > 500:
                            self.analysis_history = self.analysis_history[-500:]
                    except Exception as e:
                        logger.error(f"[Sensor {self.patient_id}] Pipeline error: {e}")

                # بث البيانات الحية
                broadcast_data = {
                    "type": "glucose_update",
                    "patient_id": self.patient_id,
                    "timestamp": now.isoformat(),
                    "glucose": glucose_val,
                    "analysis": self.latest_analysis
                }
                await self._broadcast(broadcast_data)

                # Log
                trend = self.latest_analysis.get("computed_trend", "—")
                pred = self.latest_analysis.get("predicted_glucose_30m", "—")
                risk = self.latest_analysis.get("risk_level", "—")
                logger.info(
                    f"⏱ [Sensor {self.patient_id}] Glucose: {glucose_val} mg/dL | "
                    f"Trend: {trend} | Pred30: {pred} | Risk: {risk}"
                )

                # إطلاق أحداث تلقائية
                self._trigger_auto_events()

                # Keep only last 2000 readings
                if len(self.glucose_history) > 2000:
                    self.glucose_history = self.glucose_history[-2000:]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Sensor {self.patient_id}] Loop error: {e}")

            await asyncio.sleep(interval_sec)

        logger.info(f"🛑 [Sensor {self.patient_id}] Stopped.")

    def start(self, pipeline_callback, interval_sec: float = 3.0):
        """تشغيل الحساس كـ background task"""
        if self.is_running:
            logger.warning(f"[Sensor {self.patient_id}] Already running!")
            return
        self._task = asyncio.create_task(
            self._run_loop(pipeline_callback, interval_sec)
        )

    def stop(self):
        """إيقاف الحساس"""
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None

    def get_status(self) -> dict:
        """جلب حالة الحساس"""
        return {
            "patient_id": self.patient_id,
            "profile_type": self.profile_type,
            "profile_name": self.profile.get("name", "Unknown"),
            "is_running": self.is_running,
            "current_glucose": self.current_glucose,
            "total_readings": len(self.glucose_history),
            "total_events": len(self.event_history),
            "active_events": len(self.active_events),
        }

    def get_dashboard_data(self) -> dict:
        """جلب بيانات لوحة التحكم الكاملة"""
        history = self.glucose_history[-20:]
        latest = self.latest_analysis

        # Build chart data
        chart_data = []
        for h in history:
            ts = h["timestamp"]
            if isinstance(ts, str):
                time_str = ts.split("T")[1][:5] if "T" in ts else ts[:5]
            else:
                time_str = ts.strftime("%H:%M")
            chart_data.append({
                "time": time_str,
                "glucose": h["glucose_value"],
                "pred": None
            })

        # Add predictions
        pred_30 = latest.get("predicted_glucose_30m")
        pred_60 = latest.get("predicted_glucose_60m")
        pred_120 = latest.get("predicted_glucose_120m")

        if pred_30:
            chart_data.append({"time": "+30m", "glucose": None, "pred": round(pred_30, 1)})
        if pred_60:
            chart_data.append({"time": "+60m", "glucose": None, "pred": round(pred_60, 1)})
        if pred_120:
            chart_data.append({"time": "+2h", "glucose": None, "pred": round(pred_120, 1)})

        decision = latest.get("final_decision", {})
        risk = latest.get("risk_level", "LOW")

        # Risk class mapping
        risk_class = "safe"
        if risk == "CRITICAL":
            risk_class = "critical"
        elif risk == "HIGH":
            risk_class = "danger"
        elif risk == "MEDIUM":
            risk_class = "warning"

        # Trend color
        trend = latest.get("computed_trend", "STABLE")
        trend_color = "var(--success)"
        if "RISING" in trend:
            trend_color = "var(--warning)"
        if "RAPIDLY" in trend:
            trend_color = "var(--danger)"
        if "FALLING" in trend:
            trend_color = "var(--danger)"

        return {
            "status": "active" if self.is_running else "stopped",
            "patient_id": self.patient_id,
            "name": self.profile.get("name", f"Patient {self.patient_id}"),
            "name_ar": self.profile.get("name_ar", ""),
            "description": self.profile.get("description", ""),
            "description_ar": self.profile.get("description_ar", ""),
            "profile_type": self.profile_type,
            "glucose": round(self.current_glucose, 1),
            "trendText": trend,
            "trendColor": trend_color,
            "velocity": latest.get("glucose_velocity", 0.0),
            "pred30": round(pred_30, 1) if pred_30 else None,
            "pred60": round(pred_60, 1) if pred_60 else None,
            "pred120": round(pred_120, 1) if pred_120 else None,
            "predictionConfidence": latest.get("prediction_confidence", "—"),
            "predictionNarrativeAr": latest.get("prediction_narrative_ar", ""),
            "predictionNarrativeEn": latest.get("prediction_narrative_en", ""),
            "risk": risk,
            "riskClass": risk_class,
            "tir": f"{latest.get('time_in_range_percent', 0):.1f}%",
            "recommendation": decision.get("clinical_guidance", "لا توجد إجراءات مطلوبة حالياً"),
            "rationale": decision.get("rationale", "المؤشرات مستقرة"),
            "insight": (latest.get("behavioral_insights", [""])[0]
                        if latest.get("behavioral_insights") else ""),
            # --- NEW: Comprehensive Advice ---
            "patientAdvice": latest.get("patient_advice", {}),
            "actionSteps": latest.get("action_steps", []),
            "severityExplanation": latest.get("severity_explanation", ""),
            "preventionTips": latest.get("prevention_tips", []),
            "nextMealSuggestion": latest.get("next_meal_suggestion", ""),
            "chart": chart_data,
            "sensorStatus": self.get_status(),
        }


class SensorManager:
    """
    مدير الحساسات — يدير جميع الحساسات الافتراضية للمرضى.
    Singleton pattern للاستخدام عبر التطبيق.
    """

    def __init__(self):
        self.sensors: Dict[str, VirtualCGMSensor] = {}
        self._pipeline_callback = None

    def set_pipeline(self, callback):
        """تعيين دالة خط الأنابيب التي ستُنفّذ لكل قراءة"""
        self._pipeline_callback = callback

    def create_sensor(self, patient_id: str, profile: dict) -> VirtualCGMSensor:
        """إنشاء حساس جديد لمريض"""
        sensor = VirtualCGMSensor(patient_id=patient_id, profile=profile)
        self.sensors[patient_id] = sensor
        return sensor

    def start_sensor(self, patient_id: str, interval_sec: float = 3.0):
        """تشغيل حساس لمريض"""
        sensor = self.sensors.get(patient_id)
        if sensor:
            sensor.start(self._pipeline_callback, interval_sec)
        else:
            logger.warning(f"Sensor for patient {patient_id} not found!")

    def stop_sensor(self, patient_id: str):
        """إيقاف حساس لمريض"""
        sensor = self.sensors.get(patient_id)
        if sensor:
            sensor.stop()

    def start_all(self, interval_sec: float = 3.0):
        """تشغيل جميع الحساسات"""
        for pid, sensor in self.sensors.items():
            sensor.start(self._pipeline_callback, interval_sec)

    def stop_all(self):
        """إيقاف جميع الحساسات"""
        for sensor in self.sensors.values():
            sensor.stop()

    def get_sensor(self, patient_id: str) -> Optional[VirtualCGMSensor]:
        """جلب حساس مريض"""
        return self.sensors.get(patient_id)

    def get_all_statuses(self) -> List[dict]:
        """جلب حالة جميع الحساسات"""
        return [s.get_status() for s in self.sensors.values()]


# Singleton instance
sensor_manager = SensorManager()
