"""MCP (Model Context Protocol) server API endpoints."""
from fastapi import APIRouter
from models.meal_planning import Meal, IngredientList
from llm.client import BaseLLMClient, Message

router = APIRouter(prefix="/mcp", tags=["mcp"])

async def generate_ingredient_list_from_meal(meal: Meal):
    """Generate a personalized meal plan based on user preferences."""
    try:
        parse_ingredient_list_prompt = f"""
        Given the meal {meal.model_dump_json()} generate for the user, help me parse out a list of ingredients for the meal.
        {IngredientList.model_json_schema()}
        """

        llm_client = BaseLLMClient(model="claude-sonnet-4-20250514")

        generated_ingredient_list = await llm_client.chat_completion(
            messages=[
                Message(role="system", content="You are a helpful assistant that parse out a list of ingredients for a meal."),
                Message(role="user", content=parse_ingredient_list_prompt)
            ],
            response_model=IngredientList
        )

        return generated_ingredient_list.ingredients
    
    except Exception as e:
        print(f"Error generating ingredient list: {e}")
        raise
