"""
LangGraph Agent Node Functions — Enhanced Version
==================================================
وظائف عقد الوكلاء المحسّنة مع تنبؤ EWMA ونصائح طبية شاملة.
"""

from typing import Dict, Any, List
from backend.core.state import PatientState
from backend.agents.recommendation_agent import generate_comprehensive_advice
from backend.services.prediction_narrative import generate_prediction_narrative
import math


# ═══════════════════════════════════════════════════════════════
#  1. Data Agent — التنظيف والتحقق
# ═══════════════════════════════════════════════════════════════

def data_agent_node(state: PatientState) -> PatientState:
    """Validates data and calculates base metrics like Time In Range."""
    current_val = state["current_reading"]["glucose_value"]
    
    # Sanity check
    if current_val < 30.0 or current_val > 500.0:
        state.setdefault("shap_explanations", {})["data_anomaly"] = True
    
    # Calculate Time in Range (TIR)
    all_readings = state.get("historical_readings", []) + [state["current_reading"]]
    glucose_values = [r["glucose_value"] for r in all_readings 
                      if 30.0 <= r["glucose_value"] <= 500.0]
    
    if glucose_values:
        in_range = sum(1 for v in glucose_values if 70.0 <= v <= 180.0)
        tir = (in_range / len(glucose_values)) * 100
        state["time_in_range_percent"] = round(tir, 1)
    else:
        state["time_in_range_percent"] = 0.0
    
    return state


# ═══════════════════════════════════════════════════════════════
#  2. Trend Agent — حساب الاتجاه والسرعة
# ═══════════════════════════════════════════════════════════════

def trend_agent_node(state: PatientState) -> PatientState:
    """Calculates velocity and trend direction using recent history."""
    history = state.get("historical_readings", [])
    
    if len(history) < 2:
        state["computed_trend"] = "STABLE"
        state["glucose_velocity"] = 0.0
        return state

    current = state["current_reading"]["glucose_value"]
    
    # Use weighted average of last 3 readings for smoother velocity
    recent = history[-3:] if len(history) >= 3 else history
    velocities = []
    
    for i, reading in enumerate(recent):
        last_val = reading["glucose_value"]
        diff = current - last_val
        # Approximate time difference (5 min per reading)
        time_steps = len(recent) - i
        time_diff = time_steps * 5.0
        if time_diff > 0:
            velocities.append(diff / time_diff)
    
    # Weighted average (more recent = higher weight)
    if velocities:
        weights = list(range(1, len(velocities) + 1))
        velocity = sum(v * w for v, w in zip(velocities, weights)) / sum(weights)
    else:
        velocity = 0.0
    
    state["glucose_velocity"] = round(velocity, 2)
    
    # Classification based on medical standards
    if velocity > 2.0:
        state["computed_trend"] = "RAPIDLY_RISING"
    elif velocity > 1.0:
        state["computed_trend"] = "RISING"
    elif velocity < -2.0:
        state["computed_trend"] = "RAPIDLY_FALLING"
    elif velocity < -1.0:
        state["computed_trend"] = "FALLING"
    else:
        state["computed_trend"] = "STABLE"
        
    return state


# ═══════════════════════════════════════════════════════════════
#  3. Prediction Agent — تنبؤ محسّن بـ EWMA + Momentum
# ═══════════════════════════════════════════════════════════════

def prediction_agent_node(state: PatientState) -> PatientState:
    """
    Enhanced prediction using Exponential Weighted Moving Average (EWMA)
    with momentum and physiological damping.
    Predicts at 30, 60, and 120 minute horizons.
    """
    current = state["current_reading"]["glucose_value"]
    velocity = state.get("glucose_velocity", 0.0)
    history = state.get("historical_readings", [])
    
    # ─── EWMA-based prediction ───
    alpha = 0.3  # Smoothing factor
    
    if len(history) >= 3:
        recent_vals = [r["glucose_value"] for r in history[-6:]]
        recent_vals.append(current)
        
        # Calculate EWMA
        ewma = recent_vals[0]
        for val in recent_vals[1:]:
            ewma = alpha * val + (1 - alpha) * ewma
        
        # Momentum: acceleration (change in velocity)
        if len(history) >= 4:
            prev_velocity = (history[-1]["glucose_value"] - history[-2]["glucose_value"]) / 5.0
            acceleration = (velocity - prev_velocity) / 5.0
        else:
            acceleration = 0.0
        
        # Damping factor increases with prediction horizon
        damping_30 = 0.7
        damping_60 = 0.5
        damping_120 = 0.3
        
        # Physiological mean reversion factor
        # Glucose tends to return toward ~120 mg/dL over time
        mean_reversion_target = 120.0
        reversion_strength = 0.02
        
        # Predictions
        pred_30 = ewma + (velocity * 30 * damping_30) + (0.5 * acceleration * 30 * 30 * 0.01)
        pred_60 = ewma + (velocity * 60 * damping_60) + (0.5 * acceleration * 60 * 60 * 0.005)
        pred_120 = ewma + (velocity * 120 * damping_120) + (0.5 * acceleration * 120 * 120 * 0.002)
        
        # Apply mean reversion for longer horizons
        pred_60 += (mean_reversion_target - pred_60) * reversion_strength * 2
        pred_120 += (mean_reversion_target - pred_120) * reversion_strength * 5
        
    else:
        # Fallback: simple linear with damping
        damping = 0.5
        pred_30 = current + (velocity * 30 * damping)
        pred_60 = current + (velocity * 60 * 0.35)
        pred_120 = current + (velocity * 120 * 0.2)
    
    # Physiological bounds clamping
    pred_30 = max(40.0, min(pred_30, 450.0))
    pred_60 = max(40.0, min(pred_60, 450.0))
    pred_120 = max(40.0, min(pred_120, 450.0))
    
    state["predicted_glucose_30m"] = round(pred_30, 1)
    state["predicted_glucose_60m"] = round(pred_60, 1)
    state["predicted_glucose_120m"] = round(pred_120, 1)
    
    # ─── Prediction Confidence ───
    if abs(velocity) < 0.5 and len(history) >= 6:
        state["prediction_confidence"] = "HIGH"
    elif abs(velocity) < 1.5 and len(history) >= 3:
        state["prediction_confidence"] = "MEDIUM"
    else:
        state["prediction_confidence"] = "LOW"
    
    # ─── Generate bilingual prediction narrative ───
    narrative = generate_prediction_narrative(
        current_glucose=current,
        predicted_30m=pred_30,
        predicted_60m=pred_60,
        predicted_120m=pred_120,
        trend=state.get("computed_trend", "STABLE"),
        velocity=velocity,
        recent_events=state.get("recent_events", []),
        confidence=state.get("prediction_confidence", "MEDIUM")
    )
    
    state["prediction_narrative_ar"] = narrative["narrative_ar"]
    state["prediction_narrative_en"] = narrative["narrative_en"]
    state["prediction_confidence"] = narrative["confidence"]
    
    return state


# ═══════════════════════════════════════════════════════════════
#  4. Food Impact Agent — تأثير الوجبات
# ═══════════════════════════════════════════════════════════════

def food_impact_agent_node(state: PatientState) -> PatientState:
    """Learns personalized food responses."""
    events = state.get("recent_events", [])
    meals = [e for e in events if e.get("event_type") == "meal"]
    
    updates = []
    if meals:
        last_meal = meals[-1]
        food_name = last_meal.get("details", {}).get("food_name", "Unknown")
        carbs = last_meal.get("details", {}).get("carbs_g", 0)
        
        # Estimate impact based on carbs and current trend
        trend = state.get("computed_trend", "STABLE")
        if "RISING" in trend and carbs > 60:
            impact = "HIGH_SPIKE"
            confidence = 0.85
        elif "RISING" in trend:
            impact = "MODERATE_SPIKE"
            confidence = 0.7
        elif carbs > 80:
            impact = "EXPECTED_SPIKE"
            confidence = 0.6
        else:
            impact = "LOW_IMPACT"
            confidence = 0.5
            
        updates.append({
            "food": food_name,
            "carbs_g": carbs,
            "impact": impact,
            "confidence": confidence,
            "description_ar": _food_impact_description_ar(food_name, carbs, impact),
            "description_en": _food_impact_description_en(food_name, carbs, impact)
        })
        
    state["food_impact_updates"] = updates
    return state


def _food_impact_description_ar(food: str, carbs: int, impact: str) -> str:
    impact_map = {
        "HIGH_SPIKE": f"⚠️ وجبة {food} ({carbs}g) تسبب ارتفاعاً حاداً — حاول تقليل الكمية في المرات القادمة",
        "MODERATE_SPIKE": f"🟡 وجبة {food} ({carbs}g) تسبب ارتفاعاً متوسطاً",
        "EXPECTED_SPIKE": f"📊 وجبة {food} ({carbs}g) — متوقع ارتفاع بسبب كمية الكربوهيدرات",
        "LOW_IMPACT": f"✅ وجبة {food} ({carbs}g) — تأثير منخفض على السكر"
    }
    return impact_map.get(impact, f"وجبة {food}")


def _food_impact_description_en(food: str, carbs: int, impact: str) -> str:
    impact_map = {
        "HIGH_SPIKE": f"⚠️ {food} ({carbs}g) causes a sharp spike — try reducing portions next time",
        "MODERATE_SPIKE": f"🟡 {food} ({carbs}g) causes a moderate spike",
        "EXPECTED_SPIKE": f"📊 {food} ({carbs}g) — spike expected due to carb amount",
        "LOW_IMPACT": f"✅ {food} ({carbs}g) — low impact on blood sugar"
    }
    return impact_map.get(impact, f"{food}")


# ═══════════════════════════════════════════════════════════════
#  5. Behavior Agent — التحليل السلوكي
# ═══════════════════════════════════════════════════════════════

def behavior_agent_node(state: PatientState) -> PatientState:
    """Analyzes behavioral events and correlates with glucose trends."""
    insights = []
    events = state.get("recent_events", [])
    trend = state.get("computed_trend", "STABLE")
    
    meals = [e for e in events if e.get("event_type") == "meal"]
    exercises = [e for e in events if e.get("event_type") == "exercise"]
    insulin_events = [e for e in events if e.get("event_type") == "insulin"]
    
    if meals and "RISING" in trend:
        last_meal = meals[-1]
        food = last_meal.get("details", {}).get("food_name", "وجبة")
        carbs = last_meal.get("details", {}).get("carbs_g", 0)
        insights.append(
            f"الارتفاع الحالي مرتبط بتناول {food} ({carbs}g كربوهيدرات) | "
            f"Current rise linked to {food} ({carbs}g carbs)"
        )
    
    if insulin_events and "FALLING" in trend:
        units = insulin_events[-1].get("details", {}).get("units", 0)
        insights.append(
            f"الهبوط يتوافق مع تأثير الإنسولين ({units} وحدات) | "
            f"Drop aligns with insulin effect ({units} units)"
        )
    
    if exercises and "FALLING" in trend:
        intensity = exercises[-1].get("details", {}).get("intensity", 1.0)
        insights.append(
            f"النشاط البدني (شدة {intensity}) يزيد حساسية الخلايا للإنسولين ويخفض السكر | "
            f"Exercise (intensity {intensity}) increases insulin sensitivity"
        )
    
    if exercises and "RISING" in trend:
        insights.append(
            "رغم النشاط البدني، السكر يرتفع — ربما بسبب وجبة غنية بالكربوهيدرات أو توتر | "
            "Despite exercise, glucose is rising — possibly due to carb-heavy meal or stress"
        )
    
    if not events:
        insights.append(
            "لم تُسجّل أحداث سلوكية مؤخراً — التغيرات قد تكون فسيولوجية | "
            "No behavioral events logged — changes may be physiological"
        )
    
    if not insights:
        insights.append(
            "المؤشرات الحالية تعكس عوامل فسيولوجية طبيعية | "
            "Current metrics reflect normal physiological factors"
        )
        
    state["behavioral_insights"] = insights
    return state


# ═══════════════════════════════════════════════════════════════
#  6. Risk Agent — تقييم المخاطر
# ═══════════════════════════════════════════════════════════════

def risk_agent_node(state: PatientState) -> PatientState:
    """Classifies risk level based on current and predicted values."""
    current = state["current_reading"]["glucose_value"]
    pred = state.get("predicted_glucose_30m", current)
    velocity = state.get("glucose_velocity", 0.0)
    
    # Critical thresholds
    if current <= 55 or pred <= 55 or current >= 300 or pred >= 300:
        state["risk_level"] = "CRITICAL"
    elif current <= 70 or pred <= 70 or current >= 250 or pred >= 250:
        state["risk_level"] = "HIGH"
    elif abs(velocity) > 2.0:
        state["risk_level"] = "MEDIUM"
    elif current > 180 or current < 80:
        state["risk_level"] = "MEDIUM"
    else:
        state["risk_level"] = "LOW"
    
    return state


# ═══════════════════════════════════════════════════════════════
#  7. Recommendation Agent — النصائح الطبية الشاملة + القرار النهائي
# ═══════════════════════════════════════════════════════════════

def recommendation_agent_node(state: PatientState) -> PatientState:
    """
    Generates comprehensive bilingual medical advice and final clinical decision.
    This is the Meta-Decision agent that consolidates all agent outputs.
    """
    current = state["current_reading"]["glucose_value"]
    pred_30 = state.get("predicted_glucose_30m", current)
    risk = state.get("risk_level", "LOW")
    trend = state.get("computed_trend", "STABLE")
    velocity = state.get("glucose_velocity", 0.0)
    insights = state.get("behavioral_insights", [])
    events = state.get("recent_events", [])
    
    # ─── Generate comprehensive advice ───
    advice_result = generate_comprehensive_advice(
        current_glucose=current,
        predicted_30m=pred_30,
        risk_level=risk,
        trend=trend,
        velocity=velocity,
        behavioral_insights=insights,
        recent_events=events
    )
    
    state["patient_advice"] = advice_result["patient_advice"]
    state["action_steps"] = advice_result["action_steps"]
    state["severity_explanation"] = advice_result["severity_explanation"]
    state["prevention_tips"] = advice_result["prevention_tips"]
    state["next_meal_suggestion"] = advice_result["next_meal_suggestion"]
    
    # ─── Build final decision (legacy compatibility) ───
    decision = {
        "action_required": False,
        "notification_type": "NONE",
        "clinical_guidance": "",
        "clinical_guidance_ar": "",
        "rationale": "",
        "rationale_ar": ""
    }
    
    advice = advice_result["patient_advice"]
    
    if risk == "CRITICAL":
        decision["action_required"] = True
        decision["notification_type"] = "URGENT_ALERT"
        decision["clinical_guidance"] = advice.get("guidance_en", "")
        decision["clinical_guidance_ar"] = advice.get("guidance_ar", "")
        
        if current < 70 or pred_30 < 55:
            decision["rationale"] = (
                f"Critical Hypoglycemia — Current: {current}, Predicted: {pred_30:.0f}, "
                f"Trend: {trend}"
            )
            decision["rationale_ar"] = (
                f"هبوط حاد في السكر — الحالي: {current}، المتوقع: {pred_30:.0f}، "
                f"الاتجاه: {trend}"
            )
        else:
            decision["rationale"] = (
                f"Severe Hyperglycemia — Current: {current}, Predicted: {pred_30:.0f}, "
                f"Trend: {trend}"
            )
            decision["rationale_ar"] = (
                f"ارتفاع حاد في السكر — الحالي: {current}، المتوقع: {pred_30:.0f}، "
                f"الاتجاه: {trend}"
            )
    
    elif risk == "HIGH":
        decision["action_required"] = True
        decision["notification_type"] = "WARNING"
        decision["clinical_guidance"] = advice.get("guidance_en", "")
        decision["clinical_guidance_ar"] = advice.get("guidance_ar", "")
        
        behavioral_ctx = f" | {insights[0]}" if insights else ""
        decision["rationale"] = (
            f"High risk — Current: {current}, Predicted: {pred_30:.0f}, "
            f"Trend: {trend}{behavioral_ctx}"
        )
        decision["rationale_ar"] = (
            f"خطورة عالية — الحالي: {current}، المتوقع: {pred_30:.0f}، "
            f"الاتجاه: {trend}{behavioral_ctx}"
        )
    
    elif risk == "MEDIUM":
        decision["action_required"] = False
        decision["notification_type"] = "INFO"
        decision["clinical_guidance"] = advice.get("guidance_en", "")
        decision["clinical_guidance_ar"] = advice.get("guidance_ar", "")
        decision["rationale"] = f"Moderate change detected — monitoring recommended"
        decision["rationale_ar"] = f"تغير متوسط — يُنصح بالمراقبة"
    
    else:
        decision["action_required"] = False
        decision["notification_type"] = "INFO"
        decision["clinical_guidance"] = advice.get("guidance_en", "")
        decision["clinical_guidance_ar"] = advice.get("guidance_ar", "")
        decision["rationale"] = "All metrics stable — excellent control"
        decision["rationale_ar"] = "جميع المؤشرات مستقرة — تحكم ممتاز"
    
    # Add SHAP-style explanation
    decision["shap_insight"] = ""
    if insights:
        decision["shap_insight"] = insights[0]
    
    state["final_decision"] = decision
    
    return state
