from sqlalchemy import Column, Integer, String, Text

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    name = Column(String)
    age = Column(Integer)
    weight_kg = Column(String)
    goal = Column(String)
    intensity = Column(String)
    original_plan = Column(Text)
    updated_plan = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
