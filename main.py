"""
Remote Vital-Sign Admission Verifier
------------------------------------

Interactive multi-sensor, multi-actuator simulation using PySide6 and
pyqtgraph. This script focuses on clarity and extensibility for academic
signal-processing demonstrations.
"""

import sys
from pathlib import Path
import numpy as np
from PySide6 import QtCore, QtWidgets
import pyqtgraph as pg

from system_model import CouplingManager
from signal_utils import compute_rfft


class MainWindow(QtWidgets.QMainWindow):
    """Main application window with controls, plots, and simulation loop."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Remote Vital-Sign Admission Verifier")
        self.resize(1400, 900)
        pg.setConfigOptions(antialias=True)

        # Simulation settings
        self.dt = 0.01
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._on_timer)
        self.tick_count = 0
        self.running = False

        self.model = CouplingManager(dt=self.dt, history_seconds=20.0)
        self._build_ui()

    # --------------------------- UI Construction ---------------------------
    def _build_ui(self):
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setStretchFactor(1, 3)
        self.setCentralWidget(splitter)
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

    def _build_left_panel(self):
        left_tabs = QtWidgets.QTabWidget()
        left_tabs.addTab(self._build_sensor_tab(), "Sensors")
        left_tabs.addTab(self._build_actuator_tab(), "Actuators")
        return left_tabs

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

    def _build_right_panel(self):
        tabs = QtWidgets.QTabWidget()
        self.time_tab = self._build_time_tab()
        self.freq_tab = self._build_freq_tab()
        self.overview_tab = self._build_overview_tab()
        tabs.addTab(self.time_tab, "Time Domain")
        tabs.addTab(self.freq_tab, "Frequency Domain")
        tabs.addTab(self.overview_tab, "System Overview")
        return tabs

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
            "Adjust sliders to vary physical inputs (left tab) and actuator overrides."
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
        if source_type == "sensor":
            data = sensors[idx]
        else:
            data = actuators[idx]
        window = data[-int(2.0 / self.dt) :] if data.size > 0 else np.array([])
        freqs, mag = compute_rfft(window, self.dt)
        self.fft_curve.setData(freqs, mag)

    def _update_labels(self, sensor_inputs, actuator_overrides, sensor_outputs, actuator_effects):
        for idx, label in enumerate(self.sensor_value_labels):
            label.setText(f"Input: {sensor_inputs[idx]:.2f} | y: {sensor_outputs[idx]:.2f}")
        for idx, label in enumerate(self.actuator_labels):
            label.setText(f"Control override: {actuator_overrides[idx]:.2f} | u: {actuator_effects[idx]:.2f}")

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
