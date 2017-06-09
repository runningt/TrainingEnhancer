def _normalized_float(value, round_digits=5):
    try:
        return round(float(value), round_digits)
    except ValueError:
        return None
