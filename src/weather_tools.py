"""OpenWeather LangChain Tools for Current Weather and 5-Day Forecasts.

Implements FR-2 (Current Weather Tool) and FR-3 (5-Day Forecast Tool).
"""

from collections import Counter, defaultdict
from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
import requests
from langchain_core.tools import tool, BaseTool, StructuredTool

# Enable direct callable invocation on StructuredTool and BaseTool for flexible testing and usage
def _tool_call(self: Any, *args: Any, **kwargs: Any) -> Any:
    if kwargs:
        return self.invoke(kwargs)
    if len(args) == 1 and isinstance(args[0], dict):
        return self.invoke(args[0])
    if len(args) == 1:
        return self.invoke(args[0])
    return self.invoke({})

BaseTool.__call__ = _tool_call
StructuredTool.__call__ = _tool_call

OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


def get_openweather_api_key() -> str:
    """Retrieve the OpenWeather API key from environment or config."""
    key = os.getenv("OPENWEATHER_API_KEY", "").strip()
    if not key:
        from src.config import load_config
        config = load_config()
        key = config.openweather_api_key
    return key


@tool
def get_current_weather(city: str) -> str:
    """Fetch current real-time weather conditions for a specified city or location name.

    Args:
        city: The name of the city or location (e.g., 'Amarillo', 'London', 'Seattle, US').

    Returns:
        A formatted summary of current weather conditions including temperature,
        feels-like, humidity, wind speed, and weather description.
    """
    if not city or not city.strip():
        return "Error: Please provide a valid city name."

    city = city.strip()
    api_key = get_openweather_api_key()
    url = f"{OPENWEATHER_BASE_URL}/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "imperial"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 404:
            return f"Error: City '{city}' not found. Please verify the city name and try again."
        
        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            msg = error_data.get("message", f"HTTP {response.status_code}")
            return f"Error fetching current weather for '{city}': {msg}."

        data = response.json()
        city_name = data.get("name", city)
        country = data.get("sys", {}).get("country", "")
        location_label = f"{city_name}, {country}" if country else city_name

        main = data.get("main", {})
        temp = main.get("temp", "N/A")
        feels_like = main.get("feels_like", "N/A")
        humidity = main.get("humidity", "N/A")
        wind_speed = data.get("wind", {}).get("speed", "N/A")

        weather_list = data.get("weather", [])
        description = weather_list[0].get("description", "N/A") if weather_list else "N/A"

        return (
            f"Current Weather for {location_label}:\n"
            f"- Temperature: {temp}°F\n"
            f"- Feels Like: {feels_like}°F\n"
            f"- Conditions: {description}\n"
            f"- Humidity: {humidity}%\n"
            f"- Wind Speed: {wind_speed} mph"
        )

    except requests.RequestException as e:
        return f"Network error while fetching weather data for '{city}': {str(e)}"
    except Exception as e:
        return f"Unexpected error processing weather data for '{city}': {str(e)}"


@tool
def get_weather_forecast(city: str) -> str:
    """Fetch the 5-day weather forecast aggregated by day for a specified city.

    Args:
        city: The name of the city or location (e.g., 'Amarillo', 'London', 'Tokyo').

    Returns:
        A structured daily breakdown for the next 5 days including temperature highs,
        lows, and dominant weather conditions.
    """
    if not city or not city.strip():
        return "Error: Please provide a valid city name."

    city = city.strip()
    api_key = get_openweather_api_key()
    url = f"{OPENWEATHER_BASE_URL}/forecast"
    params = {
        "q": city,
        "appid": api_key,
        "units": "imperial"
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 404:
            return f"Error: City '{city}' not found. Please verify the city name and try again."

        if response.status_code != 200:
            error_data = response.json() if response.text else {}
            msg = error_data.get("message", f"HTTP {response.status_code}")
            return f"Error fetching forecast for '{city}': {msg}."

        data = response.json()
        city_info = data.get("city", {})
        city_name = city_info.get("name", city)
        country = city_info.get("country", "")
        location_label = f"{city_name}, {country}" if country else city_name

        forecast_list = data.get("list", [])
        if not forecast_list:
            return f"No forecast data available for '{city}'."

        # Group 3-hour forecast timestamps by date (YYYY-MM-DD)
        daily_data: Dict[str, Dict[str, List[Any]]] = defaultdict(lambda: {
            "temps": [],
            "conditions": [],
            "humidities": []
        })

        for entry in forecast_list:
            dt_txt = entry.get("dt_txt")
            if dt_txt:
                date_str = dt_txt.split(" ")[0]
            else:
                dt_val = entry.get("dt", 0)
                date_str = datetime.fromtimestamp(dt_val, tz=timezone.utc).strftime("%Y-%m-%d")

            main = entry.get("main", {})
            temp = main.get("temp")
            temp_min = main.get("temp_min", temp)
            temp_max = main.get("temp_max", temp)
            humidity = main.get("humidity")

            if temp is not None:
                daily_data[date_str]["temps"].extend([t for t in [temp, temp_min, temp_max] if t is not None])
            if humidity is not None:
                daily_data[date_str]["humidities"].append(humidity)

            weather = entry.get("weather", [])
            if weather and "description" in weather[0]:
                daily_data[date_str]["conditions"].append(weather[0]["description"])

        # Format up to 5 days
        forecast_lines = [f"5-Day Weather Forecast for {location_label}:"]
        dates = sorted(daily_data.keys())[:5]

        for d in dates:
            day_info = daily_data[d]
            temps = day_info["temps"]
            high = max(temps) if temps else "N/A"
            low = min(temps) if temps else "N/A"

            # Dominant condition (most frequent condition of the day)
            conditions = day_info["conditions"]
            if conditions:
                dominant_condition = Counter(conditions).most_common(1)[0][0]
            else:
                dominant_condition = "N/A"

            humidities = day_info["humidities"]
            avg_humidity = round(sum(humidities) / len(humidities)) if humidities else "N/A"

            high_str = f"{high:.1f}°F" if isinstance(high, (int, float)) else str(high)
            low_str = f"{low:.1f}°F" if isinstance(low, (int, float)) else str(low)
            humidity_str = f"{avg_humidity}%" if avg_humidity != "N/A" else "N/A"

            forecast_lines.append(
                f"- {d}: High {high_str}, Low {low_str} | Conditions: {dominant_condition} (Humidity: {humidity_str})"
            )

        return "\n".join(forecast_lines)

    except requests.RequestException as e:
        return f"Network error while fetching forecast data for '{city}': {str(e)}"
    except Exception as e:
        return f"Unexpected error processing forecast data for '{city}': {str(e)}"
