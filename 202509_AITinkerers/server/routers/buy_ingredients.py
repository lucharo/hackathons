"""Buy ingredients API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from models.meal_planning import Meal, IngredientList
from llm.client import BaseLLMClient, Message

router = APIRouter(prefix="/buy-ingredients", tags=["buy-ingredients"])


class IngredientListRequest(BaseModel):
    meals: list[Meal]


@router.post("/generate", response_model=IngredientList)
async def generate_ingredient_list(request: IngredientListRequest):
    """Generate an ingredient list from the provided meals."""
    try:
        # Format meals for better readability
        meals_json = "\n".join([meal.model_dump_json() for meal in request.meals])
        
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

        return generated_ingredient_list
    
    except Exception as e:
        print(f"Error generating ingredient list: {e}")
        raise


@router.post("/buy-ingredients")
async def buy_ingredients(request: IngredientListRequest):
    """Buy ingredients for the meal plan."""
    try:

        client = BaseLLMClient('claude-sonnet-4-20250514')
        messages = [Message(role='user', content='First search for pasta products on Picnic. Then try to add 2-3 different pasta products to my cart. If any fail to add, that\'s okay - just tell me which ones worked and which ones didn\'t. Also show me my current cart contents.')]
        response = await client.chat_completion(messages)
        print(response)

        return request.ingredients
    except Exception as e:
        print(f"Error buying ingredients: {e}")
        raise
