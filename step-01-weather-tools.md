# Step 01: Project Setup & OpenWeather Tool Calling

## 1. Session Scope
- **Target FRs:** FR-1 (Environment & Secret Management), FR-2 (Current Weather Tool), FR-3 (5-Day Forecast Tool)
- **Feature Boundaries:**
  - Create `src/config.py` to validate and load `XAI_API_KEY` and `OPENWEATHER_API_KEY` from `.env`.
  - Create `src/weather_tools.py` implementing `get_current_weather` and `get_weather_forecast` as LangChain `@tool` functions.
  - Implement parsing logic to extract temperature, feels-like, humidity, wind speed, description, and daily 5-day forecast summaries.
  - Gracefully handle API errors and invalid city queries.

---

## 2. Prerequisites
- Python virtual environment created and activated.
- Dependencies installed from `requirements.txt`.
- Valid `.env` created containing `XAI_API_KEY` and `OPENWEATHER_API_KEY`.
- Verified `.gitignore` excludes `.env`.

---

## 3. TDD Test Suite
Create `tests/test_weather_tools.py` with the following test cases:
1. `test_config_loads_keys`: Verifies environment variables are loaded or missing keys raise errors.
2. `test_get_current_weather_valid`: Verifies `get_current_weather` returns structured dictionary/string with temperature, feels_like, humidity, wind_speed, and conditions for a known city (e.g. "Amarillo").
3. `test_get_current_weather_invalid_city`: Verifies invalid city (e.g. "InvalidCityXYZ999") returns a graceful error message without crashing.
4. `test_get_weather_forecast_valid`: Verifies `get_weather_forecast` aggregates 5-day summary containing day-by-day temperature highs/lows and conditions.

---

## 4. Implementation Deliverables
- `src/config.py`:
  - `load_config()`: Validates that `OPENWEATHER_API_KEY` and `XAI_API_KEY` are present.
- `src/weather_tools.py`:
  - `@tool def get_current_weather(city: str) -> str`:
    - Endpoint: `https://api.openweathermap.org/data/2.5/weather`
    - Parameters: `q={city}`, `appid={OPENWEATHER_API_KEY}`, `units=imperial`
    - Formats output: Temperature (°F), feels like, humidity (%), wind speed (mph), description.
  - `@tool def get_weather_forecast(city: str) -> str`:
    - Endpoint: `https://api.openweathermap.org/data/2.5/forecast`
    - Parameters: `q={city}`, `appid={OPENWEATHER_API_KEY}`, `units=imperial`
    - Groups 3-hour forecast timestamps by date and summarizes daily high, low, and condition for 5 days.

---

## 5. Definition of Done
- Run test suite:
  ```powershell
  pytest tests/test_weather_tools.py -v
  ```
- All tests pass with exit code `0`.
- Git commit:
  ```powershell
  git add src/ tests/
  git commit -m "feat(tools): implement openweather current weather and 5-day forecast tools"
  ```
