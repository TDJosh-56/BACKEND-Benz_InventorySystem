from decimal import Decimal

UNITS = ['kg', 'g', 'L', 'mL', 'Pcs']

_WEIGHT = {'kg': Decimal(1000), 'g': Decimal(1)}
_VOLUME = {'L': Decimal(1000), 'mL': Decimal(1)}


def convert(value, from_unit, to_unit):
    """Returns None when units are incompatible (kg -> L, Pcs -> g)."""
    value = Decimal(str(value))
    if from_unit == to_unit:
        return value
    for family in (_WEIGHT, _VOLUME):
        if from_unit in family and to_unit in family:
            return value * family[from_unit] / family[to_unit]
    return None


def compatible(unit_a, unit_b):
    return convert(1, unit_a, unit_b) is not None