"""Known promotion-proposal pattern definitions."""

DEFAULT_PATTERNS = {
    "system.async_command_context_missing": {
        "category": "system",
        "description": "Async command output lost because context was not preserved.",
    },
    "system.heartbeat_repeated_check": {
        "category": "system",
        "description": "Heartbeat repeated a check without producing useful progress.",
    },
    "instruction.session_isolation": {
        "category": "instruction",
        "description": "Work crossed session boundaries without explicit user intent.",
    },
    "memory.duplicate_context": {
        "category": "memory",
        "description": "Repeated context caused noisy or stale reasoning.",
    },
    "error.unhandled_exception_async": {
        "category": "error",
        "description": "Async exception was not handled or surfaced usefully.",
    },
}


def is_known_pattern(pattern_type: str) -> bool:
    return pattern_type.lower() in DEFAULT_PATTERNS
