from uuid import UUID


def is_valid_uuid(value: str) -> bool:
    try:
        UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
