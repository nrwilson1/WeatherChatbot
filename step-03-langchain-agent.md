# Step 03: LangChain ChatXAI Agent & Tool-Calling Pipeline

## 1. Session Scope
- **Target FRs:** FR-2 (Current Weather Tool Calling), FR-3 (5-Day Forecast Tool Calling), FR-4 (Prompt Injection Defense), FR-5 (Anti-Hijacking)
- **Feature Boundaries:**
  - Build `src/agent.py` setting up the LangChain pipeline.
  - Initialize `ChatXAI(model="grok-4.7", api_key=...)`.
  - Bind the OpenWeather `@tool` functions (`get_current_weather`, `get_weather_forecast`).
  - Integrate conversation history with `SystemMessage`, `HumanMessage`, and `AIMessage`.
  - Wire in the `validate_user_prompt` guardrail before agent invocation.
  - Deliver `process_chat(user_message: str, chat_history: list) -> str` as the single entrypoint for the UI.

---

## 2. Prerequisites
- `step-01-weather-tools.md` and `step-02-security-guardrails.md` completed.
- `XAI_API_KEY` configured in `.env`.
- Pytest tests from previous steps all passing.

---

## 3. TDD Test Suite
Create `tests/test_agent.py` with the following test cases:
1. `test_agent_initialization`: Verifies `ChatXAI` initializes with `model="grok-4.7"` and binds the two tools properly.
2. `test_process_chat_blocked_prompt`: Verifies malicious or off-topic prompts are caught by the security guardrail and return the refusal message without calling the model.
3. `test_process_chat_valid_weather_query`: Verifies a valid query (e.g. "What's the weather in Amarillo right now?") triggers tool execution and returns a natural language response.

---

## 4. Implementation Deliverables
- `src/agent.py`:
  - `get_weather_agent()`:
    - Instantiates `ChatXAI(model="grok-4.7", xai_api_key=...)`.
    - Binds tools: `[get_current_weather, get_weather_forecast]`.
    - Creates the LangChain agent/runnable using `create_tool_calling_agent` and `AgentExecutor` (or `bind_tools` loop with tool calling).
  - `process_chat(user_message: str, history: list) -> str`:
    - First executes `validate_user_prompt(user_message)`.
    - If invalid: returns security refusal message immediately.
    - If valid: executes the LangChain agent pipeline, executes any required tool calls to OpenWeather, and returns the final assistant response.

---

## 5. Definition of Done
- Run full test suite:
  ```powershell
  pytest tests/ -v
  ```
- All tests in `test_weather_tools.py`, `test_security.py`, and `test_agent.py` pass.
- Git commit:
  ```powershell
  git add src/agent.py tests/test_agent.py
  git commit -m "feat(agent): implement langchain chatxai pipeline with tool binding"
  ```
