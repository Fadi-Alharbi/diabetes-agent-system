from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.models.base import Base
from datetime import datetime
import uuid

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    risk_level = Column(String, nullable=False) # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    reasoning = Column(String, nullable=False)
    
    patient = relationship("Patient", back_populates="risk_assessments")
