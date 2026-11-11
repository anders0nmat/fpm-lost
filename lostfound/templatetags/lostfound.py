from django import template
from math import trunc

register = template.Library()

@register.filter
def floatfmt(value, arg: str = '-'):
    neg, pos, *_ = arg.split(',') + ['-', '']

    if value < 0:
        return neg + str(abs(value))
    else:
        return pos + str(abs(value))

@register.filter
def sisuffix(value, arg: str = ''):
    SUFFIXES = " K"
    for suffix in SUFFIXES:
        if value < 1000:
            return f"{float(value):g}" + arg + suffix.strip()
        value /= 1000
    return f"{float(value):g}" + arg + SUFFIXES[-1]