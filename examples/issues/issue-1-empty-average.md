Title: average([]) raises ZeroDivisionError
File: calc.py

`average([])` crashes with ZeroDivisionError. An empty input
should return 0.0 instead of raising.
