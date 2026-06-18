from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from db.models.base import Base
from datetime import datetime
import uuid

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    forecast_window_mins = Column(Integer, nullable=False) # 30, 60, 120
    predicted_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=True) # Populated later for accuracy tracking
    error_metric = Column(Float, nullable=True)
    model_used = Column(String, nullable=False) # 'LSTM', 'XGBoost', etc.
    
    patient = relationship("Patient", back_populates="predictions")
