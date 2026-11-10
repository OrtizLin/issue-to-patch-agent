Title: greet() uses print for output
File: calc.py

`greet()` writes to stdout with `print()`. It should use the
`logging` module instead, so output goes through the logger.
