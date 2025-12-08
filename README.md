# Integrated Instrumentation & Signal Simulation System

PySide6 + pyqtgraph desktop app for multi-sensor, multi-actuator simulation with stability analysis, 3D spatial visualization, and Rust-backed signal generation.

## Highlights
- 6 sensors + 6 actuators with sliders for physical inputs and overrides; linear coupling matrix `v = C * y`.
- Real-time time-domain and FFT plots; CSV export of buffers.
- Stability tab: s/z-domain analysis via `control`, Bode magnitude/phase, pole-zero map, gain/phase margins, report export.
- 3D tab: sensor/actuator placement using `pyqtgraph.opengl` (spheres/cubes scale and recolor with amplitude).
- Rust tab: two-signal generator (add/sub/mul) computed by Rust binary; Python parses JSON and plots `x1, x2, y`.

## Requirements
- Python 3.10+
- PySide6, pyqtgraph, numpy, scipy, control
- For 3D view: `pyqtgraph[opengl]` and working OpenGL drivers
- Rust toolchain (for building the backend binary)

Install Python deps:
```bash
pip install PySide6 pyqtgraph numpy scipy control
# optional for 3D
pip install "pyqtgraph[opengl]"
```

## Build Rust backend
```bash
cd backend_rust
cargo build --release
# binary expected at backend_rust/target/release/rvsv_rust (rvsv_rust.exe on Windows)
```

## Run
```bash
python main.py
```

## Tabs and Usage
- **Instrumentation System**: sensor/actuator sliders, time/freq plots, coupling table, CSV export; 3D spatial view if OpenGL available.
- **Stability Analysis**: pick channel (sensor/actuator), run Bode/pole-zero/margins; export text report (gain/phase margins, poles/zeros).
- **Signal Generator (Rust)**: set f/A/phase for two signals, pick operation (add/sub/mul), run Rust job; plots `x1, x2, y`.

### Stability Analysis Notes
- Transfer model per channel: \(G(s) = \frac{K}{\tau s + 1}\), discretized with ZOH for \(G(z)\).
- Bode plot shows magnitude (dB) and phase (deg); pole-zero map uses s-plane positions.
- Report includes poles/zeros (continuous/discrete) and gain/phase margins with crossover frequencies.
- If `control` is missing, the UI will show a graceful error instead of crashing.

### 3D Spatial View Notes
- Uses `pyqtgraph.opengl` (GLViewWidget). Sensors are spheres, actuators are cubes placed at fixed coordinates.
- Color and scale respond to live signal amplitude (absolute value clipped to [0,1]).
- If OpenGL is unavailable, a placeholder message is shown instead of failing.

### Rust Signal Generator Notes
- CLI args: `--mode [add|sub|mul] --f1 --a1 --p1 --f2 --a2 --p2 --duration --dt`
- Outputs JSON `{time, x1, x2, y}`; Python parses and plots.
- `rust_bridge.py` returns deterministic mock data if the binary is missing or errors to keep the UI responsive.

## Project Layout
- `main.py` — GUI, simulation loop, tabs, CSV export.
- `sensor_models.py` — sensor models and defaults.
- `actuator_models.py` — actuator models and defaults.
- `system_model.py` — coupling manager, buffers, CSV helper.
- `signal_utils.py` — FFT helper.
- `stability_analysis.py` — control-based Bode/pole-zero/margins/report.
- `visualizer_3d.py` — OpenGL spatial view for sensors/actuators.
- `rust_bridge.py` — subprocess bridge to Rust binary (mock fallback if missing).
- `backend_rust/src/main.rs` — Rust CLI producing JSON (time, x1, x2, y).

## Extending
- Adjust coupling matrix in `system_model.py`.
- Tune gains/time constants/noise/saturation in sensor/actuator params.
- Replace Rust math with your own operations, keeping the JSON contract.
- Add filtering/control law inside `CouplingManager.step`.
