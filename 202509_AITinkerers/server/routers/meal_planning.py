"""Meal planning API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from models.meal_planning import MealPlan
from llm.client import BaseLLMClient, Message

router = APIRouter(prefix="/meal-planning", tags=["meal-planning"])


class MealPlanRequest(BaseModel):
    meal_types: list[str]
    dietary_preferences: list[str]
    goals: list[str]


@router.post("/generate", response_model=MealPlan)
async def generate_meal_plan(request: MealPlanRequest):
    """Generate a personalized meal plan based on user preferences."""
    try:
        generate_meal_plan_prompt = f"""
        A user wants to generate a meal plan based on the following preferences:
        Meal types: {request.meal_types}
        Dietary preferences: {request.dietary_preferences}
        Goals: {request.goals}

        In total, please generate 2 different breakfasts and 3 different lunch/dinner recipes.
        The total number of breakfast servings should be 5 and the total number of lunch/dinner servings should be 10.

        Please return the meal plan in the following format:
        {MealPlan.model_json_schema()}
        """

        llm_client = BaseLLMClient(model="claude-sonnet-4-20250514")

        generated_plan = await llm_client.chat_completion(
            messages=[
                Message(role="system", content="You are a helpful assistant that generates personalized meal plans."),
                Message(role="user", content=generate_meal_plan_prompt)
            ],
            response_model=MealPlan
        )

        print(generated_plan)

        return MealPlan(meals=generated_plan.meals)
    
    except Exception as e:
        print(f"Error generating meal plan: {e}")
        # Return a fallback meal plan or re-raise the exception
        raise
