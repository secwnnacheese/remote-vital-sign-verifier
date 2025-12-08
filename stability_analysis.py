"""
Stability analysis utilities using the control library.

Creates first-order transfer functions for each sensor/actuator channel and
returns Bode data, poles, zeros, and stability margins. Uses simple dynamics:
G(s) = K / (tau*s + 1), discretized with zero-order hold for z-domain.
"""

from __future__ import annotations

from typing import List

import numpy as np

try:
    import control  # type: ignore
except ImportError:  # pragma: no cover - graceful fallback
    control = None


class StabilityAnalyzer:
    """Produces Bode and pole-zero data for sensors/actuators."""

    def __init__(self, sensors, actuators):
        self.sensors = sensors
        self.actuators = actuators

    def _tf_from_params(self, gain: float, tau: float):
        if control is None:
            raise RuntimeError("control library not available")
        num = [gain]
        den = [tau, 1.0]
        return control.TransferFunction(num, den)

    def get_channel_tf(self, channel_type: str, idx: int, dt: float):
        """
        Build continuous and discrete transfer functions for the given channel.
        channel_type: 'sensor' or 'actuator'
        """
        if control is None:
            raise RuntimeError("control library not available")
        if channel_type == "sensor":
            params = self.sensors[idx].params
        else:
            params = self.actuators[idx].params
        tau = max(getattr(params, "time_constant", 0.1), 1e-6)
        gain = getattr(params, "gain", 1.0)
        g_s = self._tf_from_params(gain, tau)
        g_z = control.c2d(g_s, dt, method="zoh")
        return g_s, g_z

    def bode_data(self, channel_type: str, idx: int, dt: float):
        """
        Return frequency (rad/s), magnitude (dB), phase (deg) for the channel.
        """
        if control is None:
            raise RuntimeError("control library not available")
        g_s, _ = self.get_channel_tf(channel_type, idx, dt)
        omega, mag, phase = control.bode_plot(g_s, Plot=False)
        mag_db = 20 * np.log10(mag)
        return omega, mag_db, phase

    def poles_zeros(self, channel_type: str, idx: int, dt: float):
        """Return continuous/discrete poles and zeros."""
        if control is None:
            raise RuntimeError("control library not available")
        g_s, g_z = self.get_channel_tf(channel_type, idx, dt)
        poles_s = control.pole(g_s)
        zeros_s = control.zero(g_s)
        poles_z = control.pole(g_z)
        zeros_z = control.zero(g_z)
        return poles_s, zeros_s, poles_z, zeros_z

    def margins(self, channel_type: str, idx: int, dt: float):
        """Compute gain margin, phase margin, and corresponding frequencies."""
        if control is None:
            raise RuntimeError("control library not available")
        g_s, _ = self.get_channel_tf(channel_type, idx, dt)
        gm, pm, wg, wp = control.margin(g_s)
        return gm, pm, wg, wp

    def report_summary(self, channel_type: str, idx: int, dt: float) -> str:
        """Generate a text summary of poles/zeros and margins."""
        if control is None:
            return "control library not available; cannot generate report."
        poles_s, zeros_s, poles_z, zeros_z = self.poles_zeros(channel_type, idx, dt)
        gm, pm, wg, wp = self.margins(channel_type, idx, dt)
        lines: List[str] = []
        lines.append(f"Channel: {channel_type} #{idx+1}")
        lines.append("Continuous-time poles: " + ", ".join(f"{p:.4g}" for p in poles_s))
        lines.append("Continuous-time zeros: " + (", ".join(f"{z:.4g}" for z in zeros_s) or "None"))
        lines.append("Discrete-time poles: " + ", ".join(f"{p:.4g}" for p in poles_z))
        lines.append("Discrete-time zeros: " + (", ".join(f"{z:.4g}" for z in zeros_z) or "None"))
        lines.append(f"Gain margin: {gm:.3g} at {wg:.3g} rad/s")
        lines.append(f"Phase margin: {pm:.3g} deg at {wp:.3g} rad/s")
        return "\n".join(lines)
