"""
وكيل التوصيات والنصائح الطبية الشامل
==========================================
يعطي المريض نصائح مفصّلة ومخصصة بالعربية والإنجليزية
حسب حالته الحالية والمتوقعة، ويشرح كيف يتعامل مع
كل سيناريو (ارتفاع، هبوط، استقرار، تغير سريع).
"""

import logging
from typing import Dict, Any, List
from openai import OpenAI
import os 
import json
logger = logging.getLogger("IMDCS_RecommendationAgent")


# ═══════════════════════════════════════════════════════════════
#  قاعدة المعرفة الطبية — النصائح المفصّلة لكل سيناريو
# ═══════════════════════════════════════════════════════════════

ADVICE_DATABASE = {
    # ───── حالات الهبوط الحرج (Critical Hypoglycemia ≤55 mg/dL) ─────
    "CRITICAL_HYPO": {
        "title": "⚠️ هبوط حاد في السكر — حالة طوارئ",
        "title_en": "⚠️ Severe Hypoglycemia — Emergency",
        "severity": "CRITICAL",
        "guidance_ar": "مستوى السكر في منطقة الخطر الشديد. يجب التصرف فوراً!",
        "guidance_en": "Blood glucose is in the critical danger zone. Act immediately!",
        "action_steps_ar": [
            "١. تناول فوراً 15 غرام كربوهيدرات سريعة المفعول (نصف كوب عصير، 3-4 حبات حلوى جلوكوز، أو ملعقة عسل)",
            "٢. اجلس أو استلقِ في مكان آمن — لا تقُد السيارة ولا تمارس أي نشاط",
            "٣. انتظر 15 دقيقة ثم أعد قياس السكر",
            "٤. إذا بقي أقل من 70: كرر الخطوة الأولى",
            "٥. بعد ارتفاع السكر فوق 70: تناول وجبة خفيفة تحتوي بروتين + كربوهيدرات معقدة (مثل جبنة مع خبز)",
            "٦. إذا فقدت الوعي أو لم يرتفع السكر بعد 3 محاولات: اتصل بالطوارئ فوراً"
        ],
        "action_steps_en": [
            "1. Immediately consume 15g of fast-acting carbs (half cup of juice, 3-4 glucose tablets, or 1 tbsp honey)",
            "2. Sit down or lie down safely — do NOT drive or exercise",
            "3. Wait 15 minutes, then recheck blood glucose",
            "4. If still below 70: repeat step 1",
            "5. After glucose rises above 70: eat a snack with protein + complex carbs (e.g., cheese with bread)",
            "6. If unconscious or no improvement after 3 attempts: call emergency services immediately"
        ],
        "prevention_tips_ar": [
            "• تأكد من تناول وجباتك في مواعيد منتظمة",
            "• لا تتخطَ أي وجبة خاصة إذا أخذت الإنسولين",
            "• احمل معك دائماً حلوى جلوكوز أو عصير صغير",
            "• راجع جرعة الإنسولين مع طبيبك — قد تكون مرتفعة",
            "• قلل جرعة الإنسولين قبل الرياضة بعد استشارة الطبيب"
        ],
        "prevention_tips_en": [
            "• Eat meals on a regular schedule",
            "• Never skip meals, especially after taking insulin",
            "• Always carry glucose tablets or a small juice box",
            "• Review insulin dosage with your doctor — it may be too high",
            "• Reduce insulin dose before exercise (consult your doctor)"
        ],
        "meal_suggestion_ar": "بعد الاستقرار: تناول وجبة متوازنة (خبز أسمر + بروتين + خضار) لمنع تكرار الهبوط",
        "meal_suggestion_en": "After stabilization: eat a balanced meal (whole grain + protein + vegetables) to prevent recurrence"
    },

    # ───── هبوط (Hypoglycemia 56-70 mg/dL) ─────
    "HIGH_RISK_HYPO": {
        "title": "🟡 هبوط في السكر — تحذير",
        "title_en": "🟡 Low Blood Sugar — Warning",
        "severity": "HIGH",
        "guidance_ar": "السكر في مستوى منخفض ويحتاج تدخل سريع قبل أن يصل لمنطقة الخطر.",
        "guidance_en": "Blood sugar is low and needs quick intervention before reaching danger zone.",
        "action_steps_ar": [
            "١. تناول 15 غرام كربوهيدرات سريعة (نصف كوب عصير أو 3 حبات حلوى جلوكوز)",
            "٢. انتظر 15 دقيقة وأعد القياس",
            "٣. إذا ارتفع فوق 80: تناول وجبة خفيفة تحتوي نشويات معقدة",
            "٤. سجّل هذا الحدث وأبلغ طبيبك في الزيارة القادمة"
        ],
        "action_steps_en": [
            "1. Consume 15g fast-acting carbs (half cup juice or 3 glucose tablets)",
            "2. Wait 15 minutes and recheck",
            "3. If above 80: eat a snack with complex carbohydrates",
            "4. Log this event and report to your doctor at next visit"
        ],
        "prevention_tips_ar": [
            "• لا تؤخر وجباتك الرئيسية",
            "• تناول وجبة خفيفة قبل التمارين الرياضية",
            "• احرص على النوم الكافي (7-8 ساعات)"
        ],
        "prevention_tips_en": [
            "• Don't delay your main meals",
            "• Have a snack before exercise",
            "• Ensure adequate sleep (7-8 hours)"
        ],
        "meal_suggestion_ar": "تناول وجبة تحتوي كربوهيدرات معقدة + بروتين (مثل: شوفان مع لبن وموز)",
        "meal_suggestion_en": "Eat complex carbs + protein (e.g., oatmeal with yogurt and banana)"
    },

    # ───── ارتفاع حرج (Critical Hyperglycemia ≥300 mg/dL) ─────
    "CRITICAL_HYPER": {
        "title": "🔴 ارتفاع حاد في السكر — حالة طوارئ",
        "title_en": "🔴 Severe Hyperglycemia — Emergency",
        "severity": "CRITICAL",
        "guidance_ar": "مستوى السكر مرتفع جداً وقد يكون خطيراً. يجب التصرف بحذر!",
        "guidance_en": "Blood glucose is dangerously high. Act cautiously!",
        "action_steps_ar": [
            "١. افحص الكيتونات في البول إن توفر الجهاز (خطر حموضة الدم DKA)",
            "٢. اشرب كمية كبيرة من الماء (كوب كل 30 دقيقة) لمساعدة الكلى",
            "٣. خذ جرعة تصحيح الإنسولين حسب تعليمات طبيبك",
            "٤. لا تمارس الرياضة الآن — الرياضة مع ارتفاع شديد قد تزيد الكيتونات",
            "٥. إذا شعرت بغثيان أو آلام بطن أو تنفس سريع: اذهب للطوارئ فوراً",
            "٦. أعد قياس السكر بعد ساعة — إذا لم ينخفض تواصل مع طبيبك"
        ],
        "action_steps_en": [
            "1. Check urine ketones if available (risk of DKA)",
            "2. Drink plenty of water (one glass every 30 minutes)",
            "3. Take correction insulin dose as prescribed by your doctor",
            "4. Do NOT exercise now — exercise with very high glucose may increase ketones",
            "5. If nausea, abdominal pain, or rapid breathing: go to ER immediately",
            "6. Recheck glucose after 1 hour — if not decreasing, contact your doctor"
        ],
        "prevention_tips_ar": [
            "• التزم بمواعيد الأدوية والإنسولين بدقة",
            "• قلل الكربوهيدرات البسيطة (سكريات، خبز أبيض، عصائر محلاة)",
            "• راقب تأثير الوجبات على السكر وسجّلها",
            "• لا تفوّت جرعة الإنسولين أبداً"
        ],
        "prevention_tips_en": [
            "• Take medications and insulin exactly as prescribed",
            "• Reduce simple carbohydrates (sugars, white bread, sweetened juices)",
            "• Monitor meal effects on glucose and log them",
            "• Never miss an insulin dose"
        ],
        "meal_suggestion_ar": "تجنب الأكل حالياً حتى ينخفض السكر. بعد الانخفاض: تناول بروتين + خضار (مثل: دجاج مشوي مع سلطة)",
        "meal_suggestion_en": "Avoid eating until glucose drops. After: eat protein + vegetables (e.g., grilled chicken with salad)"
    },

    # ───── ارتفاع (Hyperglycemia 250-299 mg/dL) ─────
    "HIGH_RISK_HYPER": {
        "title": "🟠 ارتفاع في السكر — تحذير",
        "title_en": "🟠 High Blood Sugar — Warning",
        "severity": "HIGH",
        "guidance_ar": "السكر مرتفع ويحتاج تدخل لتجنب المضاعفات.",
        "guidance_en": "Blood sugar is elevated and needs intervention to avoid complications.",
        "action_steps_ar": [
            "١. اشرب كوبين من الماء الآن",
            "٢. خذ جرعة تصحيح الإنسولين إذا كانت موصوفة لك",
            "٣. تجنب الأكل حتى يبدأ السكر بالانخفاض",
            "٤. مارس مشياً خفيفاً لمدة 15-20 دقيقة إذا كنت تشعر بتحسن",
            "٥. أعد القياس بعد 45 دقيقة"
        ],
        "action_steps_en": [
            "1. Drink two glasses of water now",
            "2. Take correction insulin if prescribed",
            "3. Avoid eating until glucose starts dropping",
            "4. Take a light 15-20 minute walk if feeling well",
            "5. Recheck glucose after 45 minutes"
        ],
        "prevention_tips_ar": [
            "• قسّم وجباتك إلى 5 وجبات صغيرة بدل 3 كبيرة",
            "• استبدل الأرز الأبيض بالبرغل أو الأرز البني",
            "• تناول الخضار قبل النشويات في كل وجبة"
        ],
        "prevention_tips_en": [
            "• Split meals into 5 small meals instead of 3 large ones",
            "• Replace white rice with bulgur or brown rice",
            "• Eat vegetables before carbohydrates at each meal"
        ],
        "meal_suggestion_ar": "وجبة خفيفة: خيار + حمص + زيت زيتون (بدون خبز)",
        "meal_suggestion_en": "Light snack: cucumber + hummus + olive oil (no bread)"
    },

    # ───── تغير سريع (Rapid Change but in range) ─────
    "MEDIUM_RAPID_CHANGE": {
        "title": "⚡ تغير سريع في السكر",
        "title_en": "⚡ Rapid Glucose Change",
        "severity": "MEDIUM",
        "guidance_ar": "السكر يتغير بسرعة غير عادية. يجب المراقبة عن قرب.",
        "guidance_en": "Glucose is changing unusually fast. Close monitoring needed.",
        "action_steps_ar": [
            "١. أعد القياس خلال 10 دقائق للتأكد من الاتجاه",
            "٢. إذا كان ينخفض بسرعة: جهّز وجبة خفيفة سريعة",
            "٣. إذا كان يرتفع بسرعة: اشرب ماء وراجع آخر وجبة",
            "٤. ابقَ في حالة يقظة ولا تنم حتى يستقر"
        ],
        "action_steps_en": [
            "1. Recheck in 10 minutes to confirm the trend",
            "2. If dropping fast: prepare a quick snack",
            "3. If rising fast: drink water and review last meal",
            "4. Stay alert and don't sleep until glucose stabilizes"
        ],
        "prevention_tips_ar": [
            "• تجنب الوجبات الكبيرة دفعة واحدة",
            "• وزّع الكربوهيدرات على مدار اليوم"
        ],
        "prevention_tips_en": [
            "• Avoid large meals all at once",
            "• Distribute carbohydrates throughout the day"
        ],
        "meal_suggestion_ar": "وجبة متوازنة صغيرة بعد الاستقرار",
        "meal_suggestion_en": "Small balanced meal after stabilization"
    },

    # ───── ارتفاع متوسط (Elevated 180-249 mg/dL) ─────
    "MEDIUM_ELEVATED": {
        "title": "🟡 السكر مرتفع قليلاً — انتبه",
        "title_en": "🟡 Glucose Elevated — Attention Needed",
        "severity": "MEDIUM",
        "guidance_ar": "السكر خارج النطاق المستهدف ويحتاج مراقبة ومعالجة خفيفة.",
        "guidance_en": "Blood sugar is above target range and needs monitoring with mild intervention.",
        "action_steps_ar": [
            "١. اشرب كوبين من الماء",
            "٢. تجنب تناول كربوهيدرات إضافية حالياً",
            "٣. مارس مشياً خفيفاً لمدة 10-15 دقيقة إذا أمكن",
            "٤. إذا كان لديك إنسولين تصحيحي: خذ الجرعة المحددة",
            "٥. أعد القياس بعد 30 دقيقة"
        ],
        "action_steps_en": [
            "1. Drink two glasses of water",
            "2. Avoid consuming additional carbohydrates now",
            "3. Take a light 10-15 minute walk if possible",
            "4. If you have correction insulin: take the prescribed dose",
            "5. Recheck glucose after 30 minutes"
        ],
        "prevention_tips_ar": [
            "• قلل حجم حصص الكربوهيدرات في كل وجبة",
            "• تناول البروتين والخضار أولاً ثم النشويات",
            "• تحرّك بعد كل وجبة (مشي 10 دقائق)"
        ],
        "prevention_tips_en": [
            "• Reduce carbohydrate portion sizes at each meal",
            "• Eat protein and vegetables first, then carbs",
            "• Walk for 10 minutes after each meal"
        ],
        "meal_suggestion_ar": "وجبة خفيفة: سلطة خضراء مع بروتين (دجاج أو تونة) بدون خبز",
        "meal_suggestion_en": "Light meal: green salad with protein (chicken or tuna) without bread"
    },

    # ───── مستقر (Stable — Good Control) ─────
    "LOW_STABLE": {
        "title": "✅ السكر مستقر — ممتاز!",
        "title_en": "✅ Glucose Stable — Excellent!",
        "severity": "LOW",
        "guidance_ar": "مستوى السكر في النطاق الآمن والمؤشرات مستقرة. استمر هكذا! 👏",
        "guidance_en": "Blood glucose is in the safe range and metrics are stable. Keep it up! 👏",
        "action_steps_ar": [
            "١. استمر في نظامك الغذائي الحالي — أنت تبلي بلاءً حسناً!",
            "٢. حافظ على مواعيد الأدوية",
            "٣. مارس نشاطاً بدنياً خفيفاً (مشي 30 دقيقة يومياً)"
        ],
        "action_steps_en": [
            "1. Continue your current diet — you're doing great!",
            "2. Maintain medication schedule",
            "3. Do light physical activity (30 min walk daily)"
        ],
        "prevention_tips_ar": [
            "• حافظ على هذا الروتين الصحي",
            "• سجّل ما تأكله لمعرفة الأطعمة المناسبة لك",
            "• اشرب 8 أكواب ماء يومياً"
        ],
        "prevention_tips_en": [
            "• Maintain this healthy routine",
            "• Log your meals to identify what works for you",
            "• Drink 8 glasses of water daily"
        ],
        "meal_suggestion_ar": "وجبة صحية متوازنة: بروتين (سمك/دجاج) + خضار + حبوب كاملة",
        "meal_suggestion_en": "Balanced healthy meal: protein (fish/chicken) + vegetables + whole grains"
    }
}


def generate_comprehensive_advice(
    current_glucose: float,
    predicted_30m: float,
    risk_level: str,
    trend: str,
    velocity: float,
    behavioral_insights: List[str],
    recent_events: List[dict]
) -> Dict[str, Any]:

    scenario_key = _determine_scenario(current_glucose, predicted_30m, risk_level, trend, velocity)
    fallback = ADVICE_DATABASE[scenario_key]

    try:
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        insights_text = "\n".join(behavioral_insights) if behavioral_insights else "لا توجد ملاحظات"
        events_text = str(recent_events[-3:]) if recent_events else "لا توجد أحداث"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "أنت طبيب متخصص في السكري. حلّل بيانات المريض وأرجع توصية طبية مخصصة بصيغة JSON فقط بهذا الشكل: {\"title\": \"\", \"title_en\": \"\", \"guidance_ar\": \"\", \"guidance_en\": \"\", \"action_steps_ar\": [], \"action_steps_en\": [], \"prevention_tips_ar\": [], \"prevention_tips_en\": [], \"meal_suggestion_ar\": \"\", \"meal_suggestion_en\": \"\"}"
                },
                {
                    "role": "user",
                    "content": f"السكر الحالي: {current_glucose} mg/dL\nالتوقع بعد 30 دقيقة: {predicted_30m:.0f} mg/dL\nالاتجاه: {trend}\nسرعة التغيير: {velocity:.2f}\nمستوى الخطر: {risk_level}\nالأحداث الأخيرة: {events_text}\nالملاحظات: {insights_text}"
                }
            ]
        )

        ai_advice = json.loads(response.choices[0].message.content)

        severity_explanation = _build_severity_explanation(
            current_glucose, predicted_30m, risk_level, trend, velocity
        )

        return {
            "patient_advice": {
                "title": ai_advice.get("title", fallback["title"]),
                "title_en": ai_advice.get("title_en", fallback["title_en"]),
                "severity": risk_level,
                "guidance_ar": ai_advice.get("guidance_ar", fallback["guidance_ar"]),
                "guidance_en": ai_advice.get("guidance_en", fallback["guidance_en"]),
                "contextual_note_ar": insights_text,
                "contextual_note_en": "",
            },
            "action_steps": ai_advice.get("action_steps_ar", fallback["action_steps_ar"]),
            "action_steps_en": ai_advice.get("action_steps_en", []),
            "severity_explanation": severity_explanation,
            "prevention_tips": ai_advice.get("prevention_tips_ar", fallback["prevention_tips_ar"]),
            "prevention_tips_en": ai_advice.get("prevention_tips_en", []),
            "next_meal_suggestion": ai_advice.get("meal_suggestion_ar", fallback["meal_suggestion_ar"]),
            "next_meal_suggestion_en": ai_advice.get("meal_suggestion_en", ""),
        }

    except Exception as e:
        logger.error(f"خطأ في الاتصال بالذكاء الاصطناعي: {e}")

        severity_explanation = _build_severity_explanation(
            current_glucose, predicted_30m, risk_level, trend, velocity
        )

        return {
            "patient_advice": {
                "title": fallback["title"],
                "title_en": fallback["title_en"],
                "severity": risk_level,
                "guidance_ar": fallback["guidance_ar"],
                "guidance_en": fallback["guidance_en"],
                "contextual_note_ar": "",
                "contextual_note_en": "",
            },
            "action_steps": fallback["action_steps_ar"],
            "action_steps_en": fallback.get("action_steps_en", []),
            "severity_explanation": severity_explanation,
            "prevention_tips": fallback["prevention_tips_ar"],
            "prevention_tips_en": fallback.get("prevention_tips_en", []),
            "next_meal_suggestion": fallback["meal_suggestion_ar"],
            "next_meal_suggestion_en": fallback.get("meal_suggestion_en", ""),
        }


def _determine_scenario(
    current: float, predicted: float, risk: str, trend: str, velocity: float
) -> str:
    """تحديد السيناريو المناسب بناءً على المؤشرات"""
    
    # هبوط حرج
    if current <= 55 or predicted <= 55:
        return "CRITICAL_HYPO"
    
    # هبوط
    if current <= 70 or predicted <= 70:
        return "HIGH_RISK_HYPO"
    
    # ارتفاع حرج
    if current >= 300 or predicted >= 300:
        return "CRITICAL_HYPER"
    
    # ارتفاع
    if current >= 250 or predicted >= 250:
        return "HIGH_RISK_HYPER"
    
    # تغير سريع
    if abs(velocity) >= 2.0:
        return "MEDIUM_RAPID_CHANGE"
    
    # ارتفاع متوسط (فوق النطاق المستهدف)
    if current > 180 or predicted > 200:
        return "MEDIUM_ELEVATED"
    
    # مستقر
    return "LOW_STABLE"


def _build_severity_explanation(
    current: float, predicted: float, risk: str, trend: str, velocity: float
) -> str:
    """بناء شرح مبسّط ومفهوم لمستوى الخطورة"""
    
    parts_ar = []
    
    # الوضع الحالي
    if current < 55:
        parts_ar.append(f"🔴 السكر الحالي ({current} mg/dL) منخفض بشكل خطير — أقل من الحد الأدنى الآمن (55)")
    elif current < 70:
        parts_ar.append(f"🟡 السكر الحالي ({current} mg/dL) منخفض — أقل من النطاق الطبيعي (70-180)")
    elif current > 300:
        parts_ar.append(f"🔴 السكر الحالي ({current} mg/dL) مرتفع بشكل خطير — أعلى من الحد الأقصى الآمن (300)")
    elif current > 250:
        parts_ar.append(f"🟠 السكر الحالي ({current} mg/dL) مرتفع — أعلى من النطاق الطبيعي (70-180)")
    elif current > 180:
        parts_ar.append(f"🟡 السكر الحالي ({current} mg/dL) أعلى قليلاً من النطاق المستهدف (70-180)")
    else:
        parts_ar.append(f"✅ السكر الحالي ({current} mg/dL) في النطاق الآمن (70-180)")

    # الاتجاه
    trend_map = {
        "RAPIDLY_RISING": "⬆️⬆️ يرتفع بسرعة كبيرة",
        "RISING": "⬆️ يرتفع",
        "STABLE": "➡️ مستقر",
        "FALLING": "⬇️ ينخفض",
        "RAPIDLY_FALLING": "⬇️⬇️ ينخفض بسرعة كبيرة"
    }
    parts_ar.append(f"الاتجاه: {trend_map.get(trend, trend)} (بسرعة {abs(velocity):.1f} mg/dL في الدقيقة)")

    # التنبؤ
    if predicted:
        if predicted < 70:
            parts_ar.append(f"⚠️ متوقع أن ينخفض إلى {predicted:.0f} mg/dL خلال 30 دقيقة")
        elif predicted > 250:
            parts_ar.append(f"⚠️ متوقع أن يرتفع إلى {predicted:.0f} mg/dL خلال 30 دقيقة")
        else:
            parts_ar.append(f"التنبؤ: {predicted:.0f} mg/dL خلال 30 دقيقة")

    return " | ".join(parts_ar)