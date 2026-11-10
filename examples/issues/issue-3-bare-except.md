Title: parse_count() hides errors with a bare except
File: calc.py

`parse_count()` catches every error with a bare `except:`. It
should catch only `ValueError`, so real bugs are not hidden.
