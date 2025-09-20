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
from routers.mcp import generate_ingredient_list_from_meals

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

async def login_to_sainsbury(browser):
    """Login to Sainsbury's and prepare for shopping"""
    
    if browser is None:
        raise ValueError("Browser instance is required. Please pass a browser object.")
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print('❌ Error: ANTHROPIC_API_KEY environment variable is required')
        print("Please set it in your .env file or environment")
        return False

    # Get Sainsbury's credentials
    sainsbury_username = os.getenv("SAINSBURY_USERNAME")
    sainsbury_password = os.getenv("SAINSBURY_PASSWORD")
    
    if not sainsbury_username or not sainsbury_password:
        print('❌ Error: SAINSBURY_USERNAME and SAINSBURY_PASSWORD environment variables are required')
        print("Please set them in your .env file:")
        print("SAINSBURY_USERNAME=your_email@example.com")
        print("SAINSBURY_PASSWORD=your_password")
        return False

    print('🔐 Starting Sainsbury\'s Login Agent')
    print(f'Username: {sainsbury_username}')
    print('=' * 50)

    try:
        # Initialize Claude
        llm = ChatAnthropic(model="claude-sonnet-4-0")

        # Prepare credentials for secure handling
        sainsbury_credentials = {
            'x_user': sainsbury_username,
            'x_pass': sainsbury_password
        }

        # Comprehensive task with detailed instructions
        task = f"""
        You are helping a user log into Sainsbury's grocery website and prepare for shopping. Follow these steps carefully:

        1. Navigate to https://www.sainsburys.co.uk/gol-ui/groceries
        2. Wait for the page to load completely (2-3 seconds)
        3. Look for the `Log in / Register` button and click on it.
        4. You should be taken to https://account.sainsburys.co.uk/gol/login page.
        5. Fill in the email field with the credential x_user
        6. Fill in the password field with the credential x_pass
        7. Click the login/sign in button
        8. Wait for the login process to complete and for any redirects

        Finish when logged in successfully.
        """

        print('🚀 Running login process...\n')

        # Create agent with sensitive data handling
        agent = Agent(
            task=task, 
            llm=llm, 
            browser_session=browser,
            sensitive_data=sainsbury_credentials,
            use_vision=False  # Disable vision to prevent LLM seeing sensitive data in screenshots
        )

        # Run the agent
        result = await agent.run(max_steps=15)  # Generous step count for complex login flow

        print('\n' + '='*50)
        print('✅ Sainsbury\'s login completed!')
        print('='*50)
        
        return True

    except Exception as e:
        print(f'\n❌ Error during Sainsbury\'s login: {str(e)}')
        print('Please check your credentials and try again.')
        import traceback
        traceback.print_exc()
        return False


async def search_list_add_to_cart(browser, items_list):
    """Search for items and add them to cart on Sainsbury's"""
    
    if browser is None:
        raise ValueError("Browser instance is required. Please pass a browser object.")
    
    if not items_list or len(items_list) == 0:
        raise ValueError("Items list is required and cannot be empty.")
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print('❌ Error: ANTHROPIC_API_KEY environment variable is required')
        print("Please set it in your .env file or environment")
        return False

    print('🛒 Starting Sainsbury\'s Search and Add to Cart Agent')
    print(f'Items to search: {", ".join(items_list)}')
    print('=' * 50)

    try:
        # Initialize Claude
        llm = ChatAnthropic(model="claude-sonnet-4-0")

        # Items string for the task
        items_str = ", ".join(items_list)

        # Comprehensive task with detailed instructions
        task = f"""
        You are helping a user search for grocery items and add them to their cart on Sainsbury's website. 
        The user is already logged in. Follow these steps carefully:

        1. Make sure you are on https://www.sainsburys.co.uk/gol-ui/groceries page
        2. Look for and click the "Search by list" button on the top right corner of the page
        3. Input the list of items "{items_str}" as a comma separated list in the search field
        4. Click the "Find results" button
        5. Wait for the search results to load and look for multi-search-tab buttons that correspond to the items in the list
        6. For each of the multi search tab buttons:
            - click on the tab first
            - add the first item you find to the trolley by pressing the `Add` button
            - once the add_it changed to `1` item added, move to the next tab

        Finish when all items have been added to the trolley.
        """

        print('🚀 Running search and add to cart process...\n')

        # Create agent
        agent = Agent(
            task=task, 
            llm=llm, 
            browser_session=browser,
            use_vision=False
        )

        # Run the agent with generous step count for complex shopping flow
        result = await agent.run(max_steps=60)

        print('\n' + '='*50)
        print('✅ Sainsbury\'s search and add to cart completed!')
        print('='*50)
        
        return True

    except Exception as e:
        print(f'\n❌ Error during Sainsbury\'s search and add to cart: {str(e)}')
        print('Please check the items list and try again.')
        import traceback
        traceback.print_exc()
        return False


async def book_delivery_slot(browser):
    """Book a delivery slot on Sainsbury's website"""
    
    if browser is None:
        raise ValueError("Browser instance is required. Please pass a browser object.")
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print('❌ Error: ANTHROPIC_API_KEY environment variable is required')
        print("Please set it in your .env file or environment")
        return False

    print('📅 Starting Sainsbury\'s Delivery Slot Booking Agent')
    print('=' * 50)

    try:
        # Initialize Claude
        llm = ChatAnthropic(model="claude-sonnet-4-0")

        # Comprehensive task with detailed instructions
        task = """
        You are helping a user book a delivery slot on Sainsbury's website. 
        The user is already logged in and has items in their cart. Follow these steps carefully:

        1. Look for the "Book a slot" button or "book-delivery__datetime" button on the top right corner of the page
        2. Click on it to navigate to the slot booking page
        3. You should be taken to https://www.sainsburys.co.uk/gol-ui/slot/book page
        4. Wait for the page to load completely
        5. Check if the page title shows "Book delivery"
        6. If not, look for a "switch to delivery" button and click on it
        7. Make sure you are in delivery mode, not collection mode
        8. Look for available delivery slots, particularly in the evening after 5pm
        9. Find slots that are clickable (usually shown with pound values indicating the delivery cost)
        10. Click on any available evening slot after 5pm on any day
        11. Wait for a modal or confirmation dialog to appear
        12. When the modal appears, look for a "Reserve slot" button
        13. Click the "Reserve slot" button to confirm the booking
        14. Wait for the confirmation to process

        Finish when the delivery slot has been successfully reserved.
        """

        print('🚀 Running delivery slot booking process...\n')

        # Create agent
        agent = Agent(
            task=task, 
            llm=llm, 
            browser_session=browser,
            use_vision=False
        )

        # Run the agent with appropriate step count for slot booking
        result = await agent.run(max_steps=12)

        # add another task to navigate to trolley
        agent.add_new_task('Look for the trolley icon on the top right corner of the page and click on it to navigate to the trolley page.')
        result = await agent.run(max_steps=3)

        print('\n' + '='*50)
        print('✅ Sainsbury\'s delivery slot booking completed!')
        print('='*50)
        
        return True

    except Exception as e:
        print(f'\n❌ Error during Sainsbury\'s delivery slot booking: {str(e)}')
        print('Please check that you have items in your cart and try again.')
        import traceback
        traceback.print_exc()
        return False


async def parse_meals_to_ingredient_list(meal_plan: MealPlan) -> List[str]:
    ingredient_list = await generate_ingredient_list_from_meals(meal_plan.meals)
    ingredients = [ingredient.name for ingredient in ingredient_list]
    return ingredients


async def run_sainsbury_order(items_list: List[str]) -> bool:
    """
    Run the Sainsbury's ordering automation for the given items using the modular functions
    Returns True if successful, False otherwise
    """
    try:
        # Check if API key is set
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("❌ Please set your ANTHROPIC_API_KEY in the .env file")
            return False

        print("✅ API key found, initializing Sainsbury's ordering agent...")
        
        # Browser configuration with broader domain restriction for security
        browser = Browser(
            headless=False,  # Show browser window
            keep_alive=True,  # Keep browser alive for multi-step workflow
            allowed_domains=['sainsburys.co.uk', 'account.sainsburys.co.uk', 'www.sainsburys.co.uk']  # Allow main Sainsbury's domains
        )

        # Start the browser session
        await browser.start()

        try:
            # Step 1: Login to Sainsbury's
            print("🔐 Step 1: Logging into Sainsbury's...")
            login_success = await login_to_sainsbury(browser)
            
            if login_success:
                print("\n" + "="*50)
                print("Login successful! Now searching for items and adding to cart...")
                print("="*50)
                
                # Step 2: Search for items and add to cart
                print("🛒 Step 2: Searching for items and adding to cart...")
                cart_success = await search_list_add_to_cart(browser, items_list)
                
                if cart_success:
                    print("\n" + "="*50)
                    print("Items added to cart! Now booking delivery slot...")
                    print("="*50)
                    
                    # Step 3: Book delivery slot
                    print("📅 Step 3: Booking delivery slot...")
                    slot_success = await book_delivery_slot(browser)
                    
                    if slot_success:
                        print("\n📋 Sainsbury's Order Workflow Summary:")
                        print("1. ✅ Login to Sainsbury's")
                        print("2. ✅ Search for items and add to cart")
                        print("3. ✅ Book delivery slot and navigate to trolley")
                        print("4. ✅ All steps completed successfully")
                        return True
                    else:
                        print("\n❌ Failed to book delivery slot")
                        return False
                else:
                    print("\n❌ Failed to add items to cart")
                    return False
            else:
                print("\n❌ Login failed, skipping all other operations")
                return False

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
        items_list = await parse_meals_to_ingredient_list(request.meal_plan)
        
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
