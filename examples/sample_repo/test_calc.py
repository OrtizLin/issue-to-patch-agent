"""Tests that encode the expected behaviour from the issues.
They FAIL on the buggy code and PASS after the patch is applied.
"""
from calc import average, greet, parse_count


def test_average_empty_returns_zero():
    assert average([]) == 0.0


def test_average_normal():
    assert average([2, 4]) == 3.0


def test_greet_returns_greeting():
    assert greet("Otis") == "hello Otis"


def test_parse_count_valid():
    assert parse_count("42") == 42


def test_parse_count_invalid_returns_zero():
    assert parse_count("not-a-number") == 0
