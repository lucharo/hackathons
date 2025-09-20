# Nutrition Coach – Prototype 1

Minimal instructions to run the staged FastAPI backend and the Streamlit client.

## Prerequisites
- Python environment managed by `uv` (already configured in this repo).
- `ANTHROPIC_API_KEY` exported for Claude 4 Sonnet.
- Optional: `ELEVENLABS_API_KEY` if you plan to send audio (`audio_base64`) to the backend.

## Start the FastAPI Backend
```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run uvicorn app:app --reload
```
The backend also loads environment variables from a local `.env` file if present (thanks to `python-dotenv`).
The server listens on `http://127.0.0.1:8000` and exposes `/stage/1`, `/stage/2`, `/stage/3`, plus `/sessions/{session_id}` for resets.

## Launch the Streamlit Client
In a second terminal:
```bash
export ANTHROPIC_API_KEY=sk-ant-...   # same key so Streamlit requests inherit it
uv run streamlit run streamlit_app.py
```
The Streamlit client also respects values from a local `.env` file.
The app targets `http://127.0.0.1:8000` by default. Override via `~/.streamlit/secrets.toml`:
```toml
api_base = "http://localhost:8000"
api_timeout = 20
```

## Usage Flow
1. Fill in Stage 1 with profile + goal details; submit to let the intake agent collect missing fields.
2. Provide Stage 2 preferences (two breakfasts, three mains, plus allergies/dislikes).
3. Click **Generate Weekly Plan** to trigger recipe generation, ingredient aggregation, and cart link creation (stubbed URL until MCP credentials are wired in).
4. Use the sidebar to reset the session, which also clears server-side state.

Consult `plan.md` for the broader roadmap and integration notes.
