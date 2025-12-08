"""
Actuator models for the Remote Vital-Sign Admission Verifier demo.

Each actuator uses a first-order response to a control input with gain and
saturation limits. The output represents a physical quantity (intensity,
pressure, angle, etc.) in abstract units.
"""

from dataclasses import dataclass


@dataclass
class ActuatorParams:
    gain: float = 1.0
    time_constant: float = 0.25
    min_output: float = 0.0
    max_output: float = 1.0


class BaseActuator:
    """Base class for a single-output actuator."""

    def __init__(self, name: str, params: ActuatorParams | None = None):
        self.name = name
        self.params = params or ActuatorParams()
        self.state = 0.0

    def update(self, control_input: float, dt: float) -> float:
        """
        Update actuator physical effect with first-order response and saturation.
        u[n] = u[n-1] + (dt/tau) * (gain*v - u[n-1])
        """
        tau = max(self.params.time_constant, 1e-6)
        target = self.params.gain * control_input
        alpha = dt / tau
        self.state += alpha * (target - self.state)
        self.state = max(self.params.min_output, min(self.state, self.params.max_output))
        return self.state


def build_default_actuators() -> list[BaseActuator]:
    """Create the six actuators with simple parameter variations."""
    return [
        BaseActuator("Vibrotactile Haptic", ActuatorParams(gain=1.0, max_output=1.0, time_constant=0.12)),
        BaseActuator("Wearable Cuff", ActuatorParams(gain=1.2, max_output=1.0, time_constant=0.2)),
        BaseActuator("Servo Brace", ActuatorParams(gain=1.5, max_output=1.0, time_constant=0.18)),
        BaseActuator("Audible Alarm", ActuatorParams(gain=1.0, max_output=1.0, time_constant=0.1)),
        BaseActuator("LED Status Array", ActuatorParams(gain=0.9, max_output=1.0, time_constant=0.08)),
        BaseActuator("FES Stimulator", ActuatorParams(gain=1.3, max_output=1.0, time_constant=0.22)),
    ]
