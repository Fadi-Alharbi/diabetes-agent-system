from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from db.models.base import Base
from datetime import datetime
import uuid

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    clinical_guidance = Column(String, nullable=False)
    rationale = Column(String, nullable=False)
    shap_values = Column(JSON, nullable=True) # Explainable AI output
    
    patient = relationship("Patient", back_populates="recommendations")
