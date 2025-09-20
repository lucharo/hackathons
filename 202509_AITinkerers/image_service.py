"""Image generation service for recipe images."""

from __future__ import annotations

import hashlib
import httpx
import logging
import os
import random
from typing import Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
FOODISH_API_BASE = "https://foodish-api.com/api"
UNSPLASH_API_BASE = "https://api.unsplash.com"


def get_fallback_food_image() -> str:
    """Get a random food image from Foodish API as fallback."""
    food_types = [
        "biryani", "burger", "butter-chicken", "dessert", "dosa",
        "idly", "pasta", "pizza", "rice", "samosa"
    ]
    food_type = random.choice(food_types)
    return f"{FOODISH_API_BASE}/images/{food_type}/{food_type}{random.randint(1, 10)}.jpg"


async def generate_recipe_image(
    recipe_title: str,
    ingredients: list[str] | None = None,
    use_cache: bool = True
) -> str:
    """
    Generate or fetch an image for a recipe.

    First tries Unsplash API if key is available,
    then falls back to Foodish API for random food images.
    """
    try:
        # Try Unsplash first if we have an API key
        if UNSPLASH_ACCESS_KEY:
            async with httpx.AsyncClient() as client:
                # Search for food images related to the recipe title
                search_query = recipe_title.lower()
                # Extract key food items from title for better search
                food_keywords = ["breakfast", "lunch", "dinner", "salad", "soup",
                                "sandwich", "pasta", "rice", "chicken", "beef",
                                "fish", "vegetarian", "vegan", "dessert", "cake"]

                # Find any matching keywords in the title
                matching_keywords = [kw for kw in food_keywords if kw in search_query]
                if matching_keywords:
                    search_query = " ".join(matching_keywords[:2])  # Use top 2 keywords

                response = await client.get(
                    f"{UNSPLASH_API_BASE}/search/photos",
                    params={
                        "query": f"food {search_query}",
                        "per_page": 1,
                        "orientation": "landscape"
                    },
                    headers={
                        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
                    },
                    timeout=5.0
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        image_url = data["results"][0]["urls"]["regular"]
                        logger.info(f"Found Unsplash image for recipe: {recipe_title}")
                        return image_url

        # Fallback to Foodish API for random food images
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FOODISH_API_BASE}/", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if "image" in data:
                    logger.info(f"Using Foodish fallback image for recipe: {recipe_title}")
                    return data["image"]

        # Ultimate fallback - return a placeholder
        logger.warning(f"Could not generate image for recipe: {recipe_title}")
        return get_fallback_food_image()

    except Exception as e:
        logger.error(f"Error generating image for recipe {recipe_title}: {e}")
        return get_fallback_food_image()


def generate_recipe_image_sync(
    recipe_title: str,
    ingredients: list[str] | None = None
) -> str:
    """
    Synchronous version of generate_recipe_image.
    """
    try:
        # Try Unsplash first if we have an API key
        if UNSPLASH_ACCESS_KEY:
            with httpx.Client() as client:
                search_query = recipe_title.lower()
                food_keywords = ["breakfast", "lunch", "dinner", "salad", "soup",
                                "sandwich", "pasta", "rice", "chicken", "beef",
                                "fish", "vegetarian", "vegan", "dessert", "cake"]

                matching_keywords = [kw for kw in food_keywords if kw in search_query]
                if matching_keywords:
                    search_query = " ".join(matching_keywords[:2])

                response = client.get(
                    f"{UNSPLASH_API_BASE}/search/photos",
                    params={
                        "query": f"food {search_query}",
                        "per_page": 1,
                        "orientation": "landscape"
                    },
                    headers={
                        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
                    },
                    timeout=5.0
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        return data["results"][0]["urls"]["regular"]

        # Fallback to Foodish API
        with httpx.Client() as client:
            response = client.get(f"{FOODISH_API_BASE}/", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if "image" in data:
                    return data["image"]

        return get_fallback_food_image()

    except Exception as e:
        logger.error(f"Error generating image for recipe {recipe_title}: {e}")
        return get_fallback_food_image()