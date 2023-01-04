# Code from Gaussum
# License: GPL
# N. M. O'Boyle, A. L. Tenderholt and K. M. Langner. J. Comp. Chem., 2008, 29, 839-845
import math
import numpy


def activity_to_intensity(activity, frequency, excitation, temperature):
    """Convert Raman acitivity to Raman intensity according to
    Krishnakumar et al, J. Mol. Struct., 2004, 702, 9."""

    excitecm = 1 / (1e-7 * excitation)
    f = 1e-13
    above = f * (excitecm - frequency) ** 4 * activity
    exponential = -6.626068e-34 * 299792458 * frequency / (1.3806503e-23 * temperature)
    below = frequency * (1 - math.exp(exponential))
    return above / below


def get_scaling_factors(filename, scale):
    """Read in scaling factors from an existing output file.

    Note: Scale is prepopulated with the general scaling factor
    """
    inputfile = open(filename, "r")

    line = inputfile.readline()
    line = inputfile.readline()
    i = 0
    line = inputfile.readline().split('\t')
    while len(line) > 6:  # Read in the individual scaling factors
        sf = line[-2]
        if sf != '':
            scale[i] = float(sf)
        i += 1
        line = inputfile.readline().split('\t')
    inputfile.close()
    return scale


def get_raman_intensity_from_log(
        logfile, start=0, end=4000, numpts=500, FWHM=10, scalefactor=1, excitation=785, temperature=293.15):
    act = logfile.vibramans
    freq = logfile.vibfreqs.copy()
    scale = [scalefactor] * len(freq)
    for i in range(len(freq)):
        freq[i] = freq[i] * scale[i]

    intensity = [
        activity_to_intensity(activity, frequency, excitation, temperature)
        for activity, frequency in zip(act, freq)
    ]
    spectrum_intensity = Spectrum(start, end, numpts, [list(zip(freq, intensity))], FWHM, lorentzian)
    return zip(spectrum_intensity.xvalues, spectrum_intensity.spectrum[:, 0])


def plot(spec):
    import matplotlib
    figure = matplotlib.Figure()
    figure.set_xlabel("Frequency (cm$^{-1}$)")
    figure.set_ylabel(f"Raman intensity")
    figure.plot(spec.xvalues, spec.spectrum[:, 0])


def lorentzian(x, peak, height, width):
    """The lorentzian curve.

    f(x) = a/(1+a)

    where a is FWHM**2/4
    """
    a = width ** 2. / 4.
    return float(height) * a / ((peak - x) ** 2 + a)


class Spectrum(object):
    """Convolutes and stores spectrum data.

    Usage:
     Spectrum(start,end,numpts,peaks,width,formula)

    where
     peaks is [(pos,height),...]
     formula is a function such as gaussianpeak or delta


    >>> t = Spectrum(0,50,11,[[(10,1),(30,0.9),(35,1)]],5,delta)
    >>> t.spectrum
    array([[ 0.        ],
           [ 1.        ],
           [ 1.        ],
           [ 1.        ],
           [ 0.        ],
           [ 0.89999998],
           [ 1.89999998],
           [ 1.89999998],
           [ 1.        ],
           [ 0.        ],
           [ 0.        ]],'d')
    """

    def __init__(self, start, end, numpts, peaks, width, formula):
        self.start = start
        self.end = end
        self.numpts = numpts
        self.peaks = peaks
        self.width = width
        self.formula = formula

        # len(peaks) is the number of spectra in this object
        self.spectrum = numpy.zeros((numpts, len(peaks)), "d")
        self.xvalues = numpy.arange(numpts) * float(end - start) / (numpts - 1) + start
        for i in range(numpts):
            x = self.xvalues[i]
            for spectrumno in range(len(peaks)):
                for (pos, height) in peaks[spectrumno]:
                    self.spectrum[i, spectrumno] = self.spectrum[i, spectrumno] + formula(x, pos, height, width)
