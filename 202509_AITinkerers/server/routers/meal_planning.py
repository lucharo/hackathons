"""Meal planning API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from models.meal_planning import MealPlan

router = APIRouter(prefix="/meal-planning", tags=["meal-planning"])


class MealPlanRequest(BaseModel):
    meal_types: list[str]
    dietary_preferences: list[str]
    goals: list[str]


@router.post("/generate", response_model=MealPlan)
async def generate_meal_plan(request: MealPlanRequest):
    """Generate a personalized meal plan based on user preferences."""
    # TODO: Implement actual meal plan generation logic
    # For now, return a mock response
    from models.meal_planning import Meal, MealType, DietaryType, Nutrition

    mock_meals = []

    # Generate mock meals based on selected meal types
    if "breakfast" in request.meal_types:
        mock_meals.append(Meal(
            description="Overnight oats with fresh berries and almonds",
            num_servings=1,
            nutrition=Nutrition(calories=350, grams_protein=12.0, grams_carbs=45.0, grams_fat=15.0),
            meal_type=MealType.BREAKFAST,
            diet_type=DietaryType.VEGETARIAN if "vegetarian" in request.dietary_preferences else DietaryType.GLUTEN_FREE,
            allergens=["nuts"] if "nuts" not in request.dietary_preferences else []
        ))

    if "lunch" in request.meal_types:
        mock_meals.append(Meal(
            description="Quinoa bowl with roasted vegetables and tahini dressing",
            num_servings=1,
            nutrition=Nutrition(calories=420, grams_protein=15.0, grams_carbs=55.0, grams_fat=18.0),
            meal_type=MealType.LUNCH,
            diet_type=DietaryType.VEGAN if "vegan" in request.dietary_preferences else DietaryType.VEGETARIAN,
            allergens=["sesame"]
        ))

    if "dinner" in request.meal_types:
        mock_meals.append(Meal(
            description="Grilled salmon with sweet potato and steamed broccoli",
            num_servings=1,
            nutrition=Nutrition(calories=480, grams_protein=32.0, grams_carbs=35.0, grams_fat=22.0),
            meal_type=MealType.DINNER,
            diet_type=DietaryType.PESCATARIAN if "pescatarian" in request.dietary_preferences else DietaryType.GLUTEN_FREE,
            allergens=["fish"]
        ))

    return MealPlan(meals=mock_meals)
