"""Buy ingredients API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel
from models.meal_planning import Meal, IngredientList
from llm.client import BaseLLMClient, Message
from config import settings

router = APIRouter(tags=["buy-ingredients"])


class IngredientListRequest(BaseModel):
    meals: list[Meal]


@router.post("/buy-ingredients/generate", response_model=IngredientList)
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


class BuyIngredientsResponse(BaseModel):
    success: bool
    message: str


@router.post("/buy-ingredients", response_model=BuyIngredientsResponse)
async def buy_ingredients(request: IngredientListRequest):
    """Add ingredients to Picnic cart using MCP integration."""
    try:
        # Check if MCP is enabled
        if not settings.enable_mcp:
            return BuyIngredientsResponse(
                success=False,
                message="Picnic integration is not available in this environment. Please use the copy button to get your shopping list instead."
            )
        # First, generate ingredient list from meals
        llm_client = BaseLLMClient(model="claude-sonnet-4-20250514")

        # Format meals for ingredient extraction
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

        # Generate ingredient list
        generated_ingredient_list = await llm_client.chat_completion(
            messages=[
                Message(role="system", content="You are a helpful assistant that parses out ingredients from meals."),
                Message(role="user", content=parse_ingredient_list_prompt.strip())
            ],
            response_model=IngredientList
        )

        # Format ingredient list for shopping
        ingredients_text = "\n".join([
            f"• {ingredient.name} - {ingredient.qty} {ingredient.unit}"
            for ingredient in generated_ingredient_list.ingredients
        ])

        # Now use MCP to add ingredients to cart
        shopping_prompt = f"""I have a shopping list of ingredients that I need to buy. Please help me by:

1. Searching for each ingredient on Picnic
2. Adding available items to my Picnic cart
3. If an item fails to add (422 error, out of stock, not found, etc.), that's completely normal - just continue with the next item
4. Keep track of successes and failures
5. At the end, provide a detailed summary of:
   - How many items you successfully added to cart
   - Which specific items were added
   - Which items couldn't be added and why
   - Total items processed

Here's my shopping list:
{ingredients_text}

IMPORTANT: Don't stop if some items fail to add - this is expected behavior. Continue processing all items and give me a complete summary at the end. Some items might be out of stock or unavailable in my region, and that's perfectly fine."""

        response = await llm_client.chat_completion(
            messages=[
                Message(role="system", content="You are a helpful grocery shopping assistant that uses Picnic MCP tools to search for products and add them to cart."),
                Message(role="user", content=shopping_prompt)
            ]
        )

        return BuyIngredientsResponse(
            success=True,
            message=response
        )

    except Exception as e:
        print(f"Error buying ingredients: {e}")
        return BuyIngredientsResponse(
            success=False,
            message=f"Failed to add ingredients to cart: {str(e)}"
        )
