from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, Text, DateTime

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)

    age = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)

    goal = Column(String(50), nullable=False)
    intensity = Column(String(20), nullable=False)

    original_plan = Column(Text, nullable=True)
    updated_plan = Column(Text, nullable=True)

    nutrition_tip = Column(Text, nullable=True)
    latest_feedback = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )