"""Chainlit-powered chat UI for the DishGenius nutrition coach."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List

import chainlit as cl
from chainlit import Text
import httpx

DEFAULT_API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
DEFAULT_TIMEOUT = float(os.getenv("API_TIMEOUT", "300"))

WELCOME_MESSAGE = (
    "Hi! I'm **DishGenius**, your nutrition and grocery buddy 🥗.\n\n"
    "Let's get you set up:\n"
    "1. Tell me about yourself – age, height, weight, activity level, and your goal (loss/gain/maintain).\n"
    "2. Share at least two breakfasts and three mains you enjoy, plus allergies or dislikes.\n"
    "3. Ask me to generate your weekly plan and grocery cart when you're ready!"
)

STAGE3_TRIGGER_WORDS = {
    "plan",
    "generate",
    "meal",
    "recipes",
    "shopping list",
    "grocery",
}
STAGE2_HINT_WORDS = {
    "breakfast",
    "dinner",
    "lunch",
    "cuisine",
    "allergy",
    "allergies",
    "dislike",
    "prefer",
    "food",
}


def _profile_complete(state: Dict[str, Any]) -> bool:
    profile = state.get("profile") or {}
    return all(
        [
            profile.get("sex"),
            profile.get("age"),
            profile.get("height_cm"),
            profile.get("weight_kg"),
            profile.get("activity"),
        ]
    )


def _goal_complete(state: Dict[str, Any]) -> bool:
    goal = state.get("goal") or {}
    return bool(goal.get("direction") and goal.get("rate_category"))


def _prefs_complete(state: Dict[str, Any]) -> bool:
    prefs = state.get("prefs") or {}
    breakfasts = prefs.get("breakfasts_like") or []
    mains = prefs.get("mains_like") or []
    return len(breakfasts) >= 2 and len(mains) >= 3


def _infer_stage(message: str, current_stage: int) -> int:
    lower = message.lower()
    if current_stage >= 3 and any(word in lower for word in STAGE3_TRIGGER_WORDS):
        return 3
    if current_stage >= 2 and any(word in lower for word in STAGE2_HINT_WORDS):
        return 2
    if any(word in lower for word in {"age", "cm", "kg", "weight", "height", "active", "sex"}):
        return 1
    return max(1, current_stage)


async def _delete_session(session_id: str) -> None:
    url = f"{DEFAULT_API_BASE}/sessions/{session_id}"
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            await client.delete(url)
    except httpx.HTTPError:
        pass  # non-fatal for reset


async def _call_stage(stage: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{DEFAULT_API_BASE}/stage/{stage}"
    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def _build_plan_text(plan: Dict[str, Any]) -> str:
    lines = [
        f"Target calories: {plan.get('target_calories', 'N/A')} kcal/day",
        f"Maintenance (TDEE): {plan.get('tdee', 'N/A')} kcal/day",
        "",
        "Breakfasts:",
    ]
    for recipe in plan.get("breakfasts", []):
        title = recipe.get("title", "Breakfast")
        kcal = recipe.get("calories_per_serving", "?")
        servings = recipe.get("servings", "?")
        lines.append(f"- {title} — {kcal} kcal/serving (serves {servings})")

    lines.append("")
    lines.append("Mains:")
    for recipe in plan.get("mains", []):
        title = recipe.get("title", "Meal")
        kcal = recipe.get("calories_per_serving", "?")
        servings = recipe.get("servings", "?")
        lines.append(f"- {title} — {kcal} kcal/serving (serves {servings})")

    return "\n".join(lines)


def _build_shopping_list_text(shopping_list: List[Dict[str, Any]]) -> str:
    lines = [f"Total items: {len(shopping_list)}", ""]
    for item in shopping_list:
        qty = item.get("qty", "?")
        unit = item.get("unit", "")
        name = item.get("name", "Ingredient")
        lines.append(f"- {qty} {unit} {name}".strip())
    return "\n".join(lines)


async def _stream_stage_three(session_id: str) -> Dict[str, Any]:
    url = f"{DEFAULT_API_BASE}/stage/3/stream"
    payload = {"session_id": session_id}
    progress_msg = cl.Message(content="🔄 Generating your plan...\n", author="DishGenius")
    await progress_msg.send()

    final_payload: Dict[str, Any] = {}

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        async with client.stream("POST", url, json=payload) as response:
            if response.status_code != 200:
                detail = await response.aread()
                message = detail.decode("utf-8", errors="ignore") or response.reason_phrase
                raise httpx.HTTPStatusError(
                    message,
                    request=response.request,
                    response=response,
                )

            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    await progress_msg.stream_token(f"⚠️ Received malformed event: {line}\n")
                    continue

                event_type = event.get("type")

                if event_type == "status":
                    message = event.get("message")
                    if message:
                        await progress_msg.stream_token(f"• {message}\n")
                elif event_type == "recipes":
                    await progress_msg.stream_token("• Recipes ready:\n")
                    breakfasts = event.get("breakfasts") or []
                    mains = event.get("mains") or []
                    if breakfasts:
                        await progress_msg.stream_token("   - Breakfasts: " + ", ".join(breakfasts) + "\n")
                    if mains:
                        await progress_msg.stream_token("   - Mains: " + ", ".join(mains) + "\n")
                elif event_type == "tool":
                    tool = event.get("tool", "tool")
                    phase = event.get("phase", "")
                    ingredient = event.get("ingredient")
                    product = event.get("product")
                    reason = event.get("reason")
                    parts = [f"• [{tool}] {phase}"]
                    if ingredient:
                        parts.append(f"{ingredient}")
                    if product:
                        parts.append(f"→ {product}")
                    if reason:
                        parts.append(f"({reason})")
                    await progress_msg.stream_token(" ".join(parts) + "\n")
                elif event_type == "error":
                    message = event.get("message", "An error occurred during plan generation.")
                    await progress_msg.stream_token(f"❌ {message}\n")
                elif event_type == "final":
                    final_payload = event.get("payload") or {}
                elif event_type == "complete":
                    break

    await progress_msg.stream_token("✅ Plan generation complete!\n")

    return final_payload


async def _start_session(welcome: bool = True) -> None:
    prev_session = cl.user_session.get("session_id")
    if prev_session:
        await _delete_session(prev_session)

    session_id = uuid.uuid4().hex
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("current_stage", 1)
    cl.user_session.set("coach_state", {})
    cl.user_session.set("plan_payload", None)
    cl.user_session.set("shopping_list", None)
    cl.user_session.set("cart_url", None)

    if welcome:
        welcome_msg = await cl.Message(content=WELCOME_MESSAGE, author="DishGenius").send()
        await cl.Action(
            name="new_session",
            payload={"intent": "reset"},
            label="Start Over",
        ).send(for_id=welcome_msg.id)


@cl.action_callback("new_session")
async def _reset_action(action: cl.Action) -> None:
    await _start_session(welcome=True)


@cl.on_chat_start
async def on_chat_start() -> None:
    await _start_session(welcome=True)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    content = (message.content or "").strip()
    if not content:
        await cl.Message(content="Please share a bit more detail so I can help!", author="DishGenius").send()
        return

    session_id = cl.user_session.get("session_id")
    if not session_id:
        await _start_session(welcome=False)
        session_id = cl.user_session.get("session_id")

    cl.logger.info("Session %s | incoming: %s", session_id, content)
    current_stage = cl.user_session.get("current_stage", 1)
    stage_to_call = _infer_stage(content, current_stage)

    try:
        if stage_to_call in (1, 2):
            response = await _call_stage(stage_to_call, {"session_id": session_id, "text": content})
            cl.logger.debug("Session %s | stage %s response: %s", session_id, stage_to_call, response)
            say = response.get("say") or "Thanks!"
            await cl.Message(content=say, author="DishGenius").send()

            state = response.get("state") or {}
            cl.user_session.set("coach_state", state)

            if stage_to_call == 1 and _profile_complete(state) and _goal_complete(state):
                cl.user_session.set("current_stage", 2)
            elif stage_to_call == 2 and _prefs_complete(state):
                cl.user_session.set("current_stage", 3)
            else:
                cl.user_session.set("current_stage", max(current_stage, stage_to_call))

        else:  # stage 3
            cl.user_session.set("current_stage", 3)
            final_payload = await _stream_stage_three(session_id)

            if not final_payload:
                await cl.Message(
                    content="Plan generation finished without results. Feel free to try again!",
                    author="DishGenius",
                ).send()
                return

            say = final_payload.get("say")
            if say:
                await cl.Message(content=say, author="DishGenius").send()

            plan = final_payload.get("plan") or {}
            shopping_list = final_payload.get("shopping_list") or []
            cart_url = final_payload.get("cart_url")

            cl.user_session.set("plan_payload", plan)
            cl.user_session.set("shopping_list", shopping_list)
            cl.user_session.set("cart_url", cart_url)

            elements: List[Text] = []
            if plan:
                elements.append(Text(name="Weekly Plan", content=_build_plan_text(plan)))
            if shopping_list:
                elements.append(Text(name="Shopping List", content=_build_shopping_list_text(shopping_list)))

            summary_lines = []
            if cart_url:
                summary_lines.append(f"[Open your Picnic cart]({cart_url})")
            else:
                summary_lines.append("No cart link available (demo mode).")
            summary_lines.append("Use the action below to start a new session anytime.")

            await cl.Message(
                content="📦 I've attached your plan details below.",
                author="DishGenius",
                elements=elements,
            ).send()

            await cl.Message(content="\n".join(summary_lines), author="DishGenius").send()

    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        cl.logger.exception("Session %s | API error %s", session_id, exc)
        await cl.Message(
            content=f"❌ API error {exc.response.status_code}: {detail}",
            author="DishGenius",
        ).send()
    except httpx.HTTPError as exc:
        cl.logger.exception("Session %s | network error", session_id)
        await cl.Message(
            content=f"❌ Network error while contacting the backend: {exc}",
            author="DishGenius",
        ).send()
    except Exception as exc:  # noqa: BLE001
        cl.logger.exception("Session %s | unexpected error", session_id)
        await cl.Message(
            content=f"❌ Something went wrong: {exc}",
            author="DishGenius",
        ).send()
