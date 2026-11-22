# AGENTS.md: AI Agent Development Guide

## 1. Project Overview
The **Weather Chatbot** is an interactive AI application built with **LangChain**, xAI's **grok-4.7** model, and the **OpenWeather REST API**. 
The application provides real-time weather information and 5-day forecasts while strictly enforcing topic boundaries and defending against prompt injection, jailbreaks, and API service hijacking.

All functional requirements are formally defined in `@FRs.md`.

---

## 2. Tech Stack & Commands
- **Backend / AI Orchestration:** Python 3.10+, LangChain (`langchain`, `langchain-xai`, `langchain-core`)
- **LLM Engine:** xAI `grok-4.7` via `ChatXAI(model="grok-4.7")`
- **External Data Source:** OpenWeather REST APIs (Current Weather API & 5-Day Forecast API)
- **Frontend / UI:** Streamlit (`streamlit`)
- **Secrets Management:** `python-dotenv` (reading `.env` loaded via `os.getenv`)
- **Testing:** `pytest`
- **Dependency Management:** Python `pip` / `venv` or `uv`

### Common Commands:
- **Activate Virtual Environment:**
  - Windows: `.\venv\Scripts\activate` or `.venv\Scripts\Activate.ps1`
- **Install Dependencies:** `pip install -r requirements.txt`
- **Run Tests:** `pytest` or `python -m pytest`
- **Run Application:** `streamlit run app.py`

---

## 3. Project Structure
Keep the file tree modular, clean, and separation-of-concerns focused:

```
WeatherChatbot/
├── .env.example              # Placeholder environment secrets
├── .gitignore                # Strictly excludes .env and python caches
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation and security reflection
├── AGENTS.md                 # Agent context & guidelines
├── FRs.md                    # Functional requirements specifications
├── USER_STORIES.md           # User stories mapped to FRs
├── app.py                    # Streamlit frontend chat application
├── src/
│   ├── __init__.py
│   ├── config.py             # Environment configuration & credential validation
│   ├── weather_tools.py      # OpenWeather API functions & LangChain @tool definitions
│   ├── security.py           # Guardrails: Prompt injection & hijacking detection
│   └── agent.py              # LangChain ChatXAI agent pipeline & tool binding
└── tests/
    ├── __init__.py
    ├── test_weather_tools.py # Tests for OpenWeather API integration & parsing
    ├── test_security.py      # Tests for prompt injection & off-topic refusal
    └── test_agent.py         # Tests for LangChain tool calling & agent execution
```

---

## 4. Architectural & Coding Guidelines
1. **Zero-Hardcoded Secrets**: NEVER hardcode API keys or commit `.env` to version control. Load keys dynamically using `python-dotenv`.
2. **Defensive AI Engineering**:
   - The chatbot must answer **only** weather-related queries.
   - Any query attempting to repurpose the chatbot as a general-purpose LLM (coding, essays, general Q&A) or override system instructions (jailbreaks, "developer mode", prompt leaks) must be blocked and refused.
   - Use a **multi-layer defense strategy**:
     - *Layer 1 (Code-Level Pre-Screening Filter)*: Fast deterministic filter detecting known injection payloads, sensitive keywords (e.g., `.env`, `system prompt`), and off-topic requests before burning LLM tokens.
     - *Layer 2 (System Prompt Boundary Enforcement)*: Rigorous system instructions instructing `grok-4.7` on its role, allowed tools, and refusal policy.
3. **Structured Tool Calling**: Tools must be registered with `@tool`, have clear docstrings for parameter extraction by `grok-4.7`, and return sanitized JSON/structured output.
4. **Clean Interactive UI**: Streamlit must display conversational turns with `st.chat_message`, format weather data with readable cards/markdown, and show clear safety refusal messages.

---

## 5. Implementation Strategy (Test-Driven Development)
Work incrementally through the step files (`step-01-weather-tools.md`, etc.):
1. Create unit tests in `tests/` verifying expected functionality and edge cases.
2. Run `pytest` to verify initial test failures.
3. Implement the minimal codebase logic in `src/` to satisfy the tests.
4. Re-run `pytest` until all tests pass (exit code 0).
5. Integrate with the Streamlit UI and manually verify in the browser.

---

## 6. Git Commit Directives
After completing each step and confirming tests pass:
- Ensure `.env` is never staged (`git status` check).
- Stage relevant modified files (`git add <files>`).
- Commit using conventional commit format:
  - `git commit -m "<type>(<scope>): <short description>"`
  - Examples:
    - `feat(tools): implement openweather current weather and 5-day forecast tools`
    - `feat(security): implement prompt injection and hijacking guardrails`
    - `feat(agent): initialize langchain chatxai pipeline with tool binding`
    - `feat(ui): build streamlit weather chat interface`
