"""Shared domain models, helpers, and LLM agents for Prototype 1."""

from __future__ import annotations

import json
import logging
import math
import os
import shlex
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent

load_dotenv()

logger = logging.getLogger(__name__)

try:
    from mcp.client import stdio as mcp_stdio
    from mcp.client.stdio import StdioServerParameters
    from mcp.client.session import ClientSession as MCPClientSession

    _MCP_AVAILABLE = True
except Exception:  # noqa: BLE001 - optional dependency
    mcp_stdio = None  # type: ignore[assignment]
    MCPClientSession = None  # type: ignore[assignment]
    StdioServerParameters = None  # type: ignore[assignment]
    _MCP_AVAILABLE = False

DEFAULT_MODEL = "anthropic:claude-sonnet-4-20250514"
BASE_MODEL = os.environ.get("BASE_MODEL", DEFAULT_MODEL)

Activity = Literal["sedentary", "light", "moderate", "very", "extreme"]
Direction = Literal["loss", "gain"]
RateCat = Literal["low", "mid", "fast"]


class Profile(BaseModel):
    sex: Optional[Literal["male", "female"]] = None
    age: Optional[int] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity: Optional[Activity] = None


class Goal(BaseModel):
    direction: Optional[Direction] = None
    rate_category: Optional[RateCat] = None
    weeks: Optional[int] = None
    target_delta_kg: Optional[float] = None


class FoodPrefs(BaseModel):
    dislikes: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    cuisines: List[str] = Field(default_factory=list)
    breakfasts_like: List[str] = Field(default_factory=list)
    mains_like: List[str] = Field(default_factory=list)


class Ingredient(BaseModel):
    name: str
    qty: float
    unit: str


class Recipe(BaseModel):
    title: str
    servings: int
    calories_per_serving: int
    ingredients: List[Ingredient]
    steps: List[str]


class WeekPlan(BaseModel):
    breakfasts: List[Recipe]
    mains: List[Recipe]
    target_calories: int
    tdee: int


class CoachState(BaseModel):
    profile: Profile = Field(default_factory=Profile)
    goal: Goal = Field(default_factory=Goal)
    prefs: FoodPrefs = Field(default_factory=FoodPrefs)
    tdee: Optional[int] = None
    target_calories: Optional[int] = None
    plan: Optional[WeekPlan] = None
    cart_url: Optional[str] = None


ACTIVITY_FACTOR: Dict[Activity, float] = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "very": 1.725,
    "extreme": 1.9,
}

LOSS_RATES = {"low": 0.25, "mid": 0.5, "fast": 0.75}
GAIN_RATES = {"low": 0.125, "mid": 0.25, "fast": 0.5}
KCAL_PER_KG = 7700.0


def mifflin_st_jeor(sex: str, weight_kg: float, height_cm: float, age: int) -> float:
    """Return resting metabolic rate (kcal/day) via Mifflin–St Jeor."""

    adjustment = 5 if sex == "male" else -161
    return 10 * weight_kg + 6.25 * height_cm - 5 * age + adjustment


def tdee_from_profile(profile: Profile) -> int:
    """Compute total daily energy expenditure from profile data."""

    if not profile.sex or profile.age is None:
        raise ValueError("Profile missing sex or age for TDEE calculation")
    if profile.height_cm is None or profile.weight_kg is None:
        raise ValueError("Profile missing height or weight for TDEE calculation")

    bmr = mifflin_st_jeor(profile.sex, profile.weight_kg, profile.height_cm, profile.age)
    activity = profile.activity or "moderate"
    return int(round(bmr * ACTIVITY_FACTOR[activity]))


def daily_calorie_delta(direction: Direction, rate: RateCat) -> float:
    """Return daily kcal surplus/deficit for the chosen rate category."""

    rates = LOSS_RATES if direction == "loss" else GAIN_RATES
    kg_per_week = rates[rate]
    return (kg_per_week * KCAL_PER_KG) / 7.0


def compute_targets(state: CoachState) -> CoachState:
    """Populate maintenance and goal calorie targets on the provided state."""

    if not state.profile.sex:
        raise ValueError("Profile sex required before computing targets")
    if state.goal.direction is None or state.goal.rate_category is None:
        raise ValueError("Goal direction and rate required before computing targets")

    tdee = tdee_from_profile(state.profile)
    delta = daily_calorie_delta(state.goal.direction, state.goal.rate_category)
    target = tdee - delta if state.goal.direction == "loss" else tdee + delta
    state.tdee = tdee
    state.target_calories = int(round(target))
    return state


class CollectOut(BaseModel):
    say: str
    profile: Profile = Field(default_factory=Profile)
    goal: Goal = Field(default_factory=Goal)
    prefs: FoodPrefs = Field(default_factory=FoodPrefs)


collect_agent = Agent(
    BASE_MODEL,
    system_prompt=(
        "You are a concise nutrition intake assistant.\n"
        "Update only the profile, goal, and food preference fields you can infer from the latest reply.\n"
        "Ask exactly one short follow-up question when mandatory data is missing.\n"
        "Mandatory before advancing: sex (male/female), age, height_cm, weight_kg, activity level, direction (loss/gain), rate_category (low/mid/fast).\n"
        "When prompted for preferences, elicit two breakfasts and three lunch/dinner ideas, plus allergies or dislikes."
    ),
    output_type=CollectOut,
)


class RecipesOut(BaseModel):
    say: str
    breakfasts: List[Recipe]
    mains: List[Recipe]


recipes_agent = Agent(
    BASE_MODEL,
    system_prompt=(
        "Generate exactly two breakfast recipes and three lunch/dinner recipes.\n"
        "Each Recipe must include servings, calories_per_serving, ingredients with numeric qty + unit, and clear steps.\n"
        "Keep combined daily calories aligned with the provided target and respect dislikes/allergies/cuisine hints."
    ),
    output_type=RecipesOut,
)


def aggregate_ingredients(recipes: List[Recipe]) -> List[Ingredient]:
    """Combine ingredient quantities across all recipes."""

    accumulator: Dict[tuple[str, str], float] = defaultdict(float)
    for recipe in recipes:
        for item in recipe.ingredients:
            key = (item.name.lower(), item.unit)
            accumulator[key] += item.qty
    return [
        Ingredient(name=name, qty=round(qty, 2), unit=unit)
        for (name, unit), qty in accumulator.items()
    ]


def _extract_json_payload(result: Any) -> Dict[str, Any] | List[Any] | None:
    """Extract JSON content from an MCP tool response."""

    if getattr(result, "structuredContent", None):
        return result.structuredContent

    for entry in getattr(result, "content", []) or []:
        text = getattr(entry, "text", "")
        if not text:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            continue
    return None


def _infer_cart_quantity(ingredient: Ingredient) -> int:
    unit = (ingredient.unit or "").lower()
    qty = ingredient.qty or 1
    if unit in {"count", "counts", "pc", "pcs", "piece", "pieces", "item", "items"}:
        return max(1, int(math.ceil(qty)))
    if unit in {"pack", "packs", "package", "packages", "bag", "bags", "bottle", "bottles", "jar", "jars"}:
        return max(1, int(math.ceil(qty)))
    if qty >= 1:
        return int(math.ceil(qty))
    return 1


def _should_clear_cart() -> bool:
    return os.getenv("PICNIC_CLEAR_CART", "false").lower() in {"1", "true", "yes", "on"}


def _picnic_env(username: str, password: str) -> Dict[str, str]:
    env = {
        "PICNIC_USERNAME": username,
        "PICNIC_PASSWORD": password,
    }
    for name in ("PICNIC_COUNTRY_CODE", "PICNIC_API_VERSION", "HTTP_PROXY", "HTTPS_PROXY"):
        value = os.getenv(name)
        if value:
            env[name] = value
    return env


def _format_search_query(ingredient: Ingredient) -> str:
    base = ingredient.name.strip()
    unit = ingredient.unit.strip() if ingredient.unit else ""
    if unit:
        return f"{base} {unit}"
    return base


def _pick_product(results: List[Dict[str, Any]], ingredient: Ingredient) -> Dict[str, Any] | None:
    target = ingredient.name.lower()
    for candidate in results:
        name = str(candidate.get("name", "")).lower()
        if name == target:
            return candidate
    return results[0] if results else None


def _derive_cart_url(cart_payload: Dict[str, Any] | None) -> str:
    base_url = os.getenv("PICNIC_CART_URL", "https://app.picnic.app/cart")
    if not isinstance(cart_payload, dict):
        return base_url
    cart_id = cart_payload.get("id") or cart_payload.get("cart_id")
    if cart_id:
        return f"{base_url}?cartId={cart_id}"
    return base_url


ProgressReporter = Callable[[Dict[str, Any]], Awaitable[None]]


async def _emit(progress_cb: ProgressReporter | None, event: Dict[str, Any]) -> None:
    if progress_cb is None:
        return
    await progress_cb(event)


async def _checkout_via_mcp(
    ingredients: List[Ingredient],
    username: str,
    password: str,
    progress_cb: ProgressReporter | None = None,
) -> str:
    if not _MCP_AVAILABLE or not mcp_stdio or not MCPClientSession or not StdioServerParameters:
        raise RuntimeError("MCP Picnic client is unavailable")

    args_env = os.getenv("PICNIC_MCP_ARGS", "-y mcp-picnic")
    arg_list = shlex.split(args_env) if args_env else []
    if not arg_list:
        arg_list = ["-y", "mcp-picnic"]

    params = StdioServerParameters(
        command=os.getenv("PICNIC_MCP_COMMAND", "npx"),
        args=arg_list,
        env=_picnic_env(username, password),
    )

    successful: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    await _emit(progress_cb, {"type": "tool", "tool": "mcp_session", "phase": "start"})

    async with mcp_stdio.stdio_client(params) as (read_stream, write_stream):
        session = MCPClientSession(read_stream, write_stream)
        await session.initialize()
        await session.list_tools()

        await _emit(progress_cb, {"type": "tool", "tool": "mcp_session", "phase": "ready"})

        if _should_clear_cart():
            await session.call_tool("picnic_clear_cart", {})

        for ingredient in ingredients:
            query = _format_search_query(ingredient)
            await _emit(
                progress_cb,
                {
                    "type": "tool",
                    "tool": "picnic_search",
                    "phase": "start",
                    "ingredient": ingredient.name,
                    "query": query,
                },
            )
            try:
                search_result = await session.call_tool("picnic_search", {"query": query, "limit": 5})
            except Exception as exc:  # noqa: BLE001
                logger.warning("Picnic search failed for %s: %s", ingredient.name, exc)
                failures.append({"ingredient": ingredient.name, "reason": "search_failed"})
                await _emit(
                    progress_cb,
                    {
                        "type": "tool",
                        "tool": "picnic_search",
                        "phase": "error",
                        "ingredient": ingredient.name,
                        "query": query,
                        "reason": "search_failed",
                    },
                )
                continue

            payload = _extract_json_payload(search_result)
            products = payload.get("results") if isinstance(payload, dict) else None
            if not products:
                failures.append({"ingredient": ingredient.name, "reason": "no_results"})
                await _emit(
                    progress_cb,
                    {
                        "type": "tool",
                        "tool": "picnic_search",
                        "phase": "error",
                        "ingredient": ingredient.name,
                        "query": query,
                        "reason": "no_results",
                    },
                )
                continue

            product = _pick_product(products, ingredient)
            if not product or "id" not in product:
                failures.append({"ingredient": ingredient.name, "reason": "no_match"})
                await _emit(
                    progress_cb,
                    {
                        "type": "tool",
                        "tool": "picnic_search",
                        "phase": "error",
                        "ingredient": ingredient.name,
                        "query": query,
                        "reason": "no_match",
                    },
                )
                continue

            await _emit(
                progress_cb,
                {
                    "type": "tool",
                    "tool": "picnic_search",
                    "phase": "success",
                    "ingredient": ingredient.name,
                    "query": query,
                    "results": len(products),
                    "product": product.get("name"),
                },
            )

            count = _infer_cart_quantity(ingredient)
            try:
                await _emit(
                    progress_cb,
                    {
                        "type": "tool",
                        "tool": "picnic_add_to_cart",
                        "phase": "start",
                        "ingredient": ingredient.name,
                        "product": product.get("name"),
                        "count": count,
                    },
                )
                await session.call_tool("picnic_add_to_cart", {"productId": product["id"], "count": count})
                successful.append({"ingredient": ingredient.name, "product": product.get("name"), "count": count})
                await _emit(
                    progress_cb,
                    {
                        "type": "tool",
                        "tool": "picnic_add_to_cart",
                        "phase": "success",
                        "ingredient": ingredient.name,
                        "product": product.get("name"),
                        "count": count,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to add %s to Picnic cart: %s", ingredient.name, exc)
                failures.append({"ingredient": ingredient.name, "reason": "add_failed"})
                await _emit(
                    progress_cb,
                    {
                        "type": "tool",
                        "tool": "picnic_add_to_cart",
                        "phase": "error",
                        "ingredient": ingredient.name,
                        "product": product.get("name"),
                        "count": count,
                        "reason": "add_failed",
                    },
                )

        cart_result = await session.call_tool("picnic_get_cart", {})
        cart_payload = _extract_json_payload(cart_result)
        await _emit(
            progress_cb,
            {
                "type": "tool",
                "tool": "picnic_get_cart",
                "phase": "success",
            },
        )

    if failures:
        logger.info("Picnic cart issues: %s", failures)
    if successful:
        logger.info("Picnic cart additions: %s", successful)

    return _derive_cart_url(cart_payload if isinstance(cart_payload, dict) else None)


async def groceries_checkout(
    ingredients: List[Ingredient],
    progress_cb: ProgressReporter | None = None,
) -> str:
    username = os.getenv("PICNIC_USERNAME")
    password = os.getenv("PICNIC_PASSWORD")

    if not ingredients:
        await _emit(progress_cb, {"type": "status", "message": "Shopping list empty; skipping cart creation."})
        return os.getenv("PICNIC_CART_URL", "https://app.picnic.app/cart")
    if not username or not password:
        logger.debug("PICNIC credentials missing; returning demo cart URL")
        await _emit(progress_cb, {"type": "status", "message": "PICNIC credentials missing; returning demo cart URL."})
        return "https://example.com/demo-cart"

    try:
        return await _checkout_via_mcp(ingredients, username, password, progress_cb)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Picnic MCP checkout failed: %s", exc)
        await _emit(progress_cb, {"type": "status", "message": "Picnic MCP checkout failed; returning demo cart URL."})
        return "https://example.com/demo-cart"


__all__ = [
    "Activity",
    "CoachState",
    "CollectOut",
    "Direction",
    "FoodPrefs",
    "Goal",
    "Ingredient",
    "Profile",
    "RateCat",
    "Recipe",
    "RecipesOut",
    "WeekPlan",
    "aggregate_ingredients",
    "collect_agent",
    "compute_targets",
    "daily_calorie_delta",
    "groceries_checkout",
    "mifflin_st_jeor",
    "recipes_agent",
    "tdee_from_profile",
]
