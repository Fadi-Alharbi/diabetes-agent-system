from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import relationship
from db.models.base import Base
from datetime import datetime
import uuid

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_type = Column(String, nullable=False) # e.g. type_2, healthy, hypo_prone, high_carb
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    readings = relationship("GlucoseReading", back_populates="patient", cascade="all, delete-orphan")
    events = relationship("BehavioralEvent", back_populates="patient", cascade="all, delete-orphan")
    food_profiles = relationship("FoodProfile", back_populates="patient", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="patient", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="patient", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="patient", cascade="all, delete-orphan")
