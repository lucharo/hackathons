from enum import Enum
from pydantic import BaseModel


class DietaryType(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    GLUTEN_FREE = "gluten_free"
    HALAL = "halal"
    NONE = "none"


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH_DINNER = "lunch/dinner"


class Nutrition(BaseModel):
    calories: int
    grams_protein: float
    grams_carbs: float
    grams_fat: float


class Meal(BaseModel):
    name: str
    description: str
    num_servings: int
    nutrition: Nutrition
    meal_type: MealType
    diet_type: DietaryType
    allergens: list[str]


class MealPlan(BaseModel):
    meals: list[Meal]
