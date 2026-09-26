from typing import Literal

from pydantic import BaseModel, Field, field_validator


Goal = Literal[
    "general wellness",
    "muscle gain",
    "weight loss",
    "flexibility",
    "endurance"
]

Intensity = Literal["low", "medium", "high"]


class UserInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    user_id: str = Field(
        min_length=2,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$"
    )
    age: int = Field(ge=13, le=100)
    weight_kg: float = Field(gt=0, le=500)
    goal: Goal
    intensity: Intensity

    @field_validator("name", "user_id")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class FeedbackRequest(BaseModel):
    user_id: str = Field(min_length=2, max_length=64)
    feedback: str = Field(min_length=3, max_length=2000)


class ExerciseItem(BaseModel):
    name: str
    sets_or_duration: str
    rest: str
    notes: str


class DayPlan(BaseModel):
    day: str
    focus: str
    warm_up: str
    exercises: list[ExerciseItem]
    cooldown: str


class WorkoutPlan(BaseModel):
    overview: str
    safety_note: str
    days: list[DayPlan] = Field(min_length=7, max_length=7)


class NutritionTip(BaseModel):
    tip: str
    recovery_note: str


class PlanResponse(BaseModel):
    user_id: str
    name: str
    goal: str
    intensity: str
    workout_plan: WorkoutPlan
    nutrition_tip: NutritionTip
    demo_mode: bool = False