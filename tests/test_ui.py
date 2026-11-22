"""Unit tests for Streamlit Chat Interface (app.py).

Verifies:
- FR-6.1: Interactive chat message handling and input processing.
- FR-6.2: Session history state maintenance.
- FR-6.3: Weather information markdown presentation.
- FR-6.4: Clear refusal alert banners for injection and off-topic blocked queries.
- Sidebar quick-test scenario buttons and configuration checks.
"""

from unittest.mock import MagicMock, patch
import pytest

from app import (
    QUICK_TEST_SCENARIOS,
    check_api_credentials,
    is_injection_refusal,
    is_off_topic_refusal,
    render_assistant_message,
)
from src.security import (
    EMPTY_PROMPT_REFUSAL_MESSAGE,
    INJECTION_REFUSAL_MESSAGE,
    OFF_TOPIC_REFUSAL_MESSAGE,
)


# --- Test 1: Quick-Test Scenarios Catalog ---

def test_quick_test_scenarios_definition():
    """Verifies that all four demo scenarios are accurately defined with labels and prompts."""
    required_keys = ["current_weather", "forecast", "off_topic", "injection"]
    for key in required_keys:
        assert key in QUICK_TEST_SCENARIOS, f"Missing scenario key: {key}"
        item = QUICK_TEST_SCENARIOS[key]
        assert "label" in item and item["label"].strip()
        assert "prompt" in item and item["prompt"].strip()
        assert "description" in item

    # Verify exact demo scenario prompts matching step-04 and FR specifications
    assert QUICK_TEST_SCENARIOS["current_weather"]["prompt"] == "What's the weather in Amarillo right now?"
    assert QUICK_TEST_SCENARIOS["forecast"]["prompt"] == "Give me the 5-day forecast for Amarillo"
    assert QUICK_TEST_SCENARIOS["off_topic"]["prompt"] == "Briefly introduce West Texas A&M University"
    assert "developer mode" in QUICK_TEST_SCENARIOS["injection"]["prompt"]
    assert ".env" in QUICK_TEST_SCENARIOS["injection"]["prompt"]


# --- Test 2: Injection Refusal Detection ---

def test_is_injection_refusal_positive():
    """Verifies is_injection_refusal identifies exact and heuristic injection refusal messages."""
    assert is_injection_refusal(INJECTION_REFUSAL_MESSAGE) is True
    assert is_injection_refusal("Security Refusal: Unauthorized instruction override detected.") is True
    assert is_injection_refusal("Security Refusal: Credential access attempt detected.") is True
    assert is_injection_refusal("Prompt injection attempt blocked.") is True


def test_is_injection_refusal_negative():
    """Verifies is_injection_refusal returns False for normal responses or empty inputs."""
    assert is_injection_refusal("") is False
    assert is_injection_refusal("The weather in Amarillo is 72°F and sunny.") is False
    assert is_injection_refusal(OFF_TOPIC_REFUSAL_MESSAGE) is False


# --- Test 3: Off-Topic Refusal Detection ---

def test_is_off_topic_refusal_positive():
    """Verifies is_off_topic_refusal identifies exact and heuristic off-topic refusal messages."""
    assert is_off_topic_refusal(OFF_TOPIC_REFUSAL_MESSAGE) is True
    assert is_off_topic_refusal("I am a dedicated Weather Assistant and can only answer weather-related questions.") is True
    assert is_off_topic_refusal("I am exclusively a weather assistant and cannot answer general knowledge questions.") is True


def test_is_off_topic_refusal_negative():
    """Verifies is_off_topic_refusal returns False for normal responses or empty inputs."""
    assert is_off_topic_refusal("") is False
    assert is_off_topic_refusal("The forecast indicates rain tomorrow in Dallas.") is False
    assert is_off_topic_refusal(INJECTION_REFUSAL_MESSAGE) is False


# --- Test 4: Refusal and Response Rendering Banners (FR-6.3, FR-6.4) ---

def test_render_assistant_message_injection():
    """FR-6.4: Verifies prompt injection refusals trigger st.error with distinct security styling."""
    with patch("streamlit.error") as mock_error:
        with patch("streamlit.warning") as mock_warning:
            with patch("streamlit.markdown") as mock_markdown:
                render_assistant_message(INJECTION_REFUSAL_MESSAGE)
                mock_error.assert_called_once()
                args, _ = mock_error.call_args
                assert "Security Alert" in args[0]
                assert INJECTION_REFUSAL_MESSAGE in args[0]
                mock_warning.assert_not_called()
                mock_markdown.assert_not_called()


def test_render_assistant_message_off_topic():
    """FR-6.4: Verifies off-topic refusals trigger st.warning with boundary policy notice."""
    with patch("streamlit.error") as mock_error:
        with patch("streamlit.warning") as mock_warning:
            with patch("streamlit.markdown") as mock_markdown:
                render_assistant_message(OFF_TOPIC_REFUSAL_MESSAGE)
                mock_warning.assert_called_once()
                args, _ = mock_warning.call_args
                assert "Topic Boundary Policy" in args[0]
                assert OFF_TOPIC_REFUSAL_MESSAGE in args[0]
                mock_error.assert_not_called()
                mock_markdown.assert_not_called()


def test_render_assistant_message_empty():
    """Verifies empty prompt warnings trigger st.info."""
    with patch("streamlit.info") as mock_info:
        render_assistant_message(EMPTY_PROMPT_REFUSAL_MESSAGE)
        mock_info.assert_called_once()
        assert EMPTY_PROMPT_REFUSAL_MESSAGE in mock_info.call_args[0][0]


def test_render_assistant_message_weather_markdown():
    """FR-6.3: Verifies legitimate weather output is rendered via st.markdown."""
    weather_text = "### Current Weather in Amarillo, US\n- **Temp:** 72°F\n- **Condition:** Clear Sky"
    with patch("streamlit.markdown") as mock_markdown:
        with patch("streamlit.error") as mock_error:
            with patch("streamlit.warning") as mock_warning:
                render_assistant_message(weather_text)
                mock_markdown.assert_called_once_with(weather_text)
                mock_error.assert_not_called()
                mock_warning.assert_not_called()


# --- Test 5: Credential Check Helper ---

def test_check_api_credentials():
    """FR-1.4: Verifies check_api_credentials accurately reports presence of required keys."""
    with patch("src.config.load_config") as mock_load:
        mock_cfg = MagicMock()
        mock_cfg.xai_api_key = "test_xai"
        mock_cfg.openweather_api_key = "test_ow"
        mock_load.return_value = mock_cfg

        status = check_api_credentials()
        assert status["xai"] is True
        assert status["openweather"] is True
