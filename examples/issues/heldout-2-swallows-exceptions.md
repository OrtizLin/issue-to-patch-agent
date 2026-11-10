Title: parse_count swallows all exceptions
File: calc.py

`parse_count` swallows all exceptions instead of only the one
that a bad number raises. Only ValueError should be caught.
