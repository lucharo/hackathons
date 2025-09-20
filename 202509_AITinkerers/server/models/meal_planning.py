from enum import Enum
from pydantic import BaseModel


class MealType(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    GLUTEN_FREE = "gluten_free"
    HALAL = "halal"


class Nutrition(BaseModel):
    calories: int
    grams_protein: float
    grams_carbs: float
    grams_fat: float


class Meal(BaseModel):
    description: str
    num_servings: int
    nutrition: Nutrition
    meal_type: MealType
    allergens: list[str]


class MealPlan(BaseModel):
    meals: list[Meal]
