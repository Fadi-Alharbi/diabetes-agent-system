from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal

class GlucoseReading(BaseModel):
    """النموذج الطبي لقراءة السكر القادمة من الحساس"""
    patient_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    glucose_value: float = Field(..., description="Glucose level in mg/dL")
    trend_arrow: Optional[str] = None  # مأخوذ من الحساس نفسه إن وجد

class BehavioralEvent(BaseModel):
    """النموذج الطبي لتسجيل الأحداث السلوكية (أكل، إنسولين، رياضة)"""
    patient_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: Literal["meal", "insulin", "exercise", "sleep"]
    details: dict = Field(default_factory=dict, description="e.g., carbs_g, units, intensity")