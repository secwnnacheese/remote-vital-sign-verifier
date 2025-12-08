"""
Integrated Instrumentation & Signal Simulation System.

Combines multi-sensor simulation, stability analysis (s/z domains),
3D spatial visualization, and Rust-backed signal generation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets

from system_model import CouplingManager
from signal_utils import compute_rfft
from stability_analysis import StabilityAnalyzer
from visualizer_3d import SystemVisualizer3D, GL_AVAILABLE
from rust_bridge import RustBridge


class MainWindow(QtWidgets.QMainWindow):
    """Main application window with instrumentation, stability, and Rust tabs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Integrated Instrumentation & Signal Simulation System")
        self.resize(1500, 950)
        pg.setConfigOptions(antialias=True)

        # Simulation settings
        self.dt = 0.01
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.tick_count = 0
        self.running = False

        self.model = CouplingManager(dt=self.dt, history_seconds=20.0)
        self.analyzer = StabilityAnalyzer(self.model.sensors, self.model.actuators)
        self.rust_bridge = RustBridge()

        self._build_ui()

    # --------------------------- UI Construction ---------------------------
    def _build_ui(self):
        self.status_label = QtWidgets.QLabel("Stopped")
        self.start_button = QtWidgets.QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.toggle_simulation)
        self.export_button = QtWidgets.QPushButton("Export CSV")
        self.export_button.clicked.connect(self.export_csv)

        bottom_bar = QtWidgets.QWidget()
        h_layout = QtWidgets.QHBoxLayout(bottom_bar)
        h_layout.addWidget(self.start_button)
        h_layout.addWidget(self.export_button)
        h_layout.addStretch()
        h_layout.addWidget(self.status_label)
        self.statusBar().addPermanentWidget(bottom_bar, 1)

        self.main_tabs = QtWidgets.QTabWidget()
        self.instrumentation_tab = self._build_instrumentation_tab()
        self.stability_tab = self._build_stability_tab()
        self.rust_tab = self._build_rust_tab()
        self.main_tabs.addTab(self.instrumentation_tab, "Instrumentation System")
        self.main_tabs.addTab(self.stability_tab, "Stability Analysis")
        self.main_tabs.addTab(self.rust_tab, "Signal Generator (Rust)")
        self.setCentralWidget(self.main_tabs)

    def _build_instrumentation_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)

        left_tabs = QtWidgets.QTabWidget()
        left_tabs.addTab(self._build_sensor_tab(), "Sensors")
        left_tabs.addTab(self._build_actuator_tab(), "Actuators")

        right_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.time_freq_tabs = QtWidgets.QTabWidget()
        self.time_tab = self._build_time_tab()
        self.freq_tab = self._build_freq_tab()
        self.overview_tab = self._build_overview_tab()
        self.time_freq_tabs.addTab(self.time_tab, "Time Domain")
        self.time_freq_tabs.addTab(self.freq_tab, "Frequency Domain")
        self.time_freq_tabs.addTab(self.overview_tab, "System Overview")
        right_splitter.addWidget(self.time_freq_tabs)

        self.visualizer_group = QtWidgets.QGroupBox("3D Spatial Visualization (Sensors/Actuators)")
        v_layout = QtWidgets.QVBoxLayout(self.visualizer_group)
        if GL_AVAILABLE:
            self.visualizer = SystemVisualizer3D()
            v_layout.addWidget(self.visualizer)
        else:
            self.visualizer = None
            v_layout.addWidget(QtWidgets.QLabel("OpenGL not available. Install pyqtgraph[opengl] to enable."))
        right_splitter.addWidget(self.visualizer_group)
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 1)

        layout.addWidget(left_tabs, 1)
        layout.addWidget(right_splitter, 3)
        return widget

    def _build_sensor_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        self.sensor_sliders = []
        self.sensor_value_labels = []
        for idx, sensor in enumerate(self.model.sensors):
            group = QtWidgets.QGroupBox(f"{idx+1}) {sensor.name}")
            g_layout = QtWidgets.QHBoxLayout(group)
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(20)
            slider.valueChanged.connect(self._make_slider_label_updater(idx, is_sensor=True))
            label = QtWidgets.QLabel("Input: 0.20")
            g_layout.addWidget(slider)
            g_layout.addWidget(label)
            layout.addWidget(group)
            self.sensor_sliders.append(slider)
            self.sensor_value_labels.append(label)
        layout.addStretch()
        return widget

    def _build_actuator_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        self.actuator_sliders = []
        self.actuator_labels = []
        for idx, actuator in enumerate(self.model.actuators):
            group = QtWidgets.QGroupBox(f"{idx+1}) {actuator.name}")
            g_layout = QtWidgets.QHBoxLayout(group)
            slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(0)
            slider.valueChanged.connect(self._make_slider_label_updater(idx, is_sensor=False))
            label = QtWidgets.QLabel("Control override: 0.00")
            g_layout.addWidget(slider)
            g_layout.addWidget(label)
            layout.addWidget(group)
            self.actuator_sliders.append(slider)
            self.actuator_labels.append(label)
        layout.addStretch()
        return widget

    def _build_time_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        self.sensor_plot = pg.PlotWidget(title="Sensor Outputs")
        self.sensor_plot.addLegend()
        self.sensor_curves = []
        for idx, sensor in enumerate(self.model.sensors):
            curve = self.sensor_plot.plot([], [], pen=pg.intColor(idx, hues=12), name=f"S{idx+1}: {sensor.name}")
            self.sensor_curves.append(curve)

        self.actuator_plot = pg.PlotWidget(title="Actuator Effects")
        self.actuator_plot.addLegend()
        self.actuator_curves = []
        for idx, actuator in enumerate(self.model.actuators):
            curve = self.actuator_plot.plot([], [], pen=pg.intColor(idx + 6, hues=12), name=f"A{idx+1}: {actuator.name}")
            self.actuator_curves.append(curve)

        layout.addWidget(self.sensor_plot)
        layout.addWidget(self.actuator_plot)
        return widget

    def _build_freq_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        selector_layout = QtWidgets.QHBoxLayout()
        selector_layout.addWidget(QtWidgets.QLabel("Source:"))
        self.fft_source_combo = QtWidgets.QComboBox()
        for idx, sensor in enumerate(self.model.sensors):
            self.fft_source_combo.addItem(f"Sensor {idx+1}: {sensor.name}", ("sensor", idx))
        for idx, actuator in enumerate(self.model.actuators):
            self.fft_source_combo.addItem(f"Actuator {idx+1}: {actuator.name}", ("actuator", idx))
        selector_layout.addWidget(self.fft_source_combo)
        selector_layout.addStretch()

        self.fft_plot = pg.PlotWidget(title="Magnitude Spectrum")
        self.fft_curve = self.fft_plot.plot([], [], pen=pg.mkPen(color="c", width=2))
        self.fft_plot.setLabel("bottom", "Frequency (Hz)")
        self.fft_plot.setLabel("left", "Magnitude")

        layout.addLayout(selector_layout)
        layout.addWidget(self.fft_plot)
        return widget

    def _build_overview_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        desc = QtWidgets.QLabel(
            "Mapping: sensors -> coupling matrix -> actuator controls.\n"
            "Adjust sliders to vary physical inputs and actuator overrides."
        )
        desc.setWordWrap(True)

        self.coupling_table = QtWidgets.QTableWidget(self.model.num_channels, self.model.num_channels)
        self.coupling_table.setHorizontalHeaderLabels([f"S{i+1}" for i in range(self.model.num_channels)])
        self.coupling_table.setVerticalHeaderLabels([f"A{i+1}" for i in range(self.model.num_channels)])
        self.coupling_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.coupling_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self._refresh_coupling_table()

        layout.addWidget(desc)
        layout.addWidget(self.coupling_table)
        return widget

    # --------------------------- Stability Tab ---------------------------
    def _build_stability_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        top_row = QtWidgets.QHBoxLayout()
        self.channel_combo = QtWidgets.QComboBox()
        for idx, sensor in enumerate(self.model.sensors):
            self.channel_combo.addItem(f"Sensor {idx+1}: {sensor.name}", ("sensor", idx))
        for idx, actuator in enumerate(self.model.actuators):
            self.channel_combo.addItem(f"Actuator {idx+1}: {actuator.name}", ("actuator", idx))
        self.run_stability_btn = QtWidgets.QPushButton("Analyze")
        self.run_stability_btn.clicked.connect(self._run_stability_analysis)
        self.report_btn = QtWidgets.QPushButton("Generate Report")
        self.report_btn.clicked.connect(self._generate_report)
        top_row.addWidget(QtWidgets.QLabel("Channel:"))
        top_row.addWidget(self.channel_combo)
        top_row.addWidget(self.run_stability_btn)
        top_row.addWidget(self.report_btn)
        top_row.addStretch()

        self.mag_plot = pg.PlotWidget(title="Bode Magnitude (dB)")
        self.phase_plot = pg.PlotWidget(title="Bode Phase (deg)")
        self.pz_plot = pg.PlotWidget(title="Pole-Zero Map (s-plane)")
        self.mag_curve = self.mag_plot.plot([], [], pen=pg.mkPen(color="y", width=2))
        self.phase_curve = self.phase_plot.plot([], [], pen=pg.mkPen(color="m", width=2))
        self.pole_scatter = pg.ScatterPlotItem(pen=pg.mkPen(None), brush=pg.mkBrush(255, 0, 0), size=10)
        self.zero_scatter = pg.ScatterPlotItem(pen=pg.mkPen(None), brush=pg.mkBrush(0, 255, 0), size=10, symbol="o")
        self.pz_plot.addItem(self.pole_scatter)
        self.pz_plot.addItem(self.zero_scatter)
        self.margin_label = QtWidgets.QLabel("Gain/Phase margins will appear here.")

        layout.addLayout(top_row)
        layout.addWidget(self.mag_plot)
        layout.addWidget(self.phase_plot)
        layout.addWidget(self.pz_plot)
        layout.addWidget(self.margin_label)
        return widget

    # --------------------------- Rust Tab ---------------------------
    def _build_rust_tab(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        form = QtWidgets.QGridLayout()
        self.sig1_freq = self._spinbox(0.0, 50.0, 1.0, 0.1)
        self.sig1_amp = self._spinbox(0.0, 2.0, 1.0, 0.05)
        self.sig1_phase = self._spinbox(-np.pi, np.pi, 0.0, 0.1)
        self.sig2_freq = self._spinbox(0.0, 50.0, 2.0, 0.1)
        self.sig2_amp = self._spinbox(0.0, 2.0, 1.0, 0.05)
        self.sig2_phase = self._spinbox(-np.pi, np.pi, 0.0, 0.1)
        self.duration_spin = self._spinbox(0.1, 10.0, 2.0, 0.1)
        self.dt_spin = self._spinbox(0.001, 0.1, 0.01, 0.001)

        form.addWidget(QtWidgets.QLabel("Signal 1 Freq (Hz)"), 0, 0)
        form.addWidget(self.sig1_freq, 0, 1)
        form.addWidget(QtWidgets.QLabel("Amp"), 0, 2)
        form.addWidget(self.sig1_amp, 0, 3)
        form.addWidget(QtWidgets.QLabel("Phase (rad)"), 0, 4)
        form.addWidget(self.sig1_phase, 0, 5)

        form.addWidget(QtWidgets.QLabel("Signal 2 Freq (Hz)"), 1, 0)
        form.addWidget(self.sig2_freq, 1, 1)
        form.addWidget(QtWidgets.QLabel("Amp"), 1, 2)
        form.addWidget(self.sig2_amp, 1, 3)
        form.addWidget(QtWidgets.QLabel("Phase (rad)"), 1, 4)
        form.addWidget(self.sig2_phase, 1, 5)

        form.addWidget(QtWidgets.QLabel("Duration (s)"), 2, 0)
        form.addWidget(self.duration_spin, 2, 1)
        form.addWidget(QtWidgets.QLabel("dt (s)"), 2, 2)
        form.addWidget(self.dt_spin, 2, 3)

        op_group = QtWidgets.QGroupBox("Operation")
        op_layout = QtWidgets.QHBoxLayout(op_group)
        self.mode_buttons = {
            "add": QtWidgets.QRadioButton("Add"),
            "sub": QtWidgets.QRadioButton("Subtract"),
            "mul": QtWidgets.QRadioButton("Multiply"),
        }
        self.mode_buttons["add"].setChecked(True)
        for btn in self.mode_buttons.values():
            op_layout.addWidget(btn)

        self.run_rust_btn = QtWidgets.QPushButton("Run Rust Simulation")
        self.run_rust_btn.clicked.connect(self._run_rust_job)
        self.rust_status = QtWidgets.QLabel("Ready.")

        self.rust_plot = pg.PlotWidget(title="Rust Signal Combination")
        self.rust_curve_x1 = self.rust_plot.plot([], [], pen=pg.mkPen(color="c", width=1), name="x1")
        self.rust_curve_x2 = self.rust_plot.plot([], [], pen=pg.mkPen(color="y", width=1), name="x2")
        self.rust_curve_y = self.rust_plot.plot([], [], pen=pg.mkPen(color="m", width=2), name="y")
        self.rust_plot.addLegend()
        self.rust_plot.setLabel("bottom", "Time (s)")

        layout.addLayout(form)
        layout.addWidget(op_group)
        layout.addWidget(self.run_rust_btn)
        layout.addWidget(self.rust_plot)
        layout.addWidget(self.rust_status)
        return widget

    # --------------------------- Simulation Loop ---------------------------
    def toggle_simulation(self):
        if self.running:
            self.timer.stop()
            self.start_button.setText("Start Simulation")
            self.status_label.setText("Stopped")
            self.running = False
            return
        self.timer.start(int(self.dt * 1000))
        self.start_button.setText("Stop Simulation")
        self.status_label.setText(f"Running at {int(1/self.dt)} Hz")
        self.running = True

    def _on_timer(self):
        sensor_inputs = [slider.value() / 100.0 for slider in self.sensor_sliders]
        actuator_overrides = [slider.value() / 100.0 for slider in self.actuator_sliders]
        sensor_outputs, _, actuator_effects = self.model.step(sensor_inputs, actuator_overrides)
        self._update_time_plots()
        if self.tick_count % 10 == 0:
            self._update_fft_plot()
        self._update_labels(sensor_inputs, actuator_overrides, sensor_outputs, actuator_effects)
        if GL_AVAILABLE and self.visualizer:
            self.visualizer.update_state(sensor_outputs, actuator_effects)
        self.tick_count += 1

    def _update_time_plots(self):
        t, sensors, actuators = self.model.latest_arrays()
        if t.size == 0:
            return
        for idx, curve in enumerate(self.sensor_curves):
            curve.setData(t, sensors[idx])
        for idx, curve in enumerate(self.actuator_curves):
            curve.setData(t, actuators[idx])

    def _update_fft_plot(self):
        source_type, idx = self.fft_source_combo.currentData()
        _, sensors, actuators = self.model.latest_arrays()
        data = sensors[idx] if source_type == "sensor" else actuators[idx]
        window = data[-int(2.0 / self.dt) :] if data.size > 0 else np.array([])
        freqs, mag = compute_rfft(window, self.dt)
        self.fft_curve.setData(freqs, mag)

    def _update_labels(self, sensor_inputs, actuator_overrides, sensor_outputs, actuator_effects):
        for idx, label in enumerate(self.sensor_value_labels):
            label.setText(f"Input: {sensor_inputs[idx]:.2f} | y: {sensor_outputs[idx]:.2f}")
        for idx, label in enumerate(self.actuator_labels):
            label.setText(f"Control override: {actuator_overrides[idx]:.2f} | u: {actuator_effects[idx]:.2f}")

    # --------------------------- Stability Logic ---------------------------
    def _run_stability_analysis(self):
        channel_type, idx = self.channel_combo.currentData()
        try:
            omega, mag_db, phase = self.analyzer.bode_data(channel_type, idx, self.dt)
            poles_s, zeros_s, poles_z, _ = self.analyzer.poles_zeros(channel_type, idx, self.dt)
            gm, pm, wg, wp = self.analyzer.margins(channel_type, idx, self.dt)
        except Exception as exc:
            self.margin_label.setText(f"Analysis unavailable: {exc}")
            return

        self.mag_curve.setData(omega, mag_db)
        self.phase_curve.setData(omega, phase)
        pole_points = [{"pos": (p.real, p.imag)} for p in poles_s]
        zero_points = [{"pos": (z.real, z.imag)} for z in zeros_s]
        self.pole_scatter.setData(pole_points)
        self.zero_scatter.setData(zero_points)
        gm_val = gm[0] if hasattr(gm, "__len__") else gm
        pm_val = pm[0] if hasattr(pm, "__len__") else pm
        wg_val = wg[0] if hasattr(wg, "__len__") else wg
        wp_val = wp[0] if hasattr(wp, "__len__") else wp
        self.margin_label.setText(
            f"Gain margin: {gm_val:.3g} at {wg_val:.3g} rad/s | "
            f"Phase margin: {pm_val:.3g} deg at {wp_val:.3g} rad/s"
        )

    def _generate_report(self):
        channel_type, idx = self.channel_combo.currentData()
        summary = self.analyzer.report_summary(channel_type, idx, self.dt)
        default_path = str(Path.cwd() / "stability_report.txt")
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Stability Report", default_path, "Text Files (*.txt)"
        )
        if filepath:
            Path(filepath).write_text(summary)
            self.margin_label.setText(f"Report saved to {filepath}")

    # --------------------------- Rust Logic ---------------------------
    def _run_rust_job(self):
        mode = [key for key, btn in self.mode_buttons.items() if btn.isChecked()][0]
        params = {
            "mode": mode,
            "f1": self.sig1_freq.value(),
            "a1": self.sig1_amp.value(),
            "p1": self.sig1_phase.value(),
            "f2": self.sig2_freq.value(),
            "a2": self.sig2_amp.value(),
            "p2": self.sig2_phase.value(),
            "duration": self.duration_spin.value(),
            "dt": self.dt_spin.value(),
        }
        result = self.rust_bridge.run_job(params)
        time = np.array(result.get("time", []))
        x1 = np.array(result.get("x1", []))
        x2 = np.array(result.get("x2", []))
        y = np.array(result.get("y", []))
        self.rust_curve_x1.setData(time, x1)
        self.rust_curve_x2.setData(time, x2)
        self.rust_curve_y.setData(time, y)
        meta = result.get("meta", "Completed.")
        self.rust_status.setText(f"Rust run done. {meta}")

    # --------------------------- Helpers & IO ---------------------------
    def _make_slider_label_updater(self, idx: int, is_sensor: bool):
        def updater(value: int):
            if is_sensor:
                self.sensor_value_labels[idx].setText(f"Input: {value/100:.2f}")
            else:
                self.actuator_labels[idx].setText(f"Control override: {value/100:.2f}")
        return updater

    def _refresh_coupling_table(self):
        for row in range(self.model.num_channels):
            for col in range(self.model.num_channels):
                item = QtWidgets.QTableWidgetItem(f"{self.model.coupling_matrix[row, col]:.2f}")
                item.setFlags(QtCore.Qt.ItemIsEnabled)
                self.coupling_table.setItem(row, col, item)

    def _spinbox(self, min_val: float, max_val: float, default: float, step: float):
        box = QtWidgets.QDoubleSpinBox()
        box.setRange(min_val, max_val)
        box.setSingleStep(step)
        box.setValue(default)
        return box

    def export_csv(self):
        default_path = str(Path.cwd() / "simulation_log.csv")
        filepath, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export CSV", default_path, "CSV Files (*.csv)")
        if filepath:
            self.model.export_buffer_to_csv(filepath)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
