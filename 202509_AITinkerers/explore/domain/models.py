"""Core data models and calorie helpers for the explore sandbox."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field

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
    adjustment = 5 if sex == "male" else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + adjustment


def tdee_from_profile(profile: Profile) -> int:
    if not profile.sex or profile.age is None:
        raise ValueError("Profile missing sex or age for TDEE calculation")
    if profile.height_cm is None or profile.weight_kg is None:
        raise ValueError("Profile missing height or weight for TDEE calculation")

    bmr = mifflin_st_jeor(profile.sex, profile.weight_kg, profile.height_cm, profile.age)
    activity = profile.activity or "moderate"
    return int(round(bmr * ACTIVITY_FACTOR[activity]))


def daily_calorie_delta(direction: Direction, rate: RateCat) -> float:
    rates = LOSS_RATES if direction == "loss" else GAIN_RATES
    kg_per_week = rates[rate]
    return (kg_per_week * KCAL_PER_KG) / 7.0


def compute_targets(state: CoachState) -> CoachState:
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


def aggregate_ingredients(recipes: List[Recipe]) -> List[Ingredient]:
    accumulator: Dict[tuple[str, str], float] = defaultdict(float)
    for recipe in recipes:
        for item in recipe.ingredients:
            key = (item.name.lower(), item.unit)
            accumulator[key] += item.qty
    return [
        Ingredient(name=name, qty=round(qty, 2), unit=unit)
        for (name, unit), qty in accumulator.items()
    ]


__all__ = [
    "Activity",
    "ACTIVITY_FACTOR",
    "CoachState",
    "FoodPrefs",
    "GAIN_RATES",
    "Goal",
    "Ingredient",
    "KCAL_PER_KG",
    "LOSS_RATES",
    "Profile",
    "RateCat",
    "Recipe",
    "WeekPlan",
    "aggregate_ingredients",
    "compute_targets",
    "daily_calorie_delta",
    "mifflin_st_jeor",
    "tdee_from_profile",
]
