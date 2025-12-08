"""
Sensor models for the Remote Vital-Sign Admission Verifier demo.

Each sensor uses a simple first-order response with configurable gain,
offset, noise, and time constant. These are intentionally lightweight so
they can be replaced with more detailed models later.
"""

from dataclasses import dataclass, field
import numpy as np


@dataclass
class SensorParams:
    gain: float = 1.0
    offset: float = 0.0
    noise_std: float = 0.01
    time_constant: float = 0.3  # seconds


class BaseSensor:
    """Base class for a single-output sensor."""

    def __init__(self, name: str, params: SensorParams | None = None):
        self.name = name
        self.params = params or SensorParams()
        self.state = 0.0

    def update(self, physical_input: float, dt: float) -> float:
        """
        Update sensor output with a first-order low-pass response.
        y[n] = y[n-1] + (dt/tau) * (gain*x + offset - y[n-1]) + noise
        """
        tau = max(self.params.time_constant, 1e-6)
        target = self.params.gain * physical_input + self.params.offset
        alpha = dt / tau
        noise = np.random.normal(0.0, self.params.noise_std)
        self.state += alpha * (target - self.state) + noise
        return self.state


def build_default_sensors() -> list[BaseSensor]:
    """Create the six sensors with simple parameter variations."""
    return [
        BaseSensor("Tri-axial Accelerometer", SensorParams(gain=1.2, noise_std=0.02, time_constant=0.15)),
        BaseSensor("Gyroscope", SensorParams(gain=0.9, noise_std=0.015, time_constant=0.12)),
        BaseSensor("Pressure Insole (FSR)", SensorParams(gain=1.5, noise_std=0.03, time_constant=0.25)),
        BaseSensor("IMU on Waist", SensorParams(gain=1.0, noise_std=0.02, time_constant=0.2)),
        BaseSensor("Barometric Altimeter", SensorParams(gain=0.7, noise_std=0.01, time_constant=0.4)),
        BaseSensor("Proximity (ToF)", SensorParams(gain=1.1, noise_std=0.02, time_constant=0.18)),
    ]
