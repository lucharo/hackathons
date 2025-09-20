"""Minimal Chainlit chat client for exploring the nutrition coach API."""

from __future__ import annotations

import json
import os
import uuid

import chainlit as cl
import httpx


API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
API_TIMEOUT = float(os.environ.get("API_TIMEOUT", "60"))

PLAN_KEYWORDS = {"plan", "generate", "shopping", "recipe"}


async def post_stage(stage: int, payload: dict) -> dict:
    url = f"{API_BASE}/stage/{stage}"
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        response = await client.post(url, json=payload)
    response.raise_for_status()
    return response.json()


@cl.on_chat_start
async def start_chat() -> None:
    session_id = uuid.uuid4().hex
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("next_stage", 1)
    await cl.Message(
        "Hi! Share your profile first, then your food preferences. "
        "Type 'generate plan' when you're ready for recipes."
    ).send()


@cl.on_message
async def handle_message(message: cl.Message) -> None:
    session_id: str = cl.user_session.get("session_id")
    next_stage: int = cl.user_session.get("next_stage", 1)
    text = message.content.strip()
    lowered = text.lower()

    if not text:
        await cl.Message("Please add some details first.").send()
        return

    if any(keyword in lowered for keyword in PLAN_KEYWORDS):
        stage = 3
        payload = {"session_id": session_id}
    else:
        stage = next_stage
        payload = {"session_id": session_id, "text": text}
        cl.user_session.set("next_stage", min(2, next_stage + 1))

    try:
        data = await post_stage(stage, payload)
    except httpx.HTTPError as exc:
        await cl.Message(
            f"Couldn't reach the backend ({exc}). Is {API_BASE} running?"
        ).send()
        return

    reply = data.get("say") or "(no response)"
    await cl.Message(reply).send()

    if stage == 3:
        plan = data.get("plan")
        shopping = data.get("shopping_list")
        cart = data.get("cart_url")

        if plan:
            pretty_plan = json.dumps(plan, indent=2)
            await cl.Message(content="Here's your plan:", author="Coach").send()
            await cl.Message(content=f"```json\n{pretty_plan}\n```", author="Coach").send()
        if shopping:
            pretty_list = json.dumps(shopping, indent=2)
            await cl.Message(content="Shopping list ready!", author="Coach").send()
            await cl.Message(content=f"```json\n{pretty_list}\n```", author="Coach").send()
        if cart:
            await cl.Message(content=f"Cart: {cart}", author="Coach").send()
