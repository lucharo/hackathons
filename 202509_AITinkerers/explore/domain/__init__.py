"""Small façade that exposes the explore sandbox helpers."""

from .groceries import ProgressCallback, groceries_checkout
from .models import (
    CoachState,
    FoodPrefs,
    Goal,
    Ingredient,
    Profile,
    Recipe,
    WeekPlan,
    aggregate_ingredients,
    compute_targets,
)
from .parsers import update_prefs_from_text, update_profile_from_text
from .planner import DEFAULT_BREAKFASTS, DEFAULT_MAINS, generate_week_plan

__all__ = [
    "CoachState",
    "FoodPrefs",
    "Goal",
    "Ingredient",
    "Profile",
    "Recipe",
    "WeekPlan",
    "compute_targets",
    "aggregate_ingredients",
    "update_profile_from_text",
    "update_prefs_from_text",
    "generate_week_plan",
    "DEFAULT_BREAKFASTS",
    "DEFAULT_MAINS",
    "groceries_checkout",
    "ProgressCallback",
]
