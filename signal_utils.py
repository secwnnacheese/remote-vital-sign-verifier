"""
Signal processing utilities for time/frequency analysis.
"""

import numpy as np


def compute_rfft(signal: np.ndarray, dt: float):
    """Compute real FFT magnitude and frequency axis for a 1D signal."""
    if signal.size == 0:
        return np.array([]), np.array([])
    n = signal.size
    freqs = np.fft.rfftfreq(n, d=dt)
    spectrum = np.fft.rfft(signal - np.mean(signal))
    magnitude = np.abs(spectrum)
    return freqs, magnitude
