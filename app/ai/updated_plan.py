"""Revises an existing workout plan based on user feedback, using Gemini Pro."""

import logging

from google.genai import types

from ..config import settings
from ..schemas import UserInput, WorkoutPlan
from .client import get_client

logger = logging.getLogger(__name__)


def _build_prompt(
    user_input: UserInput,
    current_plan: WorkoutPlan,
    feedback: str,
) -> str:
    return f"""
You are a professional fitness trainer revising an existing 7-day workout
plan based on client feedback.

Client goal: {user_input.goal}
Client intensity preference: {user_input.intensity}

Current plan (JSON):
{current_plan.model_dump_json(indent=2)}

Client feedback:
"{feedback}"

Revise the plan to address this feedback while keeping it safe, balanced,
and appropriate for the client's goal and intensity. Keep the same JSON
structure. Return exactly 7 days.
""".strip()


async def update_workout_plan(
    user_input: UserInput,
    current_plan: WorkoutPlan,
    feedback: str,
) -> tuple[WorkoutPlan, bool]:
    """
    Returns (updated_plan, demo_mode).
    demo_mode=True means Gemini could not be reached, so the original
    plan was returned unchanged instead of a revision.
    """

    try:
        client = get_client()

        response = await client.aio.models.generate_content(
            model=settings.gemini_workout_model,
            contents=_build_prompt(user_input, current_plan, feedback),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=WorkoutPlan,
            ),
        )

        updated_plan = WorkoutPlan.model_validate_json(response.text)
        return updated_plan, False

    except Exception:
        logger.exception("Gemini plan update failed, returning original plan.")
        return current_plan, True
