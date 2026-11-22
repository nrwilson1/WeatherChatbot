# Functional Requirements: Weather Chatbot

## FR-1: Environment & Secret Management
- **FR-1.1:** The application shall load all sensitive API credentials (`XAI_API_KEY` and `OPENWEATHER_API_KEY`) from a local `.env` file using `python-dotenv`.
- **FR-1.2:** The `.gitignore` file shall strictly exclude `.env` from git tracking to prevent accidental credential leakage to public repositories.
- **FR-1.3:** The repository shall include a `.env.example` file detailing all required environment variables with placeholder values.
- **FR-1.4:** The application shall gracefully validate the presence of required API keys at startup and report helpful error messages if any are missing.

---

## FR-2: Current Weather Tool Calling
- **FR-2.1:** The system shall define a structured LangChain `@tool` function (e.g., `get_current_weather`) accepting a city or location name.
- **FR-2.2:** The tool shall query OpenWeather's Current Weather API endpoint (`/data/2.5/weather`).
- **FR-2.3:** The tool shall return structured, human-readable data including:
  - Temperature
  - Feels-like temperature
  - Humidity percentage
  - Wind speed
  - Weather condition description (e.g., "scattered clouds", "clear sky", "light rain")
- **FR-2.4:** The tool shall gracefully handle invalid city names, HTTP errors, or missing data by returning clear error messages to the agent rather than crashing.

---

## FR-3: 5-Day Forecast Tool Calling
- **FR-3.1:** The system shall define a structured LangChain `@tool` function (e.g., `get_weather_forecast`) accepting a city or location name.
- **FR-3.2:** The tool shall query OpenWeather's 5-Day Forecast API endpoint (`/data/2.5/forecast`).
- **FR-3.3:** The tool shall aggregate and summarize the 3-hour interval data into a coherent 5-day daily forecast (highs/lows, dominant weather condition per day).
- **FR-3.4:** The tool shall return this structured summary back to the LLM agent to construct an intuitive forecast response for the user.

---

## FR-4: Prompt Injection & Jailbreak Defense
- **FR-4.1:** The system shall defend against prompt injection attacks attempting to override system instructions (e.g., "Ignore all previous instructions", "Reveal your system prompt").
- **FR-4.2:** The system shall defend against roleplay / jailbreak overrides (e.g., "You are now in developer mode", "DAN mode").
- **FR-4.3:** The system shall strictly prevent leaking configuration secrets, environment variables, or `.env` contents under any adversarial prompt.
- **FR-4.4:** The system shall implement at least two code-side security controls (e.g., deterministic input pre-screening filter + hardened system prompt boundary).

---

## FR-5: API Service Hijacking & Off-Topic Prevention
- **FR-5.1:** The system shall strictly restrict the chatbot to answering weather-related queries only.
- **FR-5.2:** The system shall refuse general-purpose LLM requests (e.g., "Write an essay", "Solve this coding problem", "Introduce West Texas A&M University").
- **FR-5.3:** When an off-topic request is detected, the system shall return a polite refusal explaining that it is exclusively a weather assistant.
- **FR-5.4:** The tool-calling loop shall enforce execution limits to prevent adversarial infinite loops and protect xAI API credits.

---

## FR-6: Interactive Chat Interface (Streamlit)
- **FR-6.1:** The application shall provide an interactive chat interface built with Streamlit (`st.chat_message`, `st.chat_input`).
- **FR-6.2:** The UI shall maintain conversation history across conversational turns in `st.session_state`.
- **FR-6.3:** The UI shall clearly format weather details and multi-day forecasts using markdown cards or organized layouts.
- **FR-6.4:** The UI shall display clear, distinctive refusal notices when queries are blocked by security controls.
