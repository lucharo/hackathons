"""Minimal stage-based Streamlit client for local experimentation.

This version keeps only the core flow: two text inputs feeding stage 1/2
endpoints and a single button to trigger stage 3 generation.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict

import httpx
import streamlit as st


API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:8000")
API_TIMEOUT = float(os.environ.get("API_TIMEOUT", "60"))
API_CONNECT_TIMEOUT = float(os.environ.get("API_CONNECT_TIMEOUT", "10"))
API_WRITE_TIMEOUT = float(os.environ.get("API_WRITE_TIMEOUT", "30"))

DEFAULT_STAGE1 = "Share age, height, weight, activity level, and your goal."
DEFAULT_STAGE2 = "List breakfast and main dishes you enjoy plus any allergies."


@st.cache_resource(show_spinner=False)
def get_client() -> httpx.Client:
    timeout = httpx.Timeout(
        connect=API_CONNECT_TIMEOUT,
        read=API_TIMEOUT,
        write=API_WRITE_TIMEOUT,
        pool=None,
    )
    return httpx.Client(base_url=API_BASE, timeout=timeout)


def ensure_session_state() -> None:
    if "session_id" not in st.session_state:
        st.session_state.session_id = uuid.uuid4().hex
    st.session_state.setdefault("log", [])


def call_stage(stage: str, text: str | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"session_id": st.session_state.session_id}
    if text is not None:
        payload["text"] = text.strip()

    client = get_client()
    try:
        response = client.post(f"/stage/{stage}", json=payload)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip() or exc.response.reason_phrase
        st.error(f"Backend error {exc.response.status_code}: {detail}")
        raise
    except httpx.ConnectTimeout:
        st.error(
            "Unable to reach the backend within "
            f"{API_CONNECT_TIMEOUT:.0f}s. Ensure {API_BASE} is running or set "
            "API_CONNECT_TIMEOUT to a higher value."
        )
        raise
    except httpx.ReadTimeout:
        st.error(
            "Backend took longer than "
            f"{API_TIMEOUT:.0f}s to respond. Try again or increase API_TIMEOUT."
        )
        raise
    except httpx.RequestError as exc:
        st.error(f"Network error while contacting {API_BASE}: {exc}")
        raise

    return response.json()


def render_stage(stage: str, label: str, default_text: str) -> None:
    text = st.text_area(label, value=default_text, key=f"stage_{stage}")
    if st.button(f"Submit stage {stage}", use_container_width=True, key=f"submit_{stage}"):
        if not text.strip():
            st.warning("Please add some text before submitting.")
            return
        try:
            data = call_stage(stage, text)
        except httpx.HTTPStatusError:
            return
        except httpx.RequestError as exc:
            st.error(f"Network error while contacting {API_BASE}: {exc}")
            return
        st.session_state.log.append((stage, text.strip(), data.get("say", "")))


def render_stage_three() -> None:
    if st.button("Generate weekly plan", type="primary", use_container_width=True):
        try:
            data = call_stage("3")
        except httpx.HTTPStatusError:
            return
        except httpx.RequestError as exc:
            st.error(f"Network error while contacting {API_BASE}: {exc}")
            return
        st.session_state.log.append(("3", "<generate plan>", data.get("say", "")))
        if plan := data.get("plan"):
            st.markdown("### Plan")
            st.json(plan)
        if shopping := data.get("shopping_list"):
            st.markdown("### Shopping list")
            st.json(shopping)
        if cart := data.get("cart_url"):
            st.markdown(f"[Open cart]({cart})")


def main() -> None:
    st.set_page_config(page_title="Stage demo", page_icon="🥗", layout="wide")
    ensure_session_state()

    st.sidebar.write(f"Session: `{st.session_state.session_id}`")
    st.sidebar.caption(f"Backend: {API_BASE}")

    col1, col2 = st.columns(2)
    with col1:
        render_stage("1", "Stage 1 – profile & goal", DEFAULT_STAGE1)
    with col2:
        render_stage("2", "Stage 2 – food preferences", DEFAULT_STAGE2)

    st.divider()
    render_stage_three()

    if st.session_state.log:
        st.divider()
        st.markdown("### Conversation log")
        for stage, question, reply in st.session_state.log[::-1]:
            st.write(f"**Stage {stage}**")
            st.write(question)
            st.info(reply)


if __name__ == "__main__":
    main()
