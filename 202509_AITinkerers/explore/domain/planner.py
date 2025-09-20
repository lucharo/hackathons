"""Deterministic plan generation for the explore sandbox."""

from __future__ import annotations

from typing import List, Tuple

from .models import CoachState, Ingredient, Recipe, WeekPlan, aggregate_ingredients

DEFAULT_BREAKFASTS = [
    "Overnight oats",
    "Tofu scramble",
]
DEFAULT_MAINS = [
    "Chickpea curry",
    "Lentil tacos",
    "Veggie stir fry",
]


def _recipe_from_name(name: str, calories: int) -> Recipe:
    title = name.title()
    ingredients = [
        Ingredient(name=title, qty=1.0, unit="serving"),
        Ingredient(name="Mixed veggies", qty=1.0, unit="cup"),
        Ingredient(name="Olive oil", qty=1.0, unit="tbsp"),
    ]
    steps = [
        f"Prep ingredients for {title}.",
        f"Cook {title} until ready and serve.",
    ]
    return Recipe(title=title, servings=2, calories_per_serving=calories, ingredients=ingredients, steps=steps)


def generate_week_plan(state: CoachState) -> Tuple[WeekPlan, List[Ingredient], str]:
    breakfasts_like = state.prefs.breakfasts_like or DEFAULT_BREAKFASTS
    mains_like = state.prefs.mains_like or DEFAULT_MAINS

    if len(breakfasts_like) < 2:
        breakfasts_like = (breakfasts_like + DEFAULT_BREAKFASTS)[:2]
    if len(mains_like) < 3:
        mains_like = (mains_like + DEFAULT_MAINS)[:3]

    breakfast_recipes = [_recipe_from_name(name, 400) for name in breakfasts_like[:2]]
    main_recipes = [_recipe_from_name(name, 650) for name in mains_like[:3]]

    combined = breakfast_recipes + main_recipes
    shopping_list = aggregate_ingredients(combined)

    target = state.target_calories or 2000
    tdee = state.tdee or 2200

    plan = WeekPlan(
        breakfasts=breakfast_recipes,
        mains=main_recipes,
        target_calories=target,
        tdee=tdee,
    )

    say = (
        "Your weekly plan is ready! Here's the game plan:\n"
        f" - Daily target: {target} kcal (maintenance ~{tdee} kcal).\n"
        f" - Breakfast rotation: {', '.join(recipe.title for recipe in breakfast_recipes)}.\n"
        f" - Mains lineup: {', '.join(recipe.title for recipe in main_recipes)}.\n"
        "I'll also include a consolidated shopping list and a quick cart link so you can check out in one go."
    )

    return plan, shopping_list, say


__all__ = [
    "DEFAULT_BREAKFASTS",
    "DEFAULT_MAINS",
    "generate_week_plan",
]
