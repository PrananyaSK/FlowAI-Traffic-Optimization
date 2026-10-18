# FlowAI — AI-Powered Traffic Flow Optimization System

A Windows-friendly academic major-project prototype with a dark Streamlit dashboard, YOLO vehicle detection, adaptive signal timing recommendations, repeatable multi-junction simulation, CSV exports, and a FastAPI endpoint.

## What is included

- **Live Camera:** webcam stream with YOLO detection for cars, motorcycles, buses, and trucks; live telemetry and CSV export.
- **Video Analysis:** upload MP4/MOV/AVI/MKV traffic footage, inspect an annotated frame, chart per-frame detections, and export results to CSV.
- **Signal Optimizer:** enter demand for North/East/South/West and receive bounded green-time recommendations. The optimizer respects feasible cycle-time bounds.
- **Network Simulation:** run a reproducible synthetic comparison of fixed-time and adaptive signal policies over multiple junctions.
- **FastAPI:** `/health`, `/optimize`, and interactive docs at `/docs`.
- **Tests:** unit tests for optimizer bounds, cycle totals, invalid demand, and congestion categories.

## Requirements

- Windows 10/11, 64-bit
- **Python 3.11 (recommended)**
- Internet connection for installing packages and the first download of YOLO model weights (`yolo11n.pt`)
- Webcam and browser permission for Live Camera

## Quick setup (micro-steps)

1. Download and extract the ZIP completely. Do not run the app from inside the ZIP preview.
2. Open the extracted `AI_Traffic_Optimization_Advanced` folder.
3. Double-click `INSTALL_WINDOWS.bat` and wait until it says setup is complete. This creates `.venv` and installs dependencies.
4. Double-click `RUN_DASHBOARD.bat`.
5. Open the local URL printed in the terminal, normally `http://localhost:8501`.
6. Choose **Live Camera** and press **START**, or choose **Video Analysis** and upload a video.

If double-clicking is blocked, use VS Code → Terminal → New Terminal:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run dashboard/app.py
```

If PowerShell blocks activation, run without activation:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

## Start the API (optional)

1. Keep the dashboard terminal open.
2. Double-click `RUN_API.bat` (or use a second terminal):

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- API health: `http://127.0.0.1:8000/health`
- Swagger docs: `http://127.0.0.1:8000/docs`
- `POST http://127.0.0.1:8000/optimize` body:

```json
{
  "demand": {"North": 18, "East": 7, "South": 12, "West": 4}
}
```

## Run tests

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## How to evaluate output

- **Optimizer:** results depend on the demand values, min/max green, and cycle length entered. The cycle is clamped to feasible min/max bounds if the requested cycle cannot fit all phases.
- **Video/live detection:** outputs are model predictions, not guaranteed ground truth. A vehicle may be detected repeatedly across frames; frame-level detections must not be reported as unique vehicles.
- **Simulation:** uses synthetic arrivals and a simplified queue/service model. It is suitable for demonstrating a comparison, not a validated model of a real intersection.

## Important limitations and responsible use

This is an educational prototype. It does **not** control real traffic lights, perform certified safety checks, or automatically associate live detections with individual road lanes. Live-camera counts are not automatically fed into the signal optimizer; the optimizer uses the approach-demand values you enter. Do not connect it to real traffic infrastructure without authorization, fail-safe design, and professional traffic-engineering validation.

The YOLO model weights are downloaded by Ultralytics on first use and are not included in the ZIP. CPU inference may be slow on older computers. Browser webcam access generally works on `localhost`; remote access may require HTTPS and additional WebRTC network configuration.
