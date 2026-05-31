"""Late-bound access to the separately owned agent service package."""

from importlib import import_module
from typing import Any


class AgentServiceUnavailable(RuntimeError):
    """Raised when the separately supplied agent service cannot be called."""


def _agent_function(name: str):
    try:
        module = import_module("app.services.agent")
    except ImportError as exc:
        raise AgentServiceUnavailable(
            "Agent service package app.services.agent is not installed"
        ) from exc

    function = getattr(module, name, None)
    if not callable(function):
        raise AgentServiceUnavailable(f"Agent service function {name}() is not available")
    return function


async def invoke(name: str, **kwargs: Any) -> Any:
    return await _agent_function(name)(**kwargs)
