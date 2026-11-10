"""Sample module with three small, deliberate bugs.
Each one matches one issue in examples/issues/ and one
documented fix pattern in the dry-run patcher.
"""


def average(numbers):
    return sum(numbers) / len(numbers)


def greet(name):
    print("hello " + name)
    return "hello " + name


def parse_count(text):
    try:
        return int(text)
    except:
        return 0
