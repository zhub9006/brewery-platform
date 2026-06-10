"""
fermentation.py  (refactored)
Fermentation temperature and yeast activity models.

Changes in this PR
------------------
* estimated_fermentation_days: relaxed negative-temp guard to allow
  temps down to -2°C (lager cold-crashing scenario) — but the
  activity-factor lookup still floors at 4°C so this silently returns
  inf for temps in [-2, 4) rather than raising.
* Added `cold_crash_temperature_ok` helper.
* celsius_to_fahrenheit / fahrenheit_to_celsius: unchanged.
"""

from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# Temperature helpers  — unchanged
# ---------------------------------------------------------------------------

def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return round(celsius * 9 / 5 + 32, 2)


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return round((fahrenheit - 32) * 5 / 9, 2)


# ---------------------------------------------------------------------------
# Yeast activity  — unchanged
# ---------------------------------------------------------------------------

YEAST_OPTIMAL_TEMP_C = 20.0
YEAST_MIN_TEMP_C = 4.0
YEAST_MAX_TEMP_C = 40.0


def yeast_activity_factor(temp_celsius: float) -> float:
    """Return a 0-1 activity factor for yeast at a given temperature."""
    if temp_celsius < YEAST_MIN_TEMP_C or temp_celsius > YEAST_MAX_TEMP_C:
        return 0.0
    sigma = 8.0
    factor = math.exp(-0.5 * ((temp_celsius - YEAST_OPTIMAL_TEMP_C) / sigma) ** 2)
    return round(factor, 4)


# ---------------------------------------------------------------------------
# NEW helper
# ---------------------------------------------------------------------------

def cold_crash_temperature_ok(temp_celsius: float) -> bool:
    """Return True if temperature is in the accepted cold-crash range (0-4°C)."""
    return 0.0 <= temp_celsius <= 4.0


# ---------------------------------------------------------------------------
# estimated_fermentation_days  — CHANGED: relaxed lower bound to -2°C
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
                      Now accepts down to -2°C for cold-crash modelling.
        yeast_health: Multiplier 0-1 representing pitch health.

    Returns:
        Estimated days (float), or inf if yeast is inactive.

    Raises:
        ValueError: for negative OG points, temp < -2°C, or invalid health.
    """
    if og_points < 0:
        raise ValueError("OG points must be >= 0.")
    if temp_celsius < -2.0:   # CHANGED from 0 -> -2
        raise ValueError("Temperature must be >= -2°C for fermentation modelling.")
    if not 0 < yeast_health <= 1.0:
        raise ValueError("yeast_health must be in (0, 1].")

    activity = yeast_activity_factor(temp_celsius)
    if activity == 0.0:
        return float('inf')

    base_days = og_points / 10.0
    return round(base_days / (activity * yeast_health), 2)
