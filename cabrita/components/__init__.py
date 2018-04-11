from enum import Enum


class BoxColor(Enum):
    """
    Python Blessing Colors Enum
    https://pypi.python.org/pypi/blessings/

    | Color   | Normal | Bright |
    |---------|--------|--------|
    | black   | 0      | 8      |
    | red     | 1      | 9      |
    | green   | 2      | 10     |
    | yellow  | 3      | 11     |
    | blue    | 4      | 12     |
    | magenta | 5      | 13     |
    | cyan    | 6      | 14     |
    | white   | 7      | 15     |

    """
    black = 0
    yellow = 11
    cyan = 14
    white = 7