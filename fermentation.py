"""
fermentation.py
Fermentation temperature and yeast activity models.
"""

from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# Temperature helpers
# ---------------------------------------------------------------------------

def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return round(celsius * 9 / 5 + 32, 2)


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return round((fahrenheit - 32) * 5 / 9, 2)


# ---------------------------------------------------------------------------
# Yeast activity
# ---------------------------------------------------------------------------

YEAST_OPTIMAL_TEMP_C = 20.0   # typical ale yeast optimal
YEAST_MIN_TEMP_C = 4.0
YEAST_MAX_TEMP_C = 40.0


def yeast_activity_factor(temp_celsius: float) -> float:
    """Return a 0-1 activity factor for yeast at a given temperature.

    Uses a bell-curve approximation centred on the optimal temperature.
    Returns 0.0 outside viable range.

    Args:
        temp_celsius: Fermentation temperature in °C.

    Returns:
        Activity factor between 0.0 and 1.0.
    """
    if temp_celsius < YEAST_MIN_TEMP_C or temp_celsius > YEAST_MAX_TEMP_C:
        return 0.0
    sigma = 8.0
    factor = math.exp(-0.5 * ((temp_celsius - YEAST_OPTIMAL_TEMP_C) / sigma) ** 2)
    return round(factor, 4)


# ---------------------------------------------------------------------------
# Estimated days to fermentation completion
# ---------------------------------------------------------------------------

def estimated_fermentation_days(
    og_points: float,
    temp_celsius: float,
    yeast_health: float = 1.0,
) -> float:
    """Estimate days to reach terminal gravity.

    Args:
        og_points:    OG expressed as points above 1.000 (e.g. 50 for 1.050).
        temp_celsius: Fermentation temperature in °C.
        yeast_health: Multiplier 0-1 representing pitch health.

    Returns:
        Estimated days as a float.

    Raises:
        ValueError: for negative OG points, negative temperature, or invalid health.
    """
    if og_points < 0:
        raise ValueError("OG points must be >= 0.")
    if temp_celsius < 0:
        raise ValueError("Temperature must be >= 0°C for fermentation modelling.")
    if not 0 < yeast_health <= 1.0:
        raise ValueError("yeast_health must be in (0, 1].")

    activity = yeast_activity_factor(temp_celsius)
    if activity == 0.0:
        return float('inf')   # yeast inactive

    base_days = og_points / 10.0
    return round(base_days / (activity * yeast_health), 2)
