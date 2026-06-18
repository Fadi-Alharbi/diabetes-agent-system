"""
خدمة سرد التنبؤات (Prediction Narrative Service)
=================================================
تحوّل أرقام التنبؤ إلى سرد مفهوم بالعربية والإنجليزية
يشرح للمريض ماذا يتوقع ولماذا.
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger("IMDCS_PredictionNarrative")


def generate_prediction_narrative(
    current_glucose: float,
    predicted_30m: Optional[float],
    predicted_60m: Optional[float],
    predicted_120m: Optional[float],
    trend: str,
    velocity: float,
    recent_events: List[Dict[str, Any]],
    confidence: str = "MEDIUM"
) -> Dict[str, str]:
    """
    يولّد سرداً مفهوماً للتنبؤ بالعربية والإنجليزية.
    
    Returns:
        Dict with: narrative_ar, narrative_en, confidence
    """
    
    # ═══════════════════════════════════════
    #  تحديد اتجاه التغير وشدته
    # ═══════════════════════════════════════
    
    change_30 = (predicted_30m - current_glucose) if predicted_30m else 0
    abs_change = abs(change_30)
    
    # تحديد مستوى الثقة
    if abs(velocity) < 0.5 and abs_change < 10:
        confidence = "HIGH"
    elif abs(velocity) < 1.5 and abs_change < 30:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    confidence_text_ar = {"HIGH": "عالية", "MEDIUM": "متوسطة", "LOW": "منخفضة"}
    confidence_text_en = {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}
    
    # ═══════════════════════════════════════
    #  تحليل الأحداث المؤثرة
    # ═══════════════════════════════════════
    
    cause_ar = ""
    cause_en = ""
    
    recent_meals = [e for e in recent_events if e.get("event_type") == "meal"]
    recent_insulin = [e for e in recent_events if e.get("event_type") == "insulin"]
    recent_exercise = [e for e in recent_events if e.get("event_type") == "exercise"]
    
    causes_ar = []
    causes_en = []
    
    if recent_meals:
        last_meal = recent_meals[-1]
        carbs = last_meal.get("details", {}).get("carbs_g", "?")
        food = last_meal.get("details", {}).get("food_name", "وجبة")
        causes_ar.append(f"تأثير وجبة {food} ({carbs}g كربوهيدرات)")
        causes_en.append(f"effect of {food} meal ({carbs}g carbs)")
    
    if recent_insulin:
        last_insulin = recent_insulin[-1]
        units = last_insulin.get("details", {}).get("units", "?")
        causes_ar.append(f"تأثير جرعة إنسولين ({units} وحدات)")
        causes_en.append(f"effect of insulin dose ({units} units)")
    
    if recent_exercise:
        last_exercise = recent_exercise[-1]
        intensity = last_exercise.get("details", {}).get("intensity", 1.0)
        causes_ar.append(f"تأثير النشاط البدني (شدة {intensity})")
        causes_en.append(f"effect of physical activity (intensity {intensity})")
    
    if not causes_ar:
        causes_ar.append("العوامل الفسيولوجية الطبيعية (الدورة اليومية)")
        causes_en.append("normal physiological factors (circadian rhythm)")
    
    cause_ar = " و".join(causes_ar)
    cause_en = " and ".join(causes_en)
    
    # ═══════════════════════════════════════
    #  بناء السرد
    # ═══════════════════════════════════════
    
    narrative_ar = _build_arabic_narrative(
        current_glucose, predicted_30m, predicted_60m, predicted_120m,
        trend, velocity, change_30, cause_ar, confidence,
        confidence_text_ar[confidence]
    )
    
    narrative_en = _build_english_narrative(
        current_glucose, predicted_30m, predicted_60m, predicted_120m,
        trend, velocity, change_30, cause_en, confidence,
        confidence_text_en[confidence]
    )
    
    return {
        "narrative_ar": narrative_ar,
        "narrative_en": narrative_en,
        "confidence": confidence
    }


def _build_arabic_narrative(
    current, pred_30, pred_60, pred_120,
    trend, velocity, change_30, cause, confidence, conf_text
) -> str:
    """بناء السرد بالعربية"""
    
    parts = []
    
    # الوضع الحالي
    parts.append(f"📊 السكر الحالي: {current:.0f} mg/dL")
    
    # التنبؤ
    if pred_30:
        direction = "يرتفع" if change_30 > 5 else "ينخفض" if change_30 < -5 else "يبقى مستقراً"
        
        if abs(change_30) > 5:
            parts.append(
                f"🔮 خلال 30 دقيقة: من المتوقع أن {direction} السكر إلى "
                f"{pred_30:.0f} mg/dL (تغير {change_30:+.0f})"
            )
        else:
            parts.append(
                f"🔮 خلال 30 دقيقة: من المتوقع أن {direction} السكر "
                f"حول {pred_30:.0f} mg/dL"
            )
    
    if pred_60:
        parts.append(f"⏱ خلال ساعة: {pred_60:.0f} mg/dL")
    
    if pred_120:
        parts.append(f"⏱ خلال ساعتين: {pred_120:.0f} mg/dL")
    
    # السبب
    parts.append(f"📋 السبب المتوقع: {cause}")
    
    # التحذيرات
    if pred_30:
        if pred_30 < 70:
            parts.append("⚠️ تحذير: السكر متوقع أن يدخل منطقة الهبوط — جهّز وجبة خفيفة!")
        elif pred_30 > 250:
            parts.append("⚠️ تحذير: السكر متوقع أن يدخل منطقة الارتفاع الشديد — راقب عن قرب!")
    
    # مستوى الثقة
    parts.append(f"📈 دقة التنبؤ: {conf_text}")
    
    return "\n".join(parts)


def _build_english_narrative(
    current, pred_30, pred_60, pred_120,
    trend, velocity, change_30, cause, confidence, conf_text
) -> str:
    """Build the English narrative"""
    
    parts = []
    
    # Current
    parts.append(f"📊 Current glucose: {current:.0f} mg/dL")
    
    # Prediction
    if pred_30:
        direction = "rise" if change_30 > 5 else "drop" if change_30 < -5 else "remain stable"
        
        if abs(change_30) > 5:
            parts.append(
                f"🔮 In 30 minutes: glucose is expected to {direction} to "
                f"{pred_30:.0f} mg/dL (change: {change_30:+.0f})"
            )
        else:
            parts.append(
                f"🔮 In 30 minutes: glucose is expected to {direction} "
                f"around {pred_30:.0f} mg/dL"
            )
    
    if pred_60:
        parts.append(f"⏱ In 1 hour: {pred_60:.0f} mg/dL")
    
    if pred_120:
        parts.append(f"⏱ In 2 hours: {pred_120:.0f} mg/dL")
    
    # Cause
    parts.append(f"📋 Likely cause: {cause}")
    
    # Warnings
    if pred_30:
        if pred_30 < 70:
            parts.append("⚠️ Warning: glucose expected to enter hypoglycemia zone — prepare a snack!")
        elif pred_30 > 250:
            parts.append("⚠️ Warning: glucose expected to enter severe hyperglycemia zone — monitor closely!")
    
    # Confidence
    parts.append(f"📈 Prediction confidence: {conf_text}")
    
    return "\n".join(parts)
