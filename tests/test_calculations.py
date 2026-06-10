"""
Baseline tests for brewery/calculations.py
"""
import pytest
from brewery.calculations import (
    calculate_abv,
    calculate_ibu,
    calculate_srm,
    gravity_temperature_correction,
)


class TestABV:
    def test_standard_ale(self):
        assert round(calculate_abv(1.055, 1.010), 2) == 5.91

    def test_zero_attenuation(self):
        assert calculate_abv(1.050, 1.050) == 0.0

    def test_invalid_og(self):
        with pytest.raises(ValueError):
            calculate_abv(0, 1.010)


class TestIBU:
    def test_typical_hop_addition(self):
        ibu = calculate_ibu(10.0, 1.0, 60.0, 5.0, 1.055)
        assert ibu > 0

    def test_zero_boil_time(self):
        ibu = calculate_ibu(10.0, 1.0, 0.0, 5.0, 1.055)
        assert ibu == 0.0

    def test_invalid_batch_size(self):
        with pytest.raises(ValueError):
            calculate_ibu(10.0, 1.0, 60.0, 0.0, 1.055)
