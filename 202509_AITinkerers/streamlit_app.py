from __future__ import annotations

import uuid
import os
from typing import Any, Dict, List

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEFAULT_API_BASE = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT = 120.0
DEFAULT_STAGE1 = (
    "Hi, I'm a 34-year-old male, 182 cm, 82 kg, moderately active, and I'd like to "
    "lose weight fast."
)
DEFAULT_STAGE2 = (
    "Breakfasts: overnight oats, tofu scramble. Dinners: chickpea curry, lentil "
    "tacos, veggie stir fry. No peanuts please."
)

try:
    API_BASE = st.secrets["api_base"]
except Exception:  # noqa: BLE001 - Streamlit raises if secrets missing
    API_BASE = os.environ.get("API_BASE", DEFAULT_API_BASE)

try:
    TIMEOUT = float(st.secrets["api_timeout"])  # type: ignore[arg-type]
except Exception:  # noqa: BLE001
    TIMEOUT = float(os.environ.get("API_TIMEOUT", DEFAULT_TIMEOUT))

st.set_page_config(page_title="Nutrition Coach – P1", page_icon="🥗", layout="wide")


@st.cache_resource(show_spinner=False)
def get_client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, timeout=TIMEOUT)


def ensure_session_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex
    st.session_state.setdefault("conversation", [])
    st.session_state.setdefault("state_payload", None)
    st.session_state.setdefault("plan_payload", None)
    st.session_state.setdefault("shopping_list", None)
    st.session_state.setdefault("cart_url", None)



def call_api(method: str, endpoint: str, json_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    client = get_client()
    try:
        response = client.request(method, endpoint, json=json_payload)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:  # network-level message
        detail = exc.response.text
        st.error(f"API error {exc.response.status_code}: {detail}")
        raise
    except httpx.RequestError as exc:
        st.error(f"Failed to contact API: {exc}")
        raise
    return response.json()


def append_turn(stage: str, user_text: str, reply: str) -> None:
    st.session_state.conversation.append(
        {
            "stage": stage,
            "input": user_text,
            "reply": reply,
        }
    )


def handle_stage(stage: str, text: str) -> None:
    if not text.strip():
        st.warning("Please provide some text before submitting.")
        return
    payload = {"session_id": st.session_state.session_id, "text": text.strip()}
    with st.spinner("Contacting backend..."):
        data = call_api("POST", f"/stage/{stage}", payload)
    append_turn(stage, text.strip(), data.get("say", ""))
    st.session_state.state_payload = data.get("state")
    if data.get("plan"):
        st.session_state.plan_payload = data.get("plan")
    if data.get("shopping_list"):
        st.session_state.shopping_list = data.get("shopping_list")
    if data.get("cart_url"):
        st.session_state.cart_url = data.get("cart_url")


def handle_stage_three() -> None:
    payload = {"session_id": st.session_state.session_id}
    try:
        with st.status("Generating weekly plan...", expanded=True) as status:
            status.update(label="Calling backend...", state="running")
            data = call_api("POST", "/stage/3", payload)
            status.update(label="Processing response...", state="running")
            append_turn("3", "<generate plan>", data.get("say", ""))
            st.session_state.plan_payload = data.get("plan")
            st.session_state.shopping_list = data.get("shopping_list")
            st.session_state.cart_url = data.get("cart_url")
            status.update(label="Plan ready", state="complete")
    except httpx.HTTPError:
        # call_api already surfaced an error
        st.stop()


ensure_session_state()
st.title("Prototype 1 – Nutrition Coach")
st.caption("Guide the user through intake, preferences, and generate a weekly plan with a grocery link.")

with st.sidebar:
    st.subheader("Session")
    st.write(f"ID: `{st.session_state.session_id}`")
    if st.button("New session", type="primary"):
        client = get_client()
        try:
            client.delete(f"/sessions/{st.session_state.session_id}")
        except httpx.RequestError:
            pass
        st.session_state.session_id = uuid.uuid4().hex
        st.session_state.conversation = []
        st.session_state.state_payload = None
        st.session_state.plan_payload = None
        st.session_state.shopping_list = None
        st.session_state.cart_url = None
        st.rerun()

    st.markdown("---")
    st.markdown("**Backend URL**")
    st.write(API_BASE)

col1, col2 = st.columns([1, 1])

with col1:
    st.header("Stage 1 – Profile & Goal")
    stage1_text = st.text_area(
        "Describe yourself (age, height, weight, activity, goal)",
        value=DEFAULT_STAGE1,
        key="stage1_text",
    )
    if st.button("Submit Stage 1", use_container_width=True):
        handle_stage("1", stage1_text)

with col2:
    st.header("Stage 2 – Food Preferences")
    stage2_text = st.text_area(
        "Share foods you like/dislike (2 breakfasts, 3 mains)",
        value=DEFAULT_STAGE2,
        key="stage2_text",
    )
    if st.button("Submit Stage 2", use_container_width=True):
        handle_stage("2", stage2_text)

st.markdown("### Stage 3 – Plan & Cart")
st.write("After stages 1 and 2 are complete, generate the recipes and shopping list.")
if st.button("Generate Weekly Plan", type="primary"):
    handle_stage_three()

if st.session_state.conversation:
    st.markdown("### Conversation Log")
    for turn in st.session_state.conversation[::-1]:
        with st.expander(f"Stage {turn['stage']} – {turn['input'][:40]}", expanded=False):
            st.markdown(f"**User:** {turn['input']}")
            st.markdown(f"**Coach:** {turn['reply']}")

if st.session_state.state_payload:
    st.markdown("### Session State")
    st.json(st.session_state.state_payload)

if st.session_state.plan_payload:
    st.markdown("### Generated Plan")
    plan = st.session_state.plan_payload
    st.write(f"Maintenance: {plan.get('tdee')} kcal/day")
    st.write(f"Target: {plan.get('target_calories')} kcal/day")

    def render_recipes(label: str, items: List[Dict[str, Any]]):
        st.subheader(label)
        for recipe in items:
            with st.expander(recipe.get("title", "Recipe")):
                st.markdown(f"**Servings:** {recipe.get('servings')} | **Calories/serving:** {recipe.get('calories_per_serving')}")
                st.markdown("**Ingredients**")
                ing_lines = [
                    f"- {ing['qty']} {ing['unit']} {ing['name']}"
                    for ing in recipe.get("ingredients", [])
                ]
                st.markdown("\n".join(ing_lines) or "(none)")
                st.markdown("**Steps**")
                steps = recipe.get("steps", [])
                st.markdown("\n".join(f"{idx+1}. {step}" for idx, step in enumerate(steps)) or "(none)")

    render_recipes("Breakfasts", plan.get("breakfasts", []))
    render_recipes("Lunch / Dinner", plan.get("mains", []))

if st.session_state.shopping_list:
    st.markdown("### Shopping List")
    st.table(st.session_state.shopping_list)

if st.session_state.cart_url:
    st.markdown("### Cart Link")
    st.markdown(f"[Open cart]({st.session_state.cart_url})")
