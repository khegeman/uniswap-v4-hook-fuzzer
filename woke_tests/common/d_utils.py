from .c_types import *

# pyright: basic


def adjusted_scientific_notation(val, num_decimals=2, exponent_pad=2):
    # https://stackoverflow.com/a/62561794/4204961
    exponent_template = "{:0>%d}" % exponent_pad
    mantissa_template = "{:.%df}" % num_decimals

    order_of_magnitude = math.floor(math.log10(abs(val)))
    nearest_lower_third = 3 * (order_of_magnitude // 3)
    adjusted_mantissa = val * 10 ** (-nearest_lower_third)
    adjusted_mantissa_string = mantissa_template.format(adjusted_mantissa)
    adjusted_exponent_string = "+-"[nearest_lower_third < 0] + exponent_template.format(
        abs(nearest_lower_third)
    )
    return adjusted_mantissa_string + "E" + adjusted_exponent_string


def format_int(x: int) -> str:
    if abs(x) < 10**5:
        return f"{x:_}"
    # no_of_digits = int(math.log10(abs(x))) + 1
    # if x % 10 ** (no_of_digits - 3) == 0:
    #     return f'{x:.2e}'
    # return f'{x:.2E} ({x:_})'
    return f"{adjusted_scientific_notation(x)} ({x:_})"


def num_to_letter(num: int) -> str:
    """converts a number to a lower-case letter
    e.g. 0 -> a, 1 -> b, 2 -> c, etc.
    """
    # there are 26 letters in the English alphabet
    assert num >= 0 and num <= 25
    return chr(ord("a") + num)
