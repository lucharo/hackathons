# Nutrition Coach – Prototype 1

Minimal instructions to run the staged FastAPI backend and the Streamlit client.

## Prerequisites
- Python environment managed by `uv` (already configured in this repo).
- `ANTHROPIC_API_KEY` exported for Claude 4 Sonnet.
- Optional: `ELEVENLABS_API_KEY` if you plan to send audio (`audio_base64`) to the backend.

## Environment
Create a `.env` file (see `.env.example`) containing at minimum:

```
ANTHROPIC_API_KEY=sk-ant-...
BASE_MODEL=anthropic:claude-sonnet-4-20250514
PICNIC_USERNAME=you@example.com
PICNIC_PASSWORD=super-secret
```

All CLI commands load this file automatically via `just`'s dotenv support.

## Start the FastAPI Backend
```bash
just backend
```
The server listens on `http://127.0.0.1:8000` and exposes `/stage/1`, `/stage/2`, `/stage/3`, plus `/sessions/{session_id}` for resets.

## Launch the Frontend UI
### Chainlit chat (conversational UI)
```bash
just chat
```
This spins up Chainlit on <http://127.0.0.1:8001> with a live chat interface that streams tool usage and attaches plan details.

### Streamlit stepper (detailed controls)
```bash
just frontend
```
The Streamlit client respects values from a local `.env` file.
You can still open `minimal_frontend.html` directly if you prefer an ultra-light static page.

## Start the Picnic MCP Server
```bash
just mcp
```

## All-in-one (MCP + Backend + UI)
```bash
just dev
```
Use `Ctrl+C` to stop; all processes terminate together.
The app targets `http://127.0.0.1:8000` by default. Override via `~/.streamlit/secrets.toml`:
```toml
api_base = "http://localhost:8000"
api_timeout = 20
```

## Usage Flow
1. Fill in Stage 1 with profile + goal details; submit to let the intake agent collect missing fields.
2. Provide Stage 2 preferences (two breakfasts, three mains, plus allergies/dislikes).
3. Ask DishGenius to generate the weekly plan in the Chainlit chat (or click **Generate Weekly Plan** in the Streamlit stepper) to produce recipes, a shopping list, and a Picnic cart link.
4. Use the **Start Over** action in Chainlit or the sidebar reset in Streamlit to clear the session both client- and server-side.

Consult `plan.md` for the broader roadmap and integration notes.
