"""Simple text-to-state helpers for the explore sandbox."""

from __future__ import annotations

import re
from typing import List, Optional

from .models import CoachState, compute_targets


def _extract_number(pattern: str, text: str) -> Optional[float]:
    match = re.search(pattern, text)
    if not match:
        return None
    try:
        return float(match.group(1))
    except (TypeError, ValueError):
        return None


def update_profile_from_text(state: CoachState, message: str) -> str:
    """Fill known profile and goal fields from natural language text."""

    lower = message.lower()

    if "female" in lower:
        state.profile.sex = "female"
    elif "male" in lower:
        state.profile.sex = "male"

    age = _extract_number(r"(\d{2})\s*(?:years?|yo|yr)", lower)
    if age is not None:
        state.profile.age = int(age)

    height = _extract_number(r"(\d{3})\s*(?:cm|centimet)", lower)
    if height is not None:
        state.profile.height_cm = height

    weight = _extract_number(r"(\d{2,3}(?:\.\d+)?)\s*(?:kg|kilogram)", lower)
    if weight is not None:
        state.profile.weight_kg = weight

    if "sedentary" in lower:
        state.profile.activity = "sedentary"
    elif "light" in lower:
        state.profile.activity = "light"
    elif "moderate" in lower or "active" in lower:
        state.profile.activity = "moderate"
    elif "very" in lower:
        state.profile.activity = "very"
    elif "extreme" in lower:
        state.profile.activity = "extreme"

    if any(keyword in lower for keyword in ["lose", "deficit", "cut", "fat loss"]):
        state.goal.direction = "loss"
    elif any(keyword in lower for keyword in ["gain", "bulk", "surplus"]):
        state.goal.direction = "gain"

    if "fast" in lower or "quick" in lower:
        state.goal.rate_category = "fast"
    elif any(keyword in lower for keyword in ["slow", "steady", "gradual"]):
        state.goal.rate_category = "low"
    elif state.goal.rate_category is None:
        state.goal.rate_category = "mid"

    missing: List[str] = []
    if not state.profile.sex:
        missing.append("sex")
    if state.profile.age is None:
        missing.append("age")
    if state.profile.height_cm is None:
        missing.append("height (cm)")
    if state.profile.weight_kg is None:
        missing.append("weight (kg)")
    if not state.profile.activity:
        missing.append("activity level")
    if not state.goal.direction:
        missing.append("goal (lose/gain weight)")

    if missing:
        needed = ", ".join(missing)
        return f"Thanks! I still need: {needed}."

    try:
        compute_targets(state)
    except ValueError:
        pass

    tdee = state.tdee or 2000
    target = state.target_calories or (tdee - 400 if state.goal.direction == "loss" else tdee + 400)

    return (
        f"Great. Maintenance is about {tdee} kcal/day. "
        f"Target is roughly {target} kcal/day. "
        "Tell me two breakfasts and three lunch or dinner ideas you enjoy."
    )


def update_prefs_from_text(state: CoachState, message: str) -> str:
    """Capture preferences and allergies from a short free-text message."""

    raw_items = [item.strip(" .") for item in re.split(r"[\n,;]+", message) if item.strip()]
    foods: List[str] = []

    for item in raw_items:
        lower = item.lower()
        if lower.startswith("no "):
            entry = item[3:].strip()
            if entry and entry not in state.prefs.dislikes:
                state.prefs.dislikes.append(entry)
            continue
        if "allerg" in lower:
            if item not in state.prefs.allergies:
                state.prefs.allergies.append(item)
            continue
        foods.append(item)

    unique_foods: List[str] = []
    for name in foods:
        if name and name not in unique_foods:
            unique_foods.append(name)

    breakfasts = unique_foods[:2]
    mains = unique_foods[2:5]

    if breakfasts:
        state.prefs.breakfasts_like = breakfasts
    if mains:
        state.prefs.mains_like = mains

    if len(state.prefs.breakfasts_like) < 2 or len(state.prefs.mains_like) < 3:
        return (
            "Great start! Please list at least two breakfasts and three mains you enjoy, "
            "plus any dislikes with 'no ...' statements."
        )

    return "Awesome, I have your preferences. Ready to build this week's plan and shopping list?"


__all__ = [
    "update_prefs_from_text",
    "update_profile_from_text",
]
