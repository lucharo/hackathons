"""Buy ingredients API endpoints."""
from fastapi import APIRouter
from models.meal_planning import Meal, IngredientList
from llm.client import BaseLLMClient, Message

router = APIRouter(prefix="/buy-ingredients", tags=["buy-ingredients"])

async def generate_ingredient_list_from_meals(meals: list[Meal]):
    """Generate a personalized meal plan based on user preferences."""
    try:
        # Format meals for better readability
        meals_json = "\n".join([meal.model_dump_json() for meal in meals])
        
        parse_ingredient_list_prompt = f"""Given the following meals, help me parse out a list of ingredients for all the meals so I can generate a shopping list to cook all the meals.

        Meals:
        {meals_json}

        Please return the ingredients in this format:
        {IngredientList.model_json_schema()}

        Make sure to:
        1. Include all ingredients needed for all meals
        2. Combine similar ingredients (e.g., if multiple meals need "onions", list it once)
        3. Include quantities and units for each ingredient
        4. Consider the number of servings for each meal when calculating quantities"""

        llm_client = BaseLLMClient(model="claude-sonnet-4-20250514")

        generated_ingredient_list = await llm_client.chat_completion(
            messages=[
                Message(role="system", content="You are a helpful assistant that parse out a list of ingredients for a meal."),
                Message(role="user", content=parse_ingredient_list_prompt.strip())
            ],
            response_model=IngredientList
        )

        return generated_ingredient_list.ingredients
    
    except Exception as e:
        print(f"Error generating ingredient list: {e}")
        raise
