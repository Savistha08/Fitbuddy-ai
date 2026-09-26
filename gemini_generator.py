"""Generates the initial 7-day workout plan using Gemini Pro."""

import logging

from google.genai import types

from ..config import settings
from ..schemas import DayPlan, ExerciseItem, UserInput, WorkoutPlan
from .client import get_client

logger = logging.getLogger(__name__)


def _demo_plan(user_input: UserInput) -> WorkoutPlan:
    """
    Safe fallback plan, used only if the Gemini call fails (bad API key,
    network issue, quota, etc.) so the app never crashes for the user.
    """

    days = []
    for i in range(1, 8):
        rest_day = i % 4 == 0

        days.append(
            DayPlan(
                day=f"Day {i}",
                focus="Active Recovery" if rest_day else "Full Body",
                warm_up="5-10 min light cardio and dynamic stretching.",
                exercises=[
                    ExerciseItem(
                        name="Rest / light walk" if rest_day else "Bodyweight Squats",
                        sets_or_duration="20-30 min" if rest_day else "3 sets of 12 reps",
                        rest="-" if rest_day else "60 sec",
                        notes="Keep it light and easy on your body.",
                    ),
                    ExerciseItem(
                        name="Stretching" if rest_day else "Push-ups",
                        sets_or_duration="10-15 min" if rest_day else "3 sets of 10 reps",
                        rest="-" if rest_day else "60 sec",
                        notes="Modify on knees if needed." if not rest_day else "Focus on breathing.",
                    ),
                ],
                cooldown="5 min static stretching, focus on major muscle groups.",
            )
        )

    return WorkoutPlan(
        overview=(
            f"Demo 7-day {user_input.intensity}-intensity plan for "
            f"{user_input.goal} (Gemini was unavailable, so this is a "
            f"placeholder plan — try again once your API key/network is working)."
        ),
        safety_note="Consult a doctor before starting any new fitness routine.",
        days=days,
    )


def _build_prompt(user_input: UserInput) -> str:
    return f"""
You are a professional, encouraging fitness trainer.

Create a personalized, structured 7-day workout plan for a client with:
- Goal: {user_input.goal}
- Preferred intensity: {user_input.intensity}
- Age: {user_input.age}
- Weight: {user_input.weight_kg} kg

Requirements for EVERY one of the 7 days:
- A short warm-up (5-10 minutes)
- A main workout: a list of specific exercises, each with sets/reps OR a
  duration, a rest interval, and a one-line coaching note
- A cooldown or recovery tip
- Vary the focus across the week (e.g. upper body, lower body, cardio,
  core, flexibility, rest/active recovery) so it isn't repetitive
- Keep the difficulty appropriate for the requested intensity level

Also include:
- A short overview (2-3 sentences) summarizing the plan and how it
  matches the client's goal
- A one-sentence safety note

Return exactly 7 days.
""".strip()


async def generate_workout_gemini(
    user_input: UserInput,
) -> tuple[WorkoutPlan, bool]:
    """
    Returns (plan, demo_mode).
    demo_mode=True means Gemini could not be reached, so a safe
    placeholder plan was returned instead.
    """

    try:
        client = get_client()

        response = await client.aio.models.generate_content(
            model=settings.gemini_workout_model,
            contents=_build_prompt(user_input),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=WorkoutPlan,
            ),
        )

        plan = WorkoutPlan.model_validate_json(response.text)
        return plan, False

    except Exception:
        logger.exception("Gemini workout generation failed, using demo plan.")
        return _demo_plan(user_input), True
