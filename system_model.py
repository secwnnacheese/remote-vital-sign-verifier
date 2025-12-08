"""
System coupling logic for mapping sensor outputs to actuator controls.

The CouplingManager holds sensor and actuator instances, computes control
signals using a coupling matrix, and exposes buffers for visualization.
"""

from collections import deque
from dataclasses import dataclass
import numpy as np
from sensor_models import BaseSensor, build_default_sensors
from actuator_models import BaseActuator, build_default_actuators


@dataclass
class BufferBundle:
    time: deque
    sensors: list[deque]
    actuators: list[deque]


class CouplingManager:
    """
    Manages the multi-sensor, multi-actuator loop with a linear coupling matrix.
    v = C * y + u_override
    """

    def __init__(self, dt: float, history_seconds: float = 15.0):
        self.dt = dt
        self.sensors: list[BaseSensor] = build_default_sensors()
        self.actuators: list[BaseActuator] = build_default_actuators()
        self.num_channels = len(self.sensors)
        self.coupling_matrix = np.eye(self.num_channels) * 0.5
        self.override_controls = np.zeros(self.num_channels)
        buffer_len = int(history_seconds / dt)
        self.buffers = BufferBundle(
            time=deque(maxlen=buffer_len),
            sensors=[deque(maxlen=buffer_len) for _ in range(self.num_channels)],
            actuators=[deque(maxlen=buffer_len) for _ in range(self.num_channels)],
        )
        self.current_time = 0.0

    def step(self, sensor_inputs: list[float], actuator_overrides: list[float] | None = None):
        """Advance the simulation one step."""
        actuator_overrides = actuator_overrides or [0.0] * self.num_channels
        sensor_outputs = np.zeros(self.num_channels)
        for idx, (sensor, physical_input) in enumerate(zip(self.sensors, sensor_inputs)):
            sensor_outputs[idx] = sensor.update(physical_input, self.dt)

        self.override_controls = np.array(actuator_overrides, dtype=float)
        actuator_controls = self.coupling_matrix @ sensor_outputs + self.override_controls
        actuator_effects = np.zeros(self.num_channels)
        for idx, (actuator, control) in enumerate(zip(self.actuators, actuator_controls)):
            actuator_effects[idx] = actuator.update(control, self.dt)

        self.current_time += self.dt
        self._append_buffers(sensor_outputs, actuator_effects)
        return sensor_outputs, actuator_controls, actuator_effects

    def _append_buffers(self, sensor_outputs: np.ndarray, actuator_effects: np.ndarray):
        self.buffers.time.append(self.current_time)
        for idx in range(self.num_channels):
            self.buffers.sensors[idx].append(sensor_outputs[idx])
            self.buffers.actuators[idx].append(actuator_effects[idx])

    def latest_arrays(self):
        """Return numpy arrays of buffered time, sensor outputs, and actuator effects."""
        t = np.fromiter(self.buffers.time, dtype=float)
        sensors = [np.fromiter(buf, dtype=float) for buf in self.buffers.sensors]
        actuators = [np.fromiter(buf, dtype=float) for buf in self.buffers.actuators]
        return t, sensors, actuators

    def export_buffer_to_csv(self, filepath: str):
        """Save buffered signals to CSV with columns: time, s0..s5, a0..a5."""
        t, sensors, actuators = self.latest_arrays()
        if t.size == 0:
            return
        data = np.column_stack([t] + sensors + actuators)
        header_cols = ["time"]
        header_cols += [f"sensor_{i}" for i in range(self.num_channels)]
        header_cols += [f"actuator_{i}" for i in range(self.num_channels)]
        np.savetxt(filepath, data, delimiter=",", header=",".join(header_cols), comments="")
