"""
Baseline tests for brew_calc.py
"""
import pytest
from brew_calc import calculate_abv, calculate_ibu, calculate_srm, apparent_attenuation


def test_abv_standard():
    assert calculate_abv(1.050, 1.010) == 5.25


def test_ibu_positive():
    ibu = calculate_ibu(6.5, 28, 60, 20, 1.050)
    assert ibu > 0


def test_srm_pale_ale():
    srm = calculate_srm(5.0)
    assert srm > 0


def test_attenuation_normal():
    att = apparent_attenuation(1.060, 1.012)
    assert 0 < att < 1
