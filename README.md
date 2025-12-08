# Sistem Terintegrasi Instrumentasi & Simulasi Sinyal

Aplikasi desktop (PySide6 + pyqtgraph) untuk simulasi multi-sensor/multi-aktuator dengan analisis stabilitas, visualisasi 3D, dan generator sinyal berbasis Rust.

## Ringkasan Fitur
- 6 sensor + 6 aktuator dengan slider input fisik dan override; matriks kopling linier `v = C * y`.
- Plot domain waktu dan FFT real-time; ekspor CSV buffer.
- Tab Stabilitas: analisis s/z-domain via `control`, Bode magnitudo/fase, peta pole-zero, margin gain/fase, ekspor laporan.
- Tab 3D: penempatan sensor/aktuator menggunakan `pyqtgraph.opengl`; skala dan warna berubah sesuai amplitudo.
- Tab Rust: generator dua sinyal (add/sub/mul) dihitung oleh binary Rust; Python parse JSON lalu plot `x1, x2, y`.

## Kebutuhan
- Python 3.10+
- PySide6, pyqtgraph, numpy, scipy, control
- Untuk 3D: `pyqtgraph[opengl]` dan driver OpenGL yang berfungsi
- Toolchain Rust (untuk build backend)

Instal dependensi Python:
```bash
pip install PySide6 pyqtgraph numpy scipy control
# opsional untuk 3D
pip install "pyqtgraph[opengl]"
```

## Build backend Rust
```bash
cd backend_rust
cargo build --release
# binary: backend_rust/target/release/rvsv_rust (rvsv_rust.exe di Windows)
```

## Menjalankan Aplikasi
```bash
python main.py
```

## Tab & Cara Pakai
- **Instrumentation System**: slider sensor/aktuator, plot waktu/frekuensi, tabel kopling, ekspor CSV; tampilan 3D jika OpenGL tersedia.
- **Stability Analysis**: pilih kanal (sensor/aktuator), jalankan Bode/pole-zero/margin; ekspor laporan teks (gain/phase margin, poles/zeros).
- **Signal Generator (Rust)**: atur f/A/fase dua sinyal, pilih operasi (add/sub/mul), jalankan Rust; plot `x1, x2, y`.

### Catatan Analisis Stabilitas
- Model kanal: \(G(s) = \frac{K}{\tau s + 1}\), didiskritisasi ZOH ke \(G(z)\).
- Bode menampilkan magnitudo (dB) dan fase (deg); peta pole-zero memakai lokasi s-plane.
- Laporan berisi pole/zero (kontinu/discret) serta margin gain/fase dengan frekuensi crossover.
- Jika `control` tidak ada, UI menampilkan pesan kesalahan ringan, tidak crash.

### Catatan Tampilan 3D
- Memakai `pyqtgraph.opengl` (GLViewWidget). Sensor = bola, aktuator = kubus dengan koordinat tetap.
- Warna & skala mengikuti amplitudo sinyal (nilai absolut dibatasi 0..1).
- Jika OpenGL tidak tersedia, muncul pesan placeholder.

### Catatan Generator Sinyal Rust
- Arg CLI: `--mode [add|sub|mul] --f1 --a1 --p1 --f2 --a2 --p2 --duration --dt`
- Output JSON `{time, x1, x2, y}`; Python mem-parse dan mem-plot.
- `rust_bridge.py` memberi data mock deterministik jika binary hilang/error supaya UI tetap responsif.

## Struktur Proyek
- `main.py` — GUI utama, loop simulasi, tab, ekspor CSV.
- `sensor_models.py` — model sensor dan default param.
- `actuator_models.py` — model aktuator dan default param.
- `system_model.py` — manajer kopling, buffer, ekspor CSV.
- `signal_utils.py` — helper FFT.
- `stability_analysis.py` — Bode/pole-zero/margin/report berbasis `control`.
- `visualizer_3d.py` — tampilan OpenGL sensor/aktuator.
- `rust_bridge.py` — jembatan subprocess ke binary Rust (fallback mock).
- `backend_rust/src/main.rs` — CLI Rust keluaran JSON (time, x1, x2, y).

## Mengembangkan Lebih Lanjut
- Ubah matriks kopling di `system_model.py`.
- Tuning gain/time_constant/noise/saturasi pada parameter sensor/aktuator.
- Ganti logika matematika Rust sesuai kebutuhan, tetap patuhi kontrak JSON.
- Tambah filter atau kontrol lanjutan di `CouplingManager.step`.
