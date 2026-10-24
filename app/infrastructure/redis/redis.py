def text(value: bytes | str) -> str:
    """A Redis reply as text (the client decodes replies, but is typed for both)."""
    return value.decode() if isinstance(value, bytes) else value
