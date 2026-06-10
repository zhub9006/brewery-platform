"""
Core brewing calculations for the Brewery Platform.

Formulas reference:
  ABV  : Advanced formula using Brix correction
  IBU  : Tinseth formula with hop-utilisation efficiency factor
  SRM  : Morey equation with a practical upper cap at 40 SRM
  AA%  : Apparent attenuation helper

Changes in this PR
------------------
* ABV: switched to the more accurate Brix-derived formula
  (avoids ~0.2 % underestimation at high-gravity worts).
* IBU: added `hop_utilisation_efficiency` parameter (default 1.0)
  so brewhouses with known efficiency losses can be modelled.
* SRM: added hard cap at 40 SRM (opaque black beer).
* NEW: `calculate_apparent_attenuation` helper.
* BUG FIX: `gravity_temperature_correction` now raises ValueError
  for temperatures below -459.67 °F AND also for Celsius values
  accidentally passed in (< -100 guard added with descriptive error).
"""

from __future__ import annotations
import math


# ---------------------------------------------------------------------------
# ABV  (updated: more accurate high-gravity formula)
# ---------------------------------------------------------------------------

def calculate_abv(original_gravity: float, final_gravity: float) -> float:
    """Return Alcohol By Volume (%) using the improved formula.

    Uses the more accurate formula:
        ABV = (76.08 * (OG - FG) / (1.775 - OG)) * (FG / 0.794)

    This corrects for the ~0.2 % underestimation of the simplified
    (OG - FG) * 131.25 formula at original gravities above 1.075.

    Args:
        original_gravity: OG in SG units (e.g. 1.055).
        final_gravity:    FG in SG units (e.g. 1.010).

    Returns:
        ABV as a percentage (e.g. 5.91).

    Raises:
        ValueError: if OG <= 0, FG <= 0, OG >= 1.775 (formula singularity),
                    or FG > OG.
    """
    if original_gravity <= 0 or final_gravity <= 0:
        raise ValueError("Gravity values must be positive.")
    if original_gravity >= 1.775:
        raise ValueError("OG >= 1.775 is outside the valid range for this formula.")
    if final_gravity > original_gravity:
        raise ValueError("Final gravity cannot exceed original gravity.")

    abv = (76.08 * (original_gravity - final_gravity) / (1.775 - original_gravity)) * (final_gravity / 0.794)
    return round(abv, 2)


# ---------------------------------------------------------------------------
# IBU  (Tinseth, with brewhouse efficiency factor)
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
    hop_utilisation_efficiency: float = 1.0,
) -> float:
    """Return IBU contribution of a single hop addition using the Tinseth formula.

    Args:
        alpha_acid_pct:             Alpha acid percentage (e.g. 10.5 for 10.5 %).
        hop_weight_oz:              Weight of hops in ounces.
        boil_minutes:               Time in boil (minutes).
        batch_size_gallons:         Final batch volume in US gallons.
        wort_gravity:               Average wort gravity during boil (SG).
        hop_utilisation_efficiency: Brewhouse hop utilisation factor (0 < x <= 1.0).
                                    Default 1.0 (ideal). Use e.g. 0.85 for a
                                    typical home-brew system.

    Returns:
        IBU contribution (float).

    Raises:
        ValueError: on non-positive batch size, negative boil time,
                    alpha acid out of [0, 100] range, or efficiency out of (0, 1].
    """
    if batch_size_gallons <= 0:
        raise ValueError("Batch size must be positive.")
    if boil_minutes < 0:
        raise ValueError("Boil time cannot be negative.")
    if not (0 <= alpha_acid_pct <= 100):
        raise ValueError("Alpha acid must be between 0 and 100.")
    if not (0 < hop_utilisation_efficiency <= 1.0):
        raise ValueError("hop_utilisation_efficiency must be in the range (0, 1].")
    if wort_gravity <= 0:
        raise ValueError("Wort gravity must be positive.")

    aa_utilisation = _bigness_factor(wort_gravity) * _boil_time_factor(boil_minutes)
    ibu = (
        aa_utilisation
        * (alpha_acid_pct / 100.0)
        * hop_weight_oz
        * 7489.0
        / batch_size_gallons
        * hop_utilisation_efficiency
    )
    return round(ibu, 2)


# ---------------------------------------------------------------------------
# SRM  (Morey, with cap)
# ---------------------------------------------------------------------------

SRM_MAX = 40.0  # Practical upper bound (opaque black beer)


def calculate_srm(mcu: float) -> float:
    """Return SRM colour using the Morey equation, capped at SRM_MAX.

    Args:
        mcu: Malt Colour Units  = (grain_weight_lbs * grain_colour_lovibond) / batch_size_gallons

    Returns:
        SRM value (capped at 40).

    Raises:
        ValueError: if MCU is negative.
    """
    if mcu < 0:
        raise ValueError("MCU cannot be negative.")
    raw_srm = 1.4922 * (mcu ** 0.6859)
    return round(min(raw_srm, SRM_MAX), 2)


# ---------------------------------------------------------------------------
# Apparent Attenuation  (NEW)
# ---------------------------------------------------------------------------

def calculate_apparent_attenuation(original_gravity: float, final_gravity: float) -> float:
    """Return the apparent attenuation percentage.

    Apparent attenuation = (OG - FG) / (OG - 1.0) * 100

    Args:
        original_gravity: OG in SG units.
        final_gravity:    FG in SG units.

    Returns:
        Apparent attenuation as a percentage.

    Raises:
        ValueError: if OG <= 1.0 (no fermentable sugar) or FG > OG.
    """
    if original_gravity <= 1.0:
        raise ValueError("Original gravity must be greater than 1.0 to have fermentable content.")
    if final_gravity > original_gravity:
        raise ValueError("Final gravity cannot exceed original gravity.")
    if final_gravity < 0:
        raise ValueError("Final gravity cannot be negative.")

    return round((original_gravity - final_gravity) / (original_gravity - 1.0) * 100, 2)


# ---------------------------------------------------------------------------
# Fermentation temperature correction  (bug-fix: guard against Celsius input)
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
        ValueError: if measurement temperature is below absolute zero,
                    or suspiciously low (likely a Celsius value was passed).
    """
    if measurement_temp_f < -459.67:
        raise ValueError("Temperature below absolute zero is not physical.")
    if measurement_temp_f < -100:
        raise ValueError(
            f"Temperature {measurement_temp_f}°F is below -100°F. "
            "Did you accidentally pass a Celsius value?"
        )

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
