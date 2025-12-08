"""
3D visualization of sensor/actuator placements using pyqtgraph.opengl.

Sensors are spheres, actuators are cubes. Size/color reflect current values.
"""

from __future__ import annotations

from typing import List

try:
    from pyqtgraph.opengl import GLViewWidget, MeshData, GLMeshItem
    import pyqtgraph.opengl as gl
    GL_AVAILABLE = True
except Exception:  # pragma: no cover - OpenGL may be missing
    GL_AVAILABLE = False
    GLViewWidget = object  # type: ignore
    MeshData = None  # type: ignore
    GLMeshItem = None  # type: ignore

import numpy as np


class SystemVisualizer3D(GLViewWidget):
    """3D view showing sensor (spheres) and actuator (cubes) placements."""

    def __init__(self, parent=None):
        # Initialize minimal attributes even if GL is unavailable to prevent attribute errors.
        self.sensors: List = []
        self.actuators: List = []
        self.sensor_positions = []
        self.actuator_positions = []
        if not GL_AVAILABLE:
            return
        super().__init__(parent)
        self.setBackgroundColor("k")
        self.opts["distance"] = 20
        self.grid = gl.GLGridItem()
        self.addItem(self.grid)
        self._init_items()

    def _init_items(self):
        if not GL_AVAILABLE:
            return
        sensor_positions = [
            (-4, -2, 0),
            (-2, 2, 1),
            (0, -3, 2),
            (2, 3, -1),
            (4, -1, 1.5),
            (1, 1, -2),
        ]
        actuator_positions = [
            (-4, 3, -1),
            (-1, -1, 2),
            (3, -2, 0.5),
            (4, 2, -1.5),
            (-2, 1, -2),
            (0, 4, 1),
        ]
        sphere = MeshData.sphere(rows=10, cols=20)
        # Some pyqtgraph versions don't provide MeshData.cube(); create a simple cube mesh if missing.
        if hasattr(MeshData, "cube"):
            cube = MeshData.cube()
        else:
            import numpy as _np

            verts = _np.array(
                [
                    [-1, -1, -1],
                    [1, -1, -1],
                    [1, 1, -1],
                    [-1, 1, -1],
                    [-1, -1, 1],
                    [1, -1, 1],
                    [1, 1, 1],
                    [-1, 1, 1],
                ],
                dtype=float,
            )
            faces = _np.array(
                [
                    [0, 1, 2],
                    [0, 2, 3],
                    [4, 7, 6],
                    [4, 6, 5],
                    [0, 4, 5],
                    [0, 5, 1],
                    [1, 5, 6],
                    [1, 6, 2],
                    [2, 6, 7],
                    [2, 7, 3],
                    [3, 7, 4],
                    [3, 4, 0],
                ],
                dtype=int,
            )
            cube = MeshData(vertexes=verts * 0.5, faces=faces)
        for pos in sensor_positions:
            mesh = GLMeshItem(meshdata=sphere, color=(0.2, 0.6, 1.0, 0.8), smooth=True, shader="shaded")
            mesh.translate(*pos)
            mesh.scale(0.6, 0.6, 0.6)
            self.addItem(mesh)
            self.sensors.append(mesh)
            self.sensor_positions.append(pos)
        for pos in actuator_positions:
            mesh = GLMeshItem(meshdata=cube, color=(1.0, 0.5, 0.2, 0.8), smooth=False, shader="shaded")
            mesh.translate(*pos)
            mesh.scale(0.7, 0.7, 0.7)
            self.addItem(mesh)
            self.actuators.append(mesh)
            self.actuator_positions.append(pos)

    def update_state(self, sensor_vals, actuator_vals):
        """Scale and recolor items according to current values."""
        if not GL_AVAILABLE:
            return
        def color_from_val(v, base_color):
            intensity = np.clip(abs(v), 0.0, 1.0)
            return (
                np.clip(base_color[0] * (0.5 + intensity), 0, 1),
                np.clip(base_color[1] * (0.5 + intensity), 0, 1),
                np.clip(base_color[2] * (0.5 + intensity), 0, 1),
                0.9,
            )

        for mesh, pos, val in zip(self.sensors, self.sensor_positions, sensor_vals):
            mesh.resetTransform()
            mesh.translate(*pos)
            mesh.scale(0.6 + 0.4 * abs(val), 0.6 + 0.4 * abs(val), 0.6 + 0.4 * abs(val))
            mesh.setColor(color_from_val(val, (0.2, 0.6, 1.0)))

        for mesh, pos, val in zip(self.actuators, self.actuator_positions, actuator_vals):
            mesh.resetTransform()
            mesh.translate(*pos)
            mesh.scale(0.7 + 0.5 * abs(val), 0.7 + 0.5 * abs(val), 0.7 + 0.5 * abs(val))
            mesh.setColor(color_from_val(val, (1.0, 0.5, 0.2)))
