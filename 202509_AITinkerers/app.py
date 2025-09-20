from __future__ import annotations

import base64
import json
import os
from typing import Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from domain import (
    CoachState,
    FoodPrefs,
    Goal,
    Profile,
    Recipe,
    WeekPlan,
    aggregate_ingredients,
    collect_agent,
    compute_targets,
    groceries_checkout,
    recipes_agent,
)

load_dotenv()

try:
    from elevenlabs.client import ElevenLabs

    _eleven_client: Optional[ElevenLabs] = ElevenLabs()
except Exception:  # noqa: BLE001 - swallow missing creds on purpose
    _eleven_client = None

app = FastAPI(title="Nutrition Coach – Prototype 1")

_STATE_STORE: Dict[str, CoachState] = {}


class StageRequest(BaseModel):
    session_id: str
    text: Optional[str] = None
    audio_base64: Optional[str] = None


class Stage3Request(BaseModel):
    session_id: str


def get_state(session_id: str) -> CoachState:
    if session_id not in _STATE_STORE:
        _STATE_STORE[session_id] = CoachState()
    return _STATE_STORE[session_id]


def profile_complete(profile: Profile) -> bool:
    return all(
        [
            profile.sex,
            profile.age is not None,
            profile.height_cm is not None,
            profile.weight_kg is not None,
            profile.activity,
        ]
    )


def goal_complete(goal: Goal) -> bool:
    return all([goal.direction, goal.rate_category])


def prefs_complete(prefs: FoodPrefs) -> bool:
    return len(prefs.breakfasts_like) >= 2 and len(prefs.mains_like) >= 3


def summarise_state(state: CoachState) -> str:
    summary = state.model_dump()
    # keep payload small for the prompt
    summary.pop("plan", None)
    summary.pop("cart_url", None)
    return json.dumps(summary, ensure_ascii=False)


def transcribe_audio(audio_b64: str) -> str:
    if not _eleven_client:
        raise HTTPException(status_code=503, detail="ElevenLabs client unavailable")
    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid audio_base64 payload") from exc

    try:
        response = _eleven_client.speech_to_text.convert(
            file=audio_bytes,
            model_id="scribe_v1",
            language_code="eng",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="Speech-to-text failed") from exc

    return getattr(response, "text", str(response))


async def run_collect_agent(user_text: str, state: CoachState):
    prompt = (
        "Known state: "
        + summarise_state(state)
        + ". New user reply: "
        + user_text
    )
    result = await collect_agent.run(prompt)
    output = result.output
    state.profile = state.profile.model_copy(update=output.profile.model_dump(exclude_none=True))
    state.goal = state.goal.model_copy(update=output.goal.model_dump(exclude_none=True))
    state.prefs = state.prefs.model_copy(update=output.prefs.model_dump(exclude_none=True))
    return output.say


@app.post("/stage/1")
async def stage_one(request: StageRequest):
    state = get_state(request.session_id)

    user_text = request.text
    if not user_text and request.audio_base64:
        user_text = transcribe_audio(request.audio_base64)
    if not user_text:
        raise HTTPException(status_code=400, detail="Provide text or audio_base64")

    say = await run_collect_agent(user_text, state)

    if profile_complete(state.profile) and goal_complete(state.goal) and state.tdee is None:
        try:
            compute_targets(state)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        say = (
            f"Great. Maintenance is about {state.tdee} kcal/day. "
            f"Target is roughly {state.target_calories} kcal/day. "
            "Tell me two breakfasts and three lunch or dinner ideas you enjoy."
        )

    return {"say": say, "state": state.model_dump()}


@app.post("/stage/2")
async def stage_two(request: StageRequest):
    state = get_state(request.session_id)
    if not profile_complete(state.profile) or not goal_complete(state.goal):
        raise HTTPException(status_code=400, detail="Complete stage 1 first")

    user_text = request.text
    if not user_text and request.audio_base64:
        user_text = transcribe_audio(request.audio_base64)
    if not user_text:
        raise HTTPException(status_code=400, detail="Provide text or audio_base64")

    say = await run_collect_agent(user_text, state)

    if prefs_complete(state.prefs):
        say = (
            "Awesome, I have your preferences. Ready to build this week's plan "
            "and shopping list?"
        )

    return {"say": say, "state": state.model_dump()}


@app.post("/stage/3")
async def stage_three(request: Stage3Request):
    state = get_state(request.session_id)
    if not (profile_complete(state.profile) and goal_complete(state.goal)):
        raise HTTPException(status_code=400, detail="Profile and goal are incomplete")
    if state.target_calories is None:
        compute_targets(state)
    if not prefs_complete(state.prefs):
        raise HTTPException(status_code=400, detail="Food preferences are incomplete")

    prompt = (
        "User profile and goal: "
        + summarise_state(state)
        + ". Generate the recipes now."
    )
    result = await recipes_agent.run(prompt)
    output = result.output

    breakfasts = output.breakfasts
    mains = output.mains
    state.plan = WeekPlan(
        breakfasts=breakfasts,
        mains=mains,
        target_calories=state.target_calories or 0,
        tdee=state.tdee or 0,
    )

    shopping_list = aggregate_ingredients(breakfasts + mains)
    cart_url = groceries_checkout(shopping_list)
    state.cart_url = cart_url

    response = {
        "say": output.say or "Plan ready. Here's your grocery list and cart link.",
        "plan": state.plan.model_dump(),
        "shopping_list": [item.model_dump() for item in shopping_list],
        "cart_url": cart_url,
    }
    return response


@app.delete("/sessions/{session_id}")
async def reset_session(session_id: str):
    _STATE_STORE.pop(session_id, None)
    return {"detail": "Session cleared"}
