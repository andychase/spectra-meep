def activity_to_intensity(activity, frequency, excitation, temperature):
    """Convert Raman acitivity to Raman intensity according to
    Krishnakumar et al, J. Mol. Struct., 2004, 702, 9."""

    excitecm = 1 / (1e-7 * excitation)
    f = 1e-13
    above = f * (excitecm - frequency)**4 * activity
    exponential = -6.626068e-34 * 299792458 * frequency / (1.3806503e-23 * temperature)
    below = frequency * (1 - math.exp(exponential))
    return above / below
