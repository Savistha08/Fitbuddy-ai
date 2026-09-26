"""Generates a quick nutrition/recovery tip using Gemini Flash."""

import logging

from google.genai import types

from ..config import settings
from ..schemas import NutritionTip, UserInput
from .client import get_client

logger = logging.getLogger(__name__)


_DEMO_TIPS = {
    "weight loss": "Prioritize protein and vegetables at each meal to stay full on fewer calories.",
    "muscle gain": "Aim for a good source of protein (chicken, fish, beans, or Greek yogurt) with every meal.",
    "general wellness": "Stay hydrated and aim for a colorful plate with plenty of vegetables.",
    "flexibility": "Warm up before stretching and never stretch to the point of sharp pain.",
    "endurance": "Refuel with carbs and protein within an hour after long sessions to aid recovery.",
}


def _demo_tip(user_input: UserInput) -> NutritionTip:
    return NutritionTip(
        tip=_DEMO_TIPS.get(
            user_input.goal,
            "Stay hydrated and eat a balanced diet to support your training.",
        ),
        recovery_note=(
            "Gemini was unavailable, so this is a placeholder tip — "
            "try again once your API key/network is working."
        ),
    )


def _build_prompt(user_input: UserInput) -> str:
    return (
        f"Give one clear, practical nutrition or recovery tip for someone "
        f"focused on '{user_input.goal}' training at '{user_input.intensity}' "
        f"intensity. The tip should be friendly, specific, and easy to "
        f"follow. Also include one short recovery note (e.g. sleep, "
        f"hydration, or stretching advice)."
    )


async def generate_nutrition_tip_with_flash(
    user_input: UserInput,
) -> tuple[NutritionTip, bool]:
    """
    Returns (tip, demo_mode).
    demo_mode=True means Gemini could not be reached, so a safe
    placeholder tip was returned instead.
    """

    try:
        client = get_client()

        response = await client.aio.models.generate_content(
            model=settings.gemini_tip_model,
            contents=_build_prompt(user_input),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=NutritionTip,
            ),
        )

        tip = NutritionTip.model_validate_json(response.text)
        return tip, False

    except Exception:
        logger.exception("Gemini nutrition tip generation failed, using demo tip.")
        return _demo_tip(user_input), True
