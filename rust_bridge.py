"""
Bridge utilities to call the Rust signal generator binary.

The Rust CLI is expected at backend_rust/target/release/rvsv_rust (or .exe on Windows).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict


class RustBridge:
    """Handles subprocess calls to the Rust backend."""

    def __init__(self, binary_path: str | None = None):
        default_name = "rvsv_rust.exe" if sys.platform.startswith("win") else "rvsv_rust"
        default_path = Path("backend_rust") / "target" / "release" / default_name
        self.binary_path = Path(binary_path) if binary_path else default_path

    def run_job(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call the Rust binary with provided parameters.
        params keys: mode, f1, a1, p1, f2, a2, p2, duration, dt
        """
        if not self.binary_path.exists():
            return self._mock_data(params, missing=True)
        cmd = [
            str(self.binary_path),
            "--mode",
            str(params.get("mode", "add")),
            "--f1",
            str(params.get("f1", 1.0)),
            "--a1",
            str(params.get("a1", 1.0)),
            "--p1",
            str(params.get("p1", 0.0)),
            "--f2",
            str(params.get("f2", 1.0)),
            "--a2",
            str(params.get("a2", 1.0)),
            "--p2",
            str(params.get("p2", 0.0)),
            "--duration",
            str(params.get("duration", 2.0)),
            "--dt",
            str(params.get("dt", 0.01)),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, check=True, text=True)
            return json.loads(result.stdout.strip())
        except FileNotFoundError:
            return self._mock_data(params, missing=True)
        except subprocess.CalledProcessError as exc:
            return self._mock_data(params, error=exc.stderr)
        except json.JSONDecodeError:
            return self._mock_data(params, error="Invalid JSON from Rust backend")

    def _mock_data(self, params: Dict[str, Any], missing: bool = False, error: str | None = None):
        """Return deterministic mock data if Rust binary is unavailable."""
        import numpy as np

        duration = float(params.get("duration", 2.0))
        dt = float(params.get("dt", 0.01))
        t = np.arange(0, duration, dt)
        x1 = np.sin(2 * np.pi * float(params.get("f1", 1.0)) * t)
        x2 = np.sin(2 * np.pi * float(params.get("f2", 1.0)) * t + float(params.get("p2", 0.0)))
        mode = params.get("mode", "add")
        if mode == "sub":
            y = x1 - x2
        elif mode == "mul":
            y = x1 * x2
        else:
            y = x1 + x2
        meta = "mock-data (missing binary)" if missing else f"mock-data ({error})"
        return {"time": t.tolist(), "x1": x1.tolist(), "x2": x2.tolist(), "y": y.tolist(), "meta": meta}
