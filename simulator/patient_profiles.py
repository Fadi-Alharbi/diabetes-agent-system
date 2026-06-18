"""
ملفات تعريف المرضى الافتراضيين الخمسة
كل ملف تعريف يحدد خصائص المريض الفسيولوجية والسلوكية
التي تُستخدم من قبل الحساس الافتراضي لتوليد بيانات واقعية.
"""

PATIENT_PROFILES = {
    "A": {
        "patient_id": "A",
        "name": "Patient A",
        "name_ar": "المريض أ",
        "profile_type": "high_carb",
        "description": "High-carbohydrate diet, insulin-resistant",
        "description_ar": "نظام غذائي عالي الكربوهيدرات، مقاومة الإنسولين",
        "baseline_glucose": 160.0,
        "meal_multiplier": 1.5,
        "insulin_multiplier": 1.0,
        "exercise_multiplier": 1.0,
        "auto_events": {
            "meal_interval": 20,          # كل 20 خطوة = وجبة عالية الكربوهيدرات
            "meal_carbs": 120,
            "meal_food": "بيتزا / Pizza",
            "insulin_interval": 20,       # يحقن إنسولين مع الوجبة ولكن بجرعة غير كافية
            "insulin_units": 6,
            "exercise_interval": None,     # لا يمارس رياضة
        }
    },
    "B": {
        "patient_id": "B",
        "name": "Patient B",
        "name_ar": "المريض ب",
        "profile_type": "highly_active",
        "description": "Highly active, strong exercise insulin sensitivity",
        "description_ar": "نشاط بدني عالي، حساسية قوية للإنسولين بعد الرياضة",
        "baseline_glucose": 110.0,
        "meal_multiplier": 1.0,
        "insulin_multiplier": 1.0,
        "exercise_multiplier": 1.5,
        "auto_events": {
            "meal_interval": 25,
            "meal_carbs": 60,
            "meal_food": "بروتين شيك / Protein Shake",
            "insulin_interval": None,
            "insulin_units": 0,
            "exercise_interval": 30,       # يمارس رياضة كل 30 خطوة
            "exercise_duration": 60,
            "exercise_intensity": 1.5,
        }
    },
    "C": {
        "patient_id": "C",
        "name": "Patient C",
        "name_ar": "المريض ج",
        "profile_type": "hypo_prone",
        "description": "Frequent hypoglycemia, over-correction pattern",
        "description_ar": "هبوط متكرر في السكر، نمط تصحيح مفرط",
        "baseline_glucose": 85.0,
        "meal_multiplier": 1.0,
        "insulin_multiplier": 1.5,
        "exercise_multiplier": 1.0,
        "auto_events": {
            "meal_interval": 18,
            "meal_carbs": 30,
            "meal_food": "سلطة / Salad",
            "insulin_interval": 15,        # يحقن إنسولين أكثر من اللازم
            "insulin_units": 10,
            "exercise_interval": None,
        }
    },
    "D": {
        "patient_id": "D",
        "name": "Patient D",
        "name_ar": "المريض د",
        "profile_type": "irregular_meals",
        "description": "Irregular meal schedule, nocturnal highs",
        "description_ar": "وجبات غير منتظمة، ارتفاعات ليلية",
        "baseline_glucose": 140.0,
        "meal_multiplier": 1.0,
        "insulin_multiplier": 1.0,
        "exercise_multiplier": 1.0,
        "auto_events": {
            "meal_interval": "random",     # وجبات عشوائية
            "meal_random_chance": 0.05,
            "meal_carbs_range": [30, 100],
            "meal_food": "وجبة خفيفة / Snack",
            "insulin_interval": "random",
            "insulin_random_chance": 0.025,
            "insulin_units_range": [2, 8],
            "exercise_interval": None,
        }
    },
    "E": {
        "patient_id": "E",
        "name": "Patient E",
        "name_ar": "المريض هـ",
        "profile_type": "poor_adherence",
        "description": "Poor medication adherence, large glucose variability",
        "description_ar": "التزام ضعيف بالأدوية، تقلبات كبيرة في السكر",
        "baseline_glucose": 190.0,
        "meal_multiplier": 1.0,
        "insulin_multiplier": 0.5,         # استجابة ضعيفة لأنه لا يلتزم
        "exercise_multiplier": 1.0,
        "auto_events": {
            "meal_interval": 20,
            "meal_carbs": 80,
            "meal_food": "برغر / Burger",
            "insulin_interval": 20,
            "insulin_chance": 0.2,         # يأخذ الإنسولين فقط 20% من الأحيان
            "insulin_units": 5,
            "exercise_interval": None,
        }
    }
}

def get_profile(patient_id: str) -> dict:
    """جلب ملف تعريف مريض بالمعرّف"""
    return PATIENT_PROFILES.get(patient_id, PATIENT_PROFILES["A"])

def get_all_profiles() -> dict:
    """جلب جميع ملفات تعريف المرضى"""
    return PATIENT_PROFILES
