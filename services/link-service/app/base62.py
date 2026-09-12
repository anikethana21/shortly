"""Base62 encoding/decoding for short code generation."""

CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(CHARSET)  # 62


def encode(num: int) -> str:
    """Encode a positive integer to a base62 string."""
    if num == 0:
        return CHARSET[0]
    digits = []
    while num:
        digits.append(CHARSET[num % BASE])
        num //= BASE
    return "".join(reversed(digits))


def decode(s: str) -> int:
    """Decode a base62 string back to an integer."""
    num = 0
    for char in s:
        num = num * BASE + CHARSET.index(char)
    return num
