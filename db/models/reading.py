from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.models.base import Base
from datetime import datetime
import uuid

class GlucoseReading(Base):
    __tablename__ = "glucose_readings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    glucose_value = Column(Float, nullable=False)
    
    patient = relationship("Patient", back_populates="readings")
