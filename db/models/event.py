from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from db.models.base import Base
from datetime import datetime
import uuid

class BehavioralEvent(Base):
    __tablename__ = "behavioral_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String, nullable=False) # 'meal', 'insulin', 'exercise', 'sleep'
    details = Column(JSON, nullable=True) # e.g. {"carbs_g": 50, "food_name": "Rice"}
    
    patient = relationship("Patient", back_populates="events")
