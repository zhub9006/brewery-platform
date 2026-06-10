"""
Core brewing calculations for the Brewery Platform.

Formulas reference:
  ABV  : Standard formula  (OG - FG) * 131.25
  IBU  : Tinseth formula
  SRM  : Morey equation
"""

from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# ABV
# ---------------------------------------------------------------------------

def calculate_abv(original_gravity: float, final_gravity: float) -> float:
    """Return Alcohol By Volume (%) using the simplified formula.

    Args:
        original_gravity: OG in SG units (e.g. 1.055).
        final_gravity:    FG in SG units (e.g. 1.010).

    Returns:
        ABV as a percentage (e.g. 5.91).

    Raises:
        ValueError: if OG <= 0 or FG <= 0.
    """
    if original_gravity <= 0 or final_gravity <= 0:
        raise ValueError("Gravity values must be positive.")
    return (original_gravity - final_gravity) * 131.25


# ---------------------------------------------------------------------------
# IBU  (Tinseth)
# ---------------------------------------------------------------------------

def _bigness_factor(og: float) -> float:
    """Tinseth bigness factor."""
    return 1.65 * (0.000125 ** (og - 1.0))


def _boil_time_factor(boil_minutes: float) -> float:
    """Tinseth boil-time factor."""
    return (1.0 - math.exp(-0.04 * boil_minutes)) / 4.15


def calculate_ibu(
    alpha_acid_pct: float,
    hop_weight_oz: float,
    boil_minutes: float,
    batch_size_gallons: float,
    wort_gravity: float,
) -> float:
    """Return IBU contribution of a single hop addition using the Tinseth formula.

    Args:
        alpha_acid_pct:     Alpha acid percentage (e.g. 10.5 for 10.5 %).
        hop_weight_oz:      Weight of hops in ounces.
        boil_minutes:       Time in boil (minutes).
        batch_size_gallons: Final batch volume in US gallons.
        wort_gravity:       Average wort gravity during boil (SG).

    Returns:
        IBU contribution (float).

    Raises:
        ValueError: on non-positive batch size, negative boil time, or
                    alpha acid out of [0, 100] range.
    """
    if batch_size_gallons <= 0:
        raise ValueError("Batch size must be positive.")
    if boil_minutes < 0:
        raise ValueError("Boil time cannot be negative.")
    if not (0 <= alpha_acid_pct <= 100):
        raise ValueError("Alpha acid must be between 0 and 100.")

    aa_utilisation = _bigness_factor(wort_gravity) * _boil_time_factor(boil_minutes)
    ibu = (aa_utilisation * (alpha_acid_pct / 100.0) * hop_weight_oz * 7489.0) / batch_size_gallons
    return round(ibu, 2)


# ---------------------------------------------------------------------------
# SRM  (Morey)
# ---------------------------------------------------------------------------

def calculate_srm(mcu: float) -> float:
    """Return SRM colour using the Morey equation.

    Args:
        mcu: Malt Colour Units  = (grain_weight_lbs * grain_colour_lovibond) / batch_size_gallons

    Returns:
        SRM value.

    Raises:
        ValueError: if MCU is negative.
    """
    if mcu < 0:
        raise ValueError("MCU cannot be negative.")
    return round(1.4922 * (mcu ** 0.6859), 2)


# ---------------------------------------------------------------------------
# Fermentation temperature correction
# ---------------------------------------------------------------------------

def gravity_temperature_correction(
    measured_gravity: float,
    measurement_temp_f: float,
    calibration_temp_f: float = 60.0,
) -> float:
    """Correct a hydrometer reading for temperature.

    Uses the standard polynomial correction formula.

    Args:
        measured_gravity:   Raw hydrometer reading.
        measurement_temp_f: Temperature at measurement (°F).
        calibration_temp_f: Hydrometer calibration temperature (default 60 °F).

    Returns:
        Corrected specific gravity.

    Raises:
        ValueError: if measurement temperature is below absolute zero equivalent.
    """
    if measurement_temp_f < -459.67:
        raise ValueError("Temperature below absolute zero is not physical.")

    correction = (
        1.00130346
        - 1.34722124e-4 * measurement_temp_f
        + 2.04052596e-6 * measurement_temp_f ** 2
        - 2.32820948e-9 * measurement_temp_f ** 3
    )
    calibration_correction = (
        1.00130346
        - 1.34722124e-4 * calibration_temp_f
        + 2.04052596e-6 * calibration_temp_f ** 2
        - 2.32820948e-9 * calibration_temp_f ** 3
    )
    return round(measured_gravity * (correction / calibration_correction), 5)
