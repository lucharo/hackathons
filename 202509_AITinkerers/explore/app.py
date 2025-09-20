from __future__ import annotations

import asyncio
import base64
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from domain import (
    CoachState,
    FoodPrefs,
    Goal,
    Profile,
    ProgressCallback,
    generate_week_plan,
    groceries_checkout,
    update_prefs_from_text,
    update_profile_from_text,
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


def _validate_stage_three_ready(state: CoachState) -> None:
    if not (profile_complete(state.profile) and goal_complete(state.goal)):
        raise HTTPException(status_code=400, detail="Profile and goal are incomplete")
    if state.target_calories is None:
        state.target_calories = 2000
    if state.tdee is None:
        state.tdee = 2200
    if not prefs_complete(state.prefs):
        raise HTTPException(status_code=400, detail="Food preferences are incomplete")


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


async def _run_stage_three(state: CoachState, progress_cb: ProgressCallback | None = None) -> Dict[str, Any]:
    async def emit(event: Dict[str, Any]) -> None:
        if progress_cb:
            await progress_cb(event)

    await emit({"type": "status", "message": "Generating personalized recipes..."})

    plan, shopping_list, say = generate_week_plan(state)
    breakfasts = plan.breakfasts
    mains = plan.mains

    await emit(
        {
            "type": "recipes",
            "message": "Recipes ready.",
            "breakfasts": [recipe.title for recipe in breakfasts],
            "mains": [recipe.title for recipe in mains],
        }
    )

    state.plan = plan
    state.target_calories = plan.target_calories
    state.tdee = plan.tdee

    await emit(
        {
            "type": "status",
            "message": f"Preparing grocery list with {len(shopping_list)} ingredients...",
        }
    )

    cart_url = await groceries_checkout(shopping_list, progress_cb=progress_cb)
    state.cart_url = cart_url

    response = {
        "say": say,
        "plan": plan.model_dump(),
        "shopping_list": [item.model_dump() for item in shopping_list],
        "cart_url": cart_url,
    }

    await emit({"type": "status", "message": "Plan generation complete."})
    if cart_url:
        await emit({"type": "status", "message": "Cart link ready."})

    return response


@app.post("/stage/1")
async def stage_one(request: StageRequest):
    state = get_state(request.session_id)

    user_text = request.text
    if not user_text and request.audio_base64:
        user_text = transcribe_audio(request.audio_base64)
    if not user_text:
        raise HTTPException(status_code=400, detail="Provide text or audio_base64")

    say = update_profile_from_text(state, user_text)

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

    say = update_prefs_from_text(state, user_text)

    return {"say": say, "state": state.model_dump()}


@app.post("/stage/3")
async def stage_three(request: Stage3Request):
    state = get_state(request.session_id)
    _validate_stage_three_ready(state)
    return await _run_stage_three(state)


@app.post("/stage/3/stream")
async def stage_three_stream(request: Stage3Request):
    state = get_state(request.session_id)
    _validate_stage_three_ready(state)

    queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()

    async def progress(event: Dict[str, Any]) -> None:
        await queue.put(event)

    async def worker() -> None:
        try:
            await queue.put({"type": "status", "message": "Starting plan generation..."})
            payload = await _run_stage_three(state, progress)
            await queue.put({"type": "final", "payload": payload})
        except Exception as exc:  # noqa: BLE001
            detail = str(exc)
            await queue.put({"type": "error", "message": detail})
        finally:
            await queue.put({"type": "complete"})

    worker_task = asyncio.create_task(worker())

    async def event_stream():
        try:
            while True:
                event = await queue.get()
                if event.get("type") == "complete":
                    break
                yield json.dumps(event, ensure_ascii=False) + "\n"
        finally:
            await worker_task

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


@app.delete("/sessions/{session_id}")
async def reset_session(session_id: str):
    _STATE_STORE.pop(session_id, None)
    return {"detail": "Session cleared"}
