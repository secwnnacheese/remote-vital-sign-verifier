# Remote Vital-Sign Admission Verifier

Python desktop app for interactive multi-sensor, multi-actuator signal processing. Built with PySide6 + pyqtgraph for real-time plots (time and frequency domains).

## Features
- 6 sensor inputs (accelerometer, gyroscope, pressure insole, waist IMU, barometric, proximity) with sliders for physical inputs.
- 6 actuator controls (haptic, cuff, servo brace, alarm, LED array, FES) with override sliders.
- Linear coupling matrix `v = C * y` to map sensors → actuators.
- Real-time time-domain and FFT plots; coupling overview table; start/stop; CSV export of buffers.
- Modular models: first-order sensor/actuator dynamics with tunable gain/offset/noise/time constants.

## Requirements
- Python 3.x
- PySide6, pyqtgraph, numpy, scipy (signal_utils uses FFT via numpy; scipy optional for future filtering)

Install (pip):
```bash
pip install PySide6 pyqtgraph numpy scipy
```

## Run
```bash
python main.py
```

## Project Layout
- `main.py` — GUI, simulation loop, plots, CSV export.
- `sensor_models.py` — sensor classes and defaults.
- `actuator_models.py` — actuator classes and defaults.
- `system_model.py` — coupling manager, buffers, CSV helper.
- `signal_utils.py` — FFT helper.

## Usage Notes
- Start/Stop simulation from the bottom bar; status shows the loop rate (default 100 Hz).
- Left tabs: adjust sensor physical inputs and actuator overrides.
- Right tabs: view time-domain curves, FFT for selected channel, and the coupling matrix table.
- Export CSV saves buffered time, sensors, and actuator effects (`simulation_log.csv` by default).

## Extending
- Modify coupling in `system_model.py` (`self.coupling_matrix`) to experiment with mappings.
- Tune sensor/actuator parameters in their constructors (gain, noise_std, time_constant, saturation).
- Add filtering or control logic by extending the simulation step in `system_model.CouplingManager`.
