import os
from unittest.mock import patch, MagicMock
import pytest
import requests

from src.config import load_config, Config
from src.weather_tools import get_current_weather, get_weather_forecast


# --- Mock Data Fixtures ---

MOCK_CURRENT_WEATHER_AMARILLO = {
    "coord": {"lon": -101.8313, "lat": 35.222},
    "weather": [
        {
            "id": 800,
            "main": "Clear",
            "description": "clear sky",
            "icon": "01d"
        }
    ],
    "base": "stations",
    "main": {
        "temp": 72.4,
        "feels_like": 70.8,
        "temp_min": 68.0,
        "temp_max": 75.0,
        "pressure": 1015,
        "humidity": 35
    },
    "visibility": 10000,
    "wind": {
        "speed": 12.5,
        "deg": 180
    },
    "clouds": {"all": 1},
    "dt": 1661870000,
    "sys": {
        "type": 1,
        "id": 1234,
        "country": "US",
        "sunrise": 1661860000,
        "sunset": 1661908000
    },
    "timezone": -18000,
    "id": 5516233,
    "name": "Amarillo",
    "cod": 200
}

MOCK_FORECAST_AMARILLO = {
    "cod": "200",
    "message": 0,
    "cnt": 40,
    "city": {
        "id": 5516233,
        "name": "Amarillo",
        "coord": {"lat": 35.222, "lon": -101.8313},
        "country": "US",
        "population": 199233,
        "timezone": -18000,
        "sunrise": 1661860000,
        "sunset": 1661908000
    },
    "list": [
        # Day 1: 2026-11-22
        {
            "dt": 1795352400,
            "dt_txt": "2026-11-22 12:00:00",
            "main": {"temp": 65.0, "temp_min": 60.0, "temp_max": 65.0, "humidity": 40},
            "weather": [{"main": "Clear", "description": "clear sky"}]
        },
        {
            "dt": 1795363200,
            "dt_txt": "2026-11-22 15:00:00",
            "main": {"temp": 70.0, "temp_min": 65.0, "temp_max": 70.0, "humidity": 35},
            "weather": [{"main": "Clear", "description": "clear sky"}]
        },
        # Day 2: 2026-11-23
        {
            "dt": 1795438800,
            "dt_txt": "2026-11-23 12:00:00",
            "main": {"temp": 58.0, "temp_min": 50.0, "temp_max": 58.0, "humidity": 55},
            "weather": [{"main": "Clouds", "description": "scattered clouds"}]
        },
        {
            "dt": 1795449600,
            "dt_txt": "2026-11-23 15:00:00",
            "main": {"temp": 62.0, "temp_min": 55.0, "temp_max": 62.0, "humidity": 50},
            "weather": [{"main": "Clouds", "description": "scattered clouds"}]
        },
        # Day 3: 2026-11-24
        {
            "dt": 1795525200,
            "dt_txt": "2026-11-24 12:00:00",
            "main": {"temp": 50.0, "temp_min": 45.0, "temp_max": 50.0, "humidity": 70},
            "weather": [{"main": "Rain", "description": "light rain"}]
        },
        # Day 4: 2026-11-25
        {
            "dt": 1795611600,
            "dt_txt": "2026-11-25 12:00:00",
            "main": {"temp": 55.0, "temp_min": 48.0, "temp_max": 55.0, "humidity": 60},
            "weather": [{"main": "Clouds", "description": "broken clouds"}]
        },
        # Day 5: 2026-11-26
        {
            "dt": 1795698000,
            "dt_txt": "2026-11-26 12:00:00",
            "main": {"temp": 68.0, "temp_min": 52.0, "temp_max": 68.0, "humidity": 30},
            "weather": [{"main": "Clear", "description": "sunny"}]
        }
    ]
}


# --- Config Tests (FR-1) ---

def test_config_loads_keys():
    """FR-1.1 & FR-1.4: Verify configuration correctly loads API keys from environment."""
    with patch("src.config.load_dotenv"):
        with patch.dict(os.environ, {"XAI_API_KEY": "test_xai_key_123", "OPENWEATHER_API_KEY": "test_ow_key_456"}, clear=True):
            config = load_config()
            assert config.xai_api_key == "test_xai_key_123"
            assert config.openweather_api_key == "test_ow_key_456"
            assert config["XAI_API_KEY"] == "test_xai_key_123"
            assert config["OPENWEATHER_API_KEY"] == "test_ow_key_456"


def test_config_missing_keys_raises_error():
    """FR-1.4: Verify missing keys raise a descriptive ValueError."""
    with patch("src.config.load_dotenv"):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as excinfo:
                load_config()
            assert "Missing required environment variable" in str(excinfo.value)
            assert "XAI_API_KEY" in str(excinfo.value)
            assert "OPENWEATHER_API_KEY" in str(excinfo.value)


def test_config_missing_one_key_raises_error():
    """FR-1.4: Verify missing one key raises ValueError mentioning the specific key."""
    with patch("src.config.load_dotenv"):
        with patch.dict(os.environ, {"XAI_API_KEY": "valid_key"}, clear=True):
            with pytest.raises(ValueError) as excinfo:
                load_config()
            assert "OPENWEATHER_API_KEY" in str(excinfo.value)


# --- Current Weather Tool Tests (FR-2) ---

@patch("src.weather_tools.get_openweather_api_key", return_value="dummy_key")
@patch("requests.get")
def test_get_current_weather_valid(mock_get, mock_key):
    """FR-2.1 - FR-2.3: Verify get_current_weather returns structured details for Amarillo."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_CURRENT_WEATHER_AMARILLO
    mock_get.return_value = mock_response

    # Test via LangChain tool invoke and direct call
    result = get_current_weather.invoke({"city": "Amarillo"})
    direct_result = get_current_weather("Amarillo")
    
    assert "Amarillo" in result
    assert "72.4" in result
    assert "70.8" in result
    assert "35%" in result
    assert "12.5" in result
    assert "clear sky" in result
    assert direct_result == result

    # Verify query parameters
    assert mock_get.call_count == 2
    args, kwargs = mock_get.call_args
    assert "https://api.openweathermap.org/data/2.5/weather" in args[0]
    assert kwargs["params"]["q"] == "Amarillo"
    assert kwargs["params"]["units"] == "imperial"
    assert kwargs["params"]["appid"] == "dummy_key"


@patch("src.weather_tools.get_openweather_api_key", return_value="dummy_key")
@patch("requests.get")
def test_get_current_weather_invalid_city(mock_get, mock_key):
    """FR-2.4: Verify invalid city returns graceful error message without crashing."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"cod": "404", "message": "city not found"}
    mock_get.return_value = mock_response

    result = get_current_weather.invoke({"city": "InvalidCityXYZ999"})

    assert isinstance(result, str)
    assert "not found" in result.lower() or "error" in result.lower()
    assert "InvalidCityXYZ999" in result


@patch("src.weather_tools.get_openweather_api_key", return_value="dummy_key")
@patch("requests.get")
def test_get_current_weather_network_error(mock_get, mock_key):
    """FR-2.4: Verify network failure returns graceful error message."""
    mock_get.side_effect = requests.RequestException("Connection timed out")

    result = get_current_weather.invoke({"city": "Amarillo"})

    assert isinstance(result, str)
    assert "error" in result.lower()
    assert "connection timed out" in result.lower() or "failed" in result.lower()


# --- 5-Day Forecast Tool Tests (FR-3) ---

@patch("src.weather_tools.get_openweather_api_key", return_value="dummy_key")
@patch("requests.get")
def test_get_weather_forecast_valid(mock_get, mock_key):
    """FR-3.1 - FR-3.4: Verify get_weather_forecast returns 5-day daily high/low summaries."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_FORECAST_AMARILLO
    mock_get.return_value = mock_response

    result = get_weather_forecast.invoke({"city": "Amarillo"})
    direct_result = get_weather_forecast("Amarillo")

    assert "Amarillo" in result
    assert "5-day" in result.lower() or "forecast" in result.lower()
    assert direct_result == result
    # Should include day summaries
    assert "2026-11-22" in result
    assert "2026-11-23" in result
    assert "2026-11-24" in result
    assert "2026-11-25" in result
    assert "2026-11-26" in result

    # Check high and low temperatures for Day 1 (high 70.0, low 60.0)
    assert "70" in result
    assert "60" in result
    assert "clear sky" in result

    # Check request parameters
    assert mock_get.call_count == 2
    args, kwargs = mock_get.call_args
    assert "https://api.openweathermap.org/data/2.5/forecast" in args[0]
    assert kwargs["params"]["q"] == "Amarillo"
    assert kwargs["params"]["units"] == "imperial"
    assert kwargs["params"]["appid"] == "dummy_key"


@patch("src.weather_tools.get_openweather_api_key", return_value="dummy_key")
@patch("requests.get")
def test_get_weather_forecast_invalid_city(mock_get, mock_key):
    """FR-3.4 & FR-2.4: Verify invalid city forecast returns graceful error message."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"cod": "404", "message": "city not found"}
    mock_get.return_value = mock_response

    result = get_weather_forecast.invoke({"city": "InvalidCityXYZ999"})

    assert isinstance(result, str)
    assert "not found" in result.lower() or "error" in result.lower()
    assert "InvalidCityXYZ999" in result
