"""
brew_calc.py
Core brewing calculations for the Brewery Platform.

Formulas reference:
  ABV  : (OG - FG) * 131.25
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
        original_gravity: OG in SG units (e.g. 1.050).
        final_gravity:    FG in SG units (e.g. 1.010).

    Returns:
        ABV as a percentage (e.g. 5.25).

    Raises:
        ValueError: if OG < FG (impossible fermentation).
    """
    if original_gravity < final_gravity:
        raise ValueError(
            f"OG ({original_gravity}) must be >= FG ({final_gravity})"
        )
    return round((original_gravity - final_gravity) * 131.25, 2)


# ---------------------------------------------------------------------------
# IBU  (Tinseth)
# ---------------------------------------------------------------------------

def _bigness_factor(gravity: float) -> float:
    """Tinseth bigness factor."""
    return 1.65 * (0.000125 ** (gravity - 1))


def _boil_time_factor(boil_minutes: float) -> float:
    """Tinseth boil-time utilisation factor."""
    return (1 - math.exp(-0.04 * boil_minutes)) / 4.15


def calculate_ibu(
    alpha_acid_pct: float,
    hop_weight_grams: float,
    boil_minutes: float,
    wort_volume_litres: float,
    wort_gravity: float,
) -> float:
    """Return bitterness in IBU using the Tinseth formula.

    Args:
        alpha_acid_pct:     Alpha acid percentage of hops (e.g. 6.5 for 6.5%).
        hop_weight_grams:   Weight of hops in grams.
        boil_minutes:       Boil duration in minutes.
        wort_volume_litres: Volume of wort in the kettle (litres).
        wort_gravity:       Average wort gravity during the boil (SG).

    Returns:
        IBU as a float.

    Raises:
        ValueError: for non-positive volume or negative inputs.
    """
    if wort_volume_litres <= 0:
        raise ValueError("Wort volume must be positive.")
    if alpha_acid_pct < 0 or hop_weight_grams < 0 or boil_minutes < 0:
        raise ValueError("Alpha acids, hop weight, and boil time must be >= 0.")

    utilisation = _bigness_factor(wort_gravity) * _boil_time_factor(boil_minutes)
    alpha_acid_units = (alpha_acid_pct / 100) * hop_weight_grams * 1000
    ibu = (alpha_acid_units * utilisation) / wort_volume_litres
    return round(ibu, 2)


# ---------------------------------------------------------------------------
# SRM  (Morey)
# ---------------------------------------------------------------------------

def calculate_srm(mcu: float) -> float:
    """Return beer colour in SRM using the Morey equation.

    Args:
        mcu: Malt Colour Units = (grain_weight_lb * grain_lovibond) / volume_gal.

    Returns:
        SRM colour value.
    """
    if mcu < 0:
        raise ValueError("MCU must be >= 0.")
    return round(1.4922 * (mcu ** 0.6859), 2)


# ---------------------------------------------------------------------------
# Apparent attenuation
# ---------------------------------------------------------------------------

def apparent_attenuation(original_gravity: float, final_gravity: float) -> float:
    """Return apparent attenuation as a fraction (0-1)."""
    if original_gravity <= 1.0:
        raise ValueError("OG must be > 1.000")
    og_points = original_gravity - 1.0
    fg_points = final_gravity - 1.0
    return round((og_points - fg_points) / og_points, 4)


# ---------------------------------------------------------------------------
# Priming sugar
# ---------------------------------------------------------------------------

def priming_sugar_grams(
    batch_litres: float,
    desired_volumes_co2: float,
    current_volumes_co2: float = 0.85,
) -> float:
    """Calculate grams of dextrose needed to carbonate a batch.

    Args:
        batch_litres:          Volume of beer to carbonate.
        desired_volumes_co2:   Target CO₂ volumes.
        current_volumes_co2:   Residual CO₂ already in solution.

    Returns:
        Grams of dextrose required.
    """
    if batch_litres <= 0:
        raise ValueError("Batch size must be positive.")
    co2_needed = desired_volumes_co2 - current_volumes_co2
    return round(batch_litres * co2_needed * 2.0, 2)
