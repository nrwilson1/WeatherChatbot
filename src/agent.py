"""LangChain ChatXAI Agent and Tool-Calling Pipeline for Weather Chatbot.

Implements FR-2 (Current Weather Tool Calling), FR-3 (5-Day Forecast Tool Calling),
FR-4 (Prompt Injection & Jailbreak Defense), and FR-5 (Anti-Hijacking & Off-Topic Prevention):
- Initializes ChatXAI with model="grok-4.7" and validated API key.
- Binds OpenWeather tools: get_current_weather and get_weather_forecast.
- Integrates hardened SYSTEM_PROMPT boundary instructions.
- Provides process_chat(user_message, chat_history) with deterministic pre-screening guardrail.
"""

import os
from typing import Any, Dict, List, Optional, Sequence, Union

from langchain.agents import create_agent
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.tools import BaseTool
from langchain_xai import ChatXAI

from src.config import load_config
from src.security import (
    SYSTEM_PROMPT,
    validate_user_prompt,
    INJECTION_REFUSAL_MESSAGE,
    OFF_TOPIC_REFUSAL_MESSAGE,
    EMPTY_PROMPT_REFUSAL_MESSAGE,
)
from src.weather_tools import get_current_weather, get_weather_forecast

# Standard registered tools for weather and forecast capabilities
WEATHER_TOOLS: List[BaseTool] = [get_current_weather, get_weather_forecast]


def get_xai_api_key(api_key: Optional[str] = None) -> str:
    """Retrieves the xAI API key from explicit parameter, environment, or .env config.

    Args:
        api_key: Optional explicit key string.

    Returns:
        str: Validated xAI API key.

    Raises:
        ValueError: If no xAI API key can be located.
    """
    if api_key and api_key.strip():
        return api_key.strip()

    env_key = os.getenv("XAI_API_KEY", "").strip()
    if env_key:
        return env_key

    try:
        config = load_config()
        if config.xai_api_key:
            return config.xai_api_key.strip()
    except Exception:
        pass

    raise ValueError(
        "Missing required XAI_API_KEY. Please provide it as a parameter, set it in your "
        "environment variables, or configure it in your .env file."
    )


def get_weather_agent(
    api_key: Optional[str] = None,
    tools: Optional[Sequence[BaseTool]] = None,
) -> Any:
    """Initializes ChatXAI(model="grok-4.7"), binds OpenWeather tools, and builds the agent runnable.

    Args:
        api_key: Optional explicit xAI API key. If omitted, loads from config/environment.
        tools: Optional list of tools to bind. Defaults to [get_current_weather, get_weather_forecast].

    Returns:
        An executable LangChain agent runnable configured with grok-4.7, bound tools,
        and the hardened SYSTEM_PROMPT.
    """
    key = get_xai_api_key(api_key)
    selected_tools = list(tools) if tools is not None else list(WEATHER_TOOLS)

    # Initialize ChatXAI with grok-4.7 model
    llm = ChatXAI(
        model="grok-4.7",
        api_key=key,
        xai_api_key=key,
        temperature=0.0,
    )

    # Explicitly bind tools to the LLM
    bound_llm = llm.bind_tools(selected_tools)

    # Construct the tool-calling agent graph with the hardened system prompt persona
    agent = create_agent(
        model=llm,
        tools=selected_tools,
        system_prompt=SYSTEM_PROMPT,
    )

    # Attach references for easy inspection, testing, and UI introspection
    agent.llm = llm
    agent.model = llm
    agent.bound_llm = bound_llm
    agent.tools = selected_tools
    agent.system_prompt = SYSTEM_PROMPT

    return agent


def format_chat_history(chat_history: Optional[Sequence[Any]]) -> List[BaseMessage]:
    """Converts diverse conversation history representations into LangChain BaseMessage objects.

    Supports:
        - LangChain BaseMessage objects (HumanMessage, AIMessage, SystemMessage)
        - Dictionaries with 'role' and 'content' keys (Streamlit session format)
        - (role, content) tuples

    Args:
        chat_history: Sequence of previous turns.

    Returns:
        List of typed BaseMessage objects.
    """
    messages: List[BaseMessage] = []
    if not chat_history:
        return messages

    for turn in chat_history:
        if isinstance(turn, BaseMessage):
            messages.append(turn)
        elif isinstance(turn, dict):
            role = str(turn.get("role", "")).lower().strip()
            content = str(turn.get("content", ""))
            if role in ("user", "human"):
                messages.append(HumanMessage(content=content))
            elif role in ("assistant", "ai"):
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        elif isinstance(turn, (tuple, list)) and len(turn) >= 2:
            role = str(turn[0]).lower().strip()
            content = str(turn[1])
            if role in ("user", "human"):
                messages.append(HumanMessage(content=content))
            elif role in ("assistant", "ai"):
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))

    return messages


def process_chat(
    user_message: str,
    chat_history: Optional[List[Any]] = None,
    agent: Optional[Any] = None,
    **kwargs: Any,
) -> str:
    """Single entrypoint for processing user messages through guardrails and the agent pipeline.

    Defensive Workflow:
    1. Runs the deterministic code-level pre-screening filter (validate_user_prompt).
    2. If malicious injection or off-topic query is detected, immediately returns the refusal
       message without invoking the LLM, preserving paid xAI tokens (FR-4, FR-5).
    3. If valid, prepares conversational history and invokes the LangChain grok-4.7 agent
       with OpenWeather tools, enforcing execution limits (FR-5.4).

    Args:
        user_message: Raw text prompt submitted by the user.
        chat_history: Optional prior conversation turns.
        agent: Optional pre-configured agent runnable (defaults to get_weather_agent()).
        **kwargs: Additional parameters (e.g. supports 'history' alias for chat_history).

    Returns:
        str: Final natural language response from the assistant or security refusal notice.
    """
    # Support 'history' kwarg alias for chat_history
    if chat_history is None and "history" in kwargs:
        chat_history = kwargs["history"]

    # Step 1: Layer 1 Security Guardrail Pre-screening (FR-4 & FR-5)
    is_valid, refusal_message = validate_user_prompt(user_message)
    if not is_valid:
        return refusal_message

    # Step 2: Initialize or resolve the agent instance
    if agent is None:
        agent = get_weather_agent()

    # Step 3: Format history and append current user turn
    messages = format_chat_history(chat_history)
    messages.append(HumanMessage(content=user_message.strip()))

    # Step 4: Execute agent with recursion limits (FR-5.4)
    try:
        if hasattr(agent, "invoke"):
            result = agent.invoke(
                {"messages": messages},
                config={"recursion_limit": 10},
            )
        elif callable(agent):
            result = agent({"messages": messages})
        else:
            raise TypeError("Provided agent instance is neither invokable nor callable.")

        # Extract text response from result
        if isinstance(result, str):
            return result

        if isinstance(result, dict):
            output_messages = result.get("messages", [])
            if output_messages:
                last_msg = output_messages[-1]
                content = getattr(last_msg, "content", str(last_msg))
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    text_parts = [
                        p if isinstance(p, str) else p.get("text", "")
                        for p in content
                    ]
                    return "".join(text_parts)
                return str(content)
            elif "output" in result:
                return str(result["output"])

        return str(result)

    except Exception as e:
        error_msg = str(e)
        if "recursion_limit" in error_msg.lower():
            return "Error: Tool execution exceeded the maximum allowed steps. Request aborted to prevent loops."
        return f"An error occurred while processing your request: {error_msg}"
