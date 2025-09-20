"""Shared domain models, helpers, and LLM agents for Prototype 1."""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Dict, List, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent

load_dotenv()

DEFAULT_MODEL = "anthropic:claude-sonnet-4-20250514"
BASE_MODEL = os.environ.get("BASE_MODEL", DEFAULT_MODEL)

Activity = Literal["sedentary", "light", "moderate", "very", "extreme"]
Direction = Literal["loss", "gain"]
RateCat = Literal["low", "mid", "fast"]


class Profile(BaseModel):
    sex: Optional[Literal["male", "female"]] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity: Optional[Activity] = None


class Goal(BaseModel):
    direction: Optional[Direction] = None
    rate_category: Optional[RateCat] = None
    weeks: Optional[int] = None
    target_delta_kg: Optional[float] = None


class FoodPrefs(BaseModel):
    dislikes: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    cuisines: List[str] = Field(default_factory=list)
    breakfasts_like: List[str] = Field(default_factory=list)
    mains_like: List[str] = Field(default_factory=list)


class Ingredient(BaseModel):
    name: str
    qty: float
    unit: str


class Recipe(BaseModel):
    title: str
    servings: int
    calories_per_serving: int
    ingredients: List[Ingredient]
    steps: List[str]


class WeekPlan(BaseModel):
    breakfasts: List[Recipe]
    mains: List[Recipe]
    target_calories: int
    tdee: int


class CoachState(BaseModel):
    profile: Profile = Field(default_factory=Profile)
    goal: Goal = Field(default_factory=Goal)
    prefs: FoodPrefs = Field(default_factory=FoodPrefs)
    tdee: Optional[int] = None
    target_calories: Optional[int] = None
    plan: Optional[WeekPlan] = None
    cart_url: Optional[str] = None


ACTIVITY_FACTOR: Dict[Activity, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "very": 1.725,
    "extreme": 1.9,
}

LOSS_RATES = {"low": 0.25, "mid": 0.5, "fast": 0.75}
GAIN_RATES = {"low": 0.125, "mid": 0.25, "fast": 0.5}
KCAL_PER_KG = 7700.0


def mifflin_st_jeor(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    """Return resting metabolic rate (kcal/day) via Mifflin–St Jeor."""

    adjustment = 5 if sex == "male" else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + adjustment


def tdee_from_profile(profile: Profile) -> int:
    """Compute total daily energy expenditure from profile data."""

    if not profile.sex or profile.age is None:
        raise ValueError("Profile missing sex or age for TDEE calculation")
    if profile.height_cm is None or profile.weight_kg is None:
        raise ValueError("Profile missing height or weight for TDEE calculation")

    bmr = mifflin_st_jeor(profile.sex, profile.weight_kg, profile.height_cm, profile.age)
    activity = profile.activity or "moderate"
    return int(round(bmr * ACTIVITY_FACTOR[activity]))


def daily_calorie_delta(direction: Direction, rate: RateCat) -> float:
    """Return daily kcal surplus/deficit for the chosen rate category."""

    rates = LOSS_RATES if direction == "loss" else GAIN_RATES
    kg_per_week = rates[rate]
    return (kg_per_week * KCAL_PER_KG) / 7.0


def compute_targets(state: CoachState) -> CoachState:
    """Populate maintenance and goal calorie targets on the provided state."""

    if not state.profile.sex:
        raise ValueError("Profile sex required before computing targets")
    if state.goal.direction is None or state.goal.rate_category is None:
        raise ValueError("Goal direction and rate required before computing targets")

    tdee = tdee_from_profile(state.profile)
    delta = daily_calorie_delta(state.goal.direction, state.goal.rate_category)
    target = tdee - delta if state.goal.direction == "loss" else tdee + delta
    state.tdee = tdee
    state.target_calories = int(round(target))
    return state


class CollectOut(BaseModel):
    say: str
    profile: Profile = Field(default_factory=Profile)
    goal: Goal = Field(default_factory=Goal)
    prefs: FoodPrefs = Field(default_factory=FoodPrefs)


collect_agent = Agent(
    BASE_MODEL,
    system_prompt=(
        "You are a concise nutrition intake assistant.\n"
        "Update only the profile, goal, and food preference fields you can infer from the latest reply.\n"
        "Ask exactly one short follow-up question when mandatory data is missing.\n"
        "Mandatory before advancing: sex (male/female), age, height_cm, weight_kg, activity level, direction (loss/gain), rate_category (low/mid/fast).\n"
        "When prompted for preferences, elicit two breakfasts and three lunch/dinner ideas, plus allergies or dislikes."
    ),
    output_type=CollectOut,
)


class RecipesOut(BaseModel):
    say: str
    breakfasts: List[Recipe]
    mains: List[Recipe]


recipes_agent = Agent(
    BASE_MODEL,
    system_prompt=(
        "Generate exactly two breakfast recipes and three lunch/dinner recipes.\n"
        "Each Recipe must include servings, calories_per_serving, ingredients with numeric qty + unit, and clear steps.\n"
        "Keep combined daily calories aligned with the provided target and respect dislikes/allergies/cuisine hints."
    ),
    output_type=RecipesOut,
)


def aggregate_ingredients(recipes: List[Recipe]) -> List[Ingredient]:
    """Combine ingredient quantities across all recipes."""

    accumulator: Dict[tuple[str, str], float] = defaultdict(float)
    for recipe in recipes:
        for item in recipe.ingredients:
            key = (item.name.lower(), item.unit)
            accumulator[key] += item.qty
    return [
        Ingredient(name=name, qty=round(qty, 2), unit=unit)
        for (name, unit), qty in accumulator.items()
    ]


def groceries_checkout(ingredients: List[Ingredient]) -> str:
    """Placeholder for an MCP-backed grocery checkout call."""

    return "https://example.com/demo-cart"


__all__ = [
    "Activity",
    "CoachState",
    "CollectOut",
    "Direction",
    "FoodPrefs",
    "Goal",
    "Ingredient",
    "Profile",
    "RateCat",
    "Recipe",
    "RecipesOut",
    "WeekPlan",
    "aggregate_ingredients",
    "collect_agent",
    "compute_targets",
    "daily_calorie_delta",
    "groceries_checkout",
    "mifflin_st_jeor",
    "recipes_agent",
    "tdee_from_profile",
]
