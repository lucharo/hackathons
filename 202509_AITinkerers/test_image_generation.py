#!/usr/bin/env python3
"""Test script for image generation service."""

import asyncio
from image_service import generate_recipe_image, generate_recipe_image_sync


async def test_async():
    """Test async image generation."""
    recipes = [
        "Overnight Oats with Berries",
        "Tofu Scramble",
        "Chickpea Curry",
        "Lentil Tacos",
        "Veggie Stir Fry"
    ]

    print("Testing async image generation...")
    for recipe in recipes:
        try:
            image_url = await generate_recipe_image(recipe)
            print(f"✓ {recipe}: {image_url}")
        except Exception as e:
            print(f"✗ {recipe}: Error - {e}")


def test_sync():
    """Test sync image generation."""
    recipes = [
        "Pancakes",
        "Buddha Bowl",
        "Pasta Primavera"
    ]

    print("\nTesting sync image generation...")
    for recipe in recipes:
        try:
            image_url = generate_recipe_image_sync(recipe)
            print(f"✓ {recipe}: {image_url}")
        except Exception as e:
            print(f"✗ {recipe}: Error - {e}")


if __name__ == "__main__":
    # Test async version
    asyncio.run(test_async())

    # Test sync version
    test_sync()

    print("\n✅ Image generation tests complete!")