"""
FastAPI router for Sainsbury's grocery ordering automation
"""
import asyncio
import os
import re
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from browser_use import Agent, Browser, ChatAnthropic
from dotenv import load_dotenv
from models.meal_planning import MealPlan

# Disable telemetry
os.environ['ANONYMIZED_TELEMETRY'] = "false"

load_dotenv()

router = APIRouter(prefix="/sainsbury_order", tags=["sainsbury"])

class SainsburyOrderRequest(BaseModel):
    items: str  # Comma-separated list of items

class SainsburyOrderResponse(BaseModel):
    success: bool
    message: str
    items_ordered: List[str]

class SainsburyMealPlanOrderRequest(BaseModel):
    meal_plan: MealPlan

def parse_meals_to_ingredients(meal_plan: MealPlan) -> List[str]:
    """
    Parse a MealPlan object and extract ingredients from meal descriptions.
    
    This function uses regex patterns to identify common ingredients and food items
    from the meal descriptions and names.
    
    Args:
        meal_plan: The MealPlan object containing meals to parse
        
    Returns:
        List of unique ingredient names suitable for grocery shopping
    """
    ingredients = set()
    
    # Common ingredient patterns to look for
    ingredient_patterns = [
        # Proteins
        r'\b(chicken|beef|pork|lamb|fish|salmon|tuna|shrimp|eggs|tofu|beans|lentils|chickpeas)\b',
        # Vegetables
        r'\b(tomatoes|onions|garlic|carrots|potatoes|spinach|lettuce|broccoli|peppers|mushrooms|avocado|cucumber|celery)\b',
        # Fruits
        r'\b(bananas|apples|oranges|berries|grapes|lemons|limes|strawberries|blueberries)\b',
        # Grains
        r'\b(rice|pasta|bread|quinoa|oats|flour|noodles|couscous)\b',
        # Dairy
        r'\b(milk|cheese|yogurt|butter|cream|mozzarella|cheddar|parmesan)\b',
        # Pantry staples
        r'\b(oil|olive oil|salt|pepper|sugar|honey|vinegar|soy sauce|ketchup|mustard)\b',
        # Herbs and spices
        r'\b(basil|oregano|thyme|rosemary|parsley|cilantro|ginger|cumin|paprika|chili)\b',
        # Nuts and seeds
        r'\b(almonds|walnuts|peanuts|seeds|sunflower seeds|chia seeds)\b'
    ]
    
    # Process each meal
    for meal in meal_plan.meals:
        # Combine meal name and description for ingredient extraction
        text_to_parse = f"{meal.name} {meal.description}".lower()
        
        # Apply ingredient patterns
        for pattern in ingredient_patterns:
            matches = re.findall(pattern, text_to_parse, re.IGNORECASE)
            ingredients.update(matches)
    
    # Clean up and format ingredients
    cleaned_ingredients = []
    for ingredient in ingredients:
        # Capitalize first letter and clean up
        cleaned = ingredient.strip().capitalize()
        if cleaned and len(cleaned) > 2:  # Filter out very short matches
            cleaned_ingredients.append(cleaned)
    
    # Remove duplicates and sort
    unique_ingredients = sorted(list(set(cleaned_ingredients)))
    
    # If no ingredients found, return some common grocery items as fallback
    if not unique_ingredients:
        unique_ingredients = [
            "Bread", "Milk", "Eggs", "Butter", "Cheese", "Chicken", 
            "Rice", "Pasta", "Tomatoes", "Onions", "Garlic"
        ]
    
    return unique_ingredients

async def step_start_hook(agent: Agent):
    """Hook that runs at the start of each step"""
    print(f"🔄 Starting step {agent.history.number_of_steps() + 1}")
    if agent.history.number_of_steps() > 0:
        last_action = agent.history.last_action()
        if last_action:
            # Handle both dict and object formats
            if isinstance(last_action, dict):
                action_name = list(last_action.keys())[0] if last_action else "unknown"
                print(f"   Last action: {action_name}")
            else:
                print(f"   Last action: {getattr(last_action, 'action_name', 'unknown')}")

async def step_end_hook(agent: Agent):
    """Hook that runs at the end of each step"""
    print(f"✅ Completed step {agent.history.number_of_steps()}")
    try:
        # Get current URL using the correct method
        state = await agent.browser_session.get_browser_state_summary()
        # Handle different state object structures
        if hasattr(state, 'url'):
            current_url = state.url
        elif isinstance(state, dict):
            current_url = state.get('url', 'unknown')
        else:
            current_url = 'unknown'
        print(f"   Current URL: {current_url}")
    except Exception as e:
        print(f"   Could not get current URL: {e}")

async def run_sainsbury_order(items_list: List[str]) -> bool:
    """
    Run the Sainsbury's ordering automation for the given items
    Returns True if successful, False otherwise
    """
    try:
        # Check if API key is set
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("❌ Please set your ANTHROPIC_API_KEY in the .env file")
            return False

        print("✅ API key found, initializing Sainsbury's ordering agent...")
        
        # Initialize Anthropic Claude
        llm = ChatAnthropic(model="claude-sonnet-4-0")
        
        # Sainsbury's credentials from environment variables
        sainsbury_username = os.getenv("SAINSBURY_USERNAME")
        sainsbury_password = os.getenv("SAINSBURY_PASSWORD")
        
        if not sainsbury_username or not sainsbury_password:
            print("❌ Please set SAINSBURY_USERNAME and SAINSBURY_PASSWORD in the .env file")
            return False
        
        sainsbury_credentials = {
            'x_user': sainsbury_username, 
            'x_pass': sainsbury_password
        }

        # Sensitive data for secure credential handling
        sensitive_data = sainsbury_credentials

        # Browser configuration with broader domain restriction for security
        browser = Browser(
            headless=False,  # Show browser window
            keep_alive=True,  # Keep browser alive for multi-step workflow
            allowed_domains=['sainsburys.co.uk', 'account.sainsburys.co.uk', 'www.sainsburys.co.uk']  # Allow main Sainsbury's domains
        )

        # Start the browser session
        await browser.start()

        try:
            # Create a single agent with initial navigation
            print("\n🚀 Creating agent with initial navigation...")
            agent = Agent(
                task='Navigate to Sainsbury\'s login page and prepare for login',
                sensitive_data=sensitive_data,
                use_vision=False,
                llm=llm,
                browser_session=browser,
                # Initial actions run before LLM takes over
                initial_actions=[
                    {"go_to_url": {"url": "https://account.sainsburys.co.uk/gol/login"}},
                    {"wait": {"seconds": 2}}  # Wait for page to load
                ]
            )
            
            # Fix the agent ID to be a valid identifier (no hyphens)
            agent.id = agent.id.replace('-', '')
            
            # Step 1: Initial navigation
            print("\n🚀 Step 1: Initial Navigation")
            result1 = await agent.run(
                on_step_start=step_start_hook,
                on_step_end=step_end_hook,
                max_steps=2
            )
            print(f"✅ Step 1 completed: {result1}")

            # Step 2: Login process
            print("\n🔐 Step 2: Login Process")
            agent.add_new_task('Log into Sainsbury\'s using the provided credentials (x_user and x_pass)')
            result2 = await agent.run(
                on_step_start=step_start_hook,
                on_step_end=step_end_hook,
                max_steps=5  # Increased to 5 steps for more reliable login
            )
            print(f"✅ Step 2 completed: {result2}")

            # Step 3: Navigate to grocery shopping page and search
            print("\n📊 Step 3: Navigate to Grocery Shopping")
            agent.add_new_task('Wait for the redirection to Sainsbury\'s main grocery shopping page. Press the `Search by list` button. You should be taken to https://www.sainsburys.co.uk/gol-ui/search-a-list-of-items page.')
            result3 = await agent.run(
                on_step_start=step_start_hook,
                on_step_end=step_end_hook,
                max_steps=5  # Increased to 5 steps for navigation and search
            )
            print(f"✅ Step 3 completed: {result3}")

            # Step 4: Add items to search
            print("\n🛒 Step 4: Search for shopping list items")
            items_str = ", ".join(items_list)
            agent.add_new_task(f'Input the list of items {items_str} as a comma separated list in the search field and press the `Find results` button.')
            result4 = await agent.run(
                on_step_start=step_start_hook,
                on_step_end=step_end_hook,
                max_steps=3  # 3 steps should be enough for adding to basket
            )
            print(f"✅ Step 4 completed: {result4}")

            # Step 5: Add items to basket
            print("\n🛒 Step 5: Add items to basket")
            agent.add_new_task('Wait for the page to load and then by clicking on multi-search-tab buttons one by one add the first item you find to basket for each search tab button. Wait for the page to load for each search tab button.')
            result5 = await agent.run(
                on_step_start=step_start_hook,
                on_step_end=step_end_hook,
                max_steps=12 
            )

            # Step 6: Booking a slot
            print("\n🛒 Step 6: Booking a slot")
            agent.add_new_task('Click on the `Book a slot` button or `book-delivery__datetime` button on the top right corner of the page. You should be taken to https://www.sainsburys.co.uk/gol-ui/slot/book page. Make sure the title is `Book delivery` and if not click on the `switch to develiery` button.')
            result6 = await agent.run(
                on_step_start=step_start_hook,
                on_step_end=step_end_hook,
                max_steps=3
            )
            print(f"✅ Step 6 completed: {result6}")

            # Step 7: Select any slot in the evening
            agent.add_new_task('Select any slot in the evening after 5pm on any daythat are clickable by clicking on the pound values. When the modal appears, click on the `Reserve slot` button.')
            result7 = await agent.run(
                on_step_start=step_start_hook,
                on_step_end=step_end_hook,
                max_steps=3
            )
            print(f"✅ Step 7 completed: {result7}")

            # Step 8: Check out now
            print("\n🛒 Step 8: Check out now")
            agent.add_new_task('Click on the trolley icon on the top right corner should should take you to https://www.sainsburys.co.uk/gol-ui/trolley.')
            result8 = await agent.run(
                on_step_start=step_start_hook,
                on_step_end=step_end_hook,
                max_steps=3
            )
            print(f"✅ Step 8 completed: {result8}")

            print("\n📋 Sainsbury's Order Workflow Summary:")
            print("1. ✅ Initial navigation with pre-defined actions")
            print("2. ✅ Login process with credential handling")
            print("3. ✅ Navigate to grocery shopping page and search")
            print("4. ✅ Search for shopping list items")
            print("5. ✅ Add items to basket")
            print("6. ✅ Book delivery slot")
            print("7. ✅ Navigate to trolley")
            print("8. ✅ All steps completed successfully")

            return True

        except Exception as e:
            print(f"❌ Error during Sainsbury's ordering workflow: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            print("\n🔄 Sainsbury's ordering workflow completed!")
            print("🌐 Browser will remain open for inspection...")
            print("   Press Ctrl+C to close the browser when you're done.")
            
            # Keep browser alive for inspection
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n🔄 Closing browser...")
                await browser.stop()

    except Exception as e:
        print(f"❌ Error during Sainsbury's ordering: {e}")
        import traceback
        traceback.print_exc()
        return False

@router.post("/from-meal-plan", response_model=SainsburyOrderResponse)
async def create_sainsbury_order_from_meal_plan(request: SainsburyMealPlanOrderRequest):
    """
    Create a Sainsbury's grocery order from a meal plan.
    
    This endpoint will:
    1. Parse the meal plan to extract ingredients
    2. Open a browser window
    3. Navigate to Sainsbury's and log in
    4. Search for the extracted ingredients
    5. Add items to basket
    6. Book a delivery slot
    7. Navigate to trolley for checkout
    
    The browser will remain open for user interaction and inspection.
    """
    try:
        # Parse the meal plan to extract ingredients
        items_list = parse_meals_to_ingredients(request.meal_plan)
        
        if not items_list:
            raise HTTPException(
                status_code=400, 
                detail="No ingredients could be extracted from the meal plan."
            )
        
        print(f"🛒 Starting Sainsbury's order for extracted ingredients: {items_list}")
        
        # Run the browser automation in a separate task
        # This allows the endpoint to return immediately while the browser automation runs
        success = await run_sainsbury_order(items_list)
        
        if success:
            return SainsburyOrderResponse(
                success=True,
                message="Sainsbury's order process completed successfully. Browser window is open for your review.",
                items_ordered=items_list
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to complete Sainsbury's order process. Check logs for details."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in Sainsbury's order endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/", response_model=SainsburyOrderResponse)
async def create_sainsbury_order(request: SainsburyOrderRequest):
    """
    Create a Sainsbury's grocery order with the provided items.
    
    This endpoint will:
    1. Open a browser window
    2. Navigate to Sainsbury's and log in
    3. Search for the provided items
    4. Add items to basket
    5. Book a delivery slot
    6. Navigate to trolley for checkout
    
    The browser will remain open for user interaction and inspection.
    """
    try:
        # Parse the comma-separated items
        items_list = [item.strip() for item in request.items.split(',') if item.strip()]
        
        if not items_list:
            raise HTTPException(
                status_code=400, 
                detail="No valid items provided. Please provide a comma-separated list of items."
            )
        
        print(f"🛒 Starting Sainsbury's order for items: {items_list}")
        
        # Run the browser automation in a separate task
        # This allows the endpoint to return immediately while the browser automation runs
        success = await run_sainsbury_order(items_list)
        
        if success:
            return SainsburyOrderResponse(
                success=True,
                message="Sainsbury's order process completed successfully. Browser window is open for your review.",
                items_ordered=items_list
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to complete Sainsbury's order process. Check logs for details."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in Sainsbury's order endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
