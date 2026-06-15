from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime 
from typing import List, Optional, Dict, Any
from backend.models.glucose import GlucoseReading, BehavioralEvent

class PatientState(BaseModel):
    patient_id: str
    current_reading: GlucoseReading
    historical_readings: List[GlucoseReading] = Field(default_factory=list)
    recent_events: List[BehavioralEvent] = Field(default_factory=list)
    # مخرجات الوكلاء يتم تحديثها ديناميكيًا هنا
    metrics: Dict[str, Any] = Field(default_factory=dict) # مثل الجلوكوز في النطاق TIR
    computed_trend: Optional[str] = None                   # مخرج الـ Trend Agent
    predicted_glucose_30m: Optional[float] = None          # مخرج الـ Prediction Agent
    behavioral_insights: List[str] = Field(default_factory=list) # مخرج الـ Behavior Agent
    risk_level: Optional[str] = None                      # مخرج الـ Risk Agent
    final_decision: Dict[str, Any] = Field(default_factory=dict) # مخرج الـ Decision Engine

class BaseAgent(ABC):
    def __init__(self, agent_name: str):
        self.agent_name = agent_name

    @abstractmethod
    async def process(self, state: PatientState) -> PatientState:
        """كل وكيل يجب أن ينفذ هذه الدالة لاستقبال الحالة وتحديثها بمخرجاته الخاصة"""
        pass