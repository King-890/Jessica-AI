from typing import List, Tuple

from data.db import (
    log_command,
    get_recent_commands,
    append_conversation,
    get_recent_conversation,
    bump_pattern,
    get_top_patterns,
)


class MemoryStore:
    """Persistent memory store backed by SQLite.

    Keeps recent commands, conversation history, and simple pattern counts.
    """

    def log_command(self, text: str) -> None:
        log_command(text)

    def recent_commands(self, limit: int = 10) -> List[str]:
        return get_recent_commands(limit)

    def add_message(self, role: str, content: str) -> None:
        append_conversation(role, content)

    def recent_history(self, limit: int = 20) -> List[Tuple[str, str]]:
        return get_recent_conversation(limit)

    def bump_pattern(self, pattern: str) -> None:
        bump_pattern(pattern)

    def top_patterns(self, limit: int = 10) -> List[Tuple[str, int]]:
        return get_top_patterns(limit)