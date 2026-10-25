"""Validation utilities for domain models and input sanitation."""
from typing import Any, List, Optional


class ValidationError(Exception):
    """Raised when domain validation fails."""
    pass


def validate_id(entity_id: str, field_name: str = "ID") -> str:
    """Validate entity identifier string."""
    if not isinstance(entity_id, str) or not entity_id.strip():
        raise ValidationError(f"{field_name} must be a non-empty string.")
    return entity_id.strip()


def validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
    """Validate latitude and longitude values."""
    if not (-90.0 <= lat <= 90.0):
        raise ValidationError(f"Latitude must be between -90 and 90, got {lat}.")
    if not (-180.0 <= lon <= 180.0):
        raise ValidationError(f"Longitude must be between -180 and 180, got {lon}.")
    return float(lat), float(lon)


def validate_non_negative(value: float, field_name: str = "Value") -> float:
    """Ensure value is non-negative."""
    if value < 0:
        raise ValidationError(f"{field_name} must be non-negative, got {value}.")
    return float(value)
