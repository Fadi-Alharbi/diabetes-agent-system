from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from db.models.base import Base
import uuid

class FoodProfile(Base):
    __tablename__ = "food_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    food_name = Column(String, nullable=False)
    avg_rise_mgdl = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False) # 0.0 to 1.0
    impact_level = Column(String, nullable=False) # 'LOW', 'MEDIUM', 'HIGH'
    
    patient = relationship("Patient", back_populates="food_profiles")
