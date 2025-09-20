# Meal Coach Agent – Prototype Plan

## 1. Goals & Guardrails
- Deliver a nutrition + grocery planning agent that can gather goals, generate recipes, and hand off a shoppable cart link.
- Keep Prototype 1 fully deterministic and demoable without live voice/WebSocket dependencies.
- Use official/low-risk integrations where possible (Instacart MCP for cart link, optional hosted MCP provider such as Composio/Gumloop).
- Preserve structured state (Pydantic models) across stages so Prototype 2 can reuse the same core logic.

## 2. Shared Domain Layer (Both Prototypes)
- Define domain models in `domain.py`: `Profile`, `Goal`, `FoodPrefs`, `Recipe`, `Ingredient`, `WeekPlan`, `CoachState`.
- Implement calorie math utilities (Mifflin–St Jeor, activity factors, surplus/deficit per rate category).
- Provide aggregation helper to consolidate recipe ingredients into a weekly shopping list.
- Create PydanticAI agents:
  - `collect_agent` – slot filling for profile/goal/prefs (output → `CollectOut`).
  - `recipes_agent` – generates two breakfasts + three mains respecting calorie target/prefs.
- Stub `groceries_checkout(ingredients)`; swap with Instacart MCP tool later (maps ingredient list to Instacart Create Shopping List/Recipe endpoint and returns checkout URL).

## 3. Prototype 1 – Turn-Based Stepper (HTTP + optional push-to-talk)
### UX Flow
1. **Stage 1 – Profile & Goal Intake**
   - User submits short text or audio clip (batch STT via ElevenLabs `scribe_v1`).
   - Backend calls `collect_agent` → merges fields into `CoachState.profile`/`goal`.
   - When required slots filled, call `compute_targets(state)` → respond with calorie summary + prompt for food prefs.
2. **Stage 2 – Food Preferences**
   - Continue calling `collect_agent` with user text until `breakfasts_like` (2 items) & `mains_like` (3 items) captured; also record allergies/dislikes.
3. **Stage 3 – Plan & Cart**
   - Prompt `recipes_agent` with target calories + prefs → obtain 5 recipes.
   - Aggregate ingredients → call `groceries_checkout` (Instacart MCP) → receive cart/deep link.
   - Return payload containing structured plan, shopping list, cart URL.

### Implementation Notes
- Framework: FastAPI app with three endpoints (`/stage/1`, `/stage/2`, `/stage/3`). Persist `CoachState` per session (in-memory dict keyed by session id or JWT).
- Optional voice: frontend records audio → POST to `/stage/1` or `/stage/2`; backend uses ElevenLabs STT. Responses can be text or TTS (stream back `eleven_flash_v2_5`).
- MCP integration (P1 scope): use hosted Instacart MCP over HTTP/Streamable (requires token). Tool call payload includes ingredient names, quantities, optional UPC hints.
- Deliverables: domain module, FastAPI router, simple SPA/Page that walks user through stages, mocked Instacart response when credentials absent.

## 4. Prototype 2 – Conversational WS Agent (Full Duplex)
### Experience
- Voice-first, continuous conversation via ElevenLabs Conversational AI WS (handles ASR, VAD, TTS, barge-in).
- ElevenLabs Agent prompt instructs model to gather fields, then call client tools sequentially.
- Client tools (Python functions) wrap PydanticAI logic:
  - `coach_turn` (ongoing slot filling, reuse P1 logic or split into `collect_profile` / `collect_prefs`).
  - `calc_targets` – runs calorie math once data ready, speaks summary.
  - `generate_plan` – calls `recipes_agent`, stores `WeekPlan` in session state.
  - `groceries_checkout` – same MCP call as P1.
- Tools return `{"say": str, "state": CoachState, ...}`; ElevenLabs streams the `say` audio automatically.

### Stack & Wiring
- Reuse `domain.py` from P1.
- ElevenLabs SDK (`Conversation`) with `ClientTools` registering the Python functions.
- State persistence: map `conversation_id` → `CoachState` (in-memory cache or Redis for scalability).
- Error handling: respond with fallback speech if tool raises (set `is_error` flag in WS protocol).
- UI: optional browser client with microphone; otherwise run locally with `DefaultAudioInterface`.

## 5. MCP & Groceries Integration Plan
1. **Instacart MCP (Preferred for Demo)**
   - Acquire hosted MCP endpoint/token (e.g., Composio catalog or Gumloop remote server).
   - Tool to call: `create_shopping_list_page` or `create_recipe_page`.
   - Payload mapping: recipe ingredient list → line_items (name, quantity, unit, optional UPC/brand).
   - Response: URL for user to open, choose store, and checkout.
2. **Fallback / Offline Mode**
   - Provide mock response (e.g., `https://instacart.com/fakelink`) for demos without credentials.
   - Log payload for future debugging.
3. **Future Enhancements**
   - Add UPC mapping via Open Food Facts/Spoonacular or stored UPC dict for higher accuracy.
   - Support alternate grocers (Kroger, Picnic) by switching MCP endpoint + auth config.

## 6. Testing Strategy
- Unit tests for calorie calculations and ingredient aggregation.
- Contract tests for `collect_agent` / `recipes_agent` prompts using mocked LLM responses.
- Integration smoke test hitting hosted Instacart MCP (record sanitized payload/URL).
- For P2, run conversational dry-runs (scripted audio) to verify tool call ordering.

## 7. Delivery Checklist
- [ ] `domain.py` with models/utilities/agents.
- [ ] FastAPI endpoints + session handling (P1).
- [ ] Optional frontend or CLI driving the three stages.
- [ ] ElevenLabs WS script for P2 (using real mic for demo) + instructions.
- [ ] Config docs (`.env` template with OpenAI, ElevenLabs, MCP tokens).
- [ ] README snippet explaining how to switch between P1 (stepper) and P2 (realtime).
