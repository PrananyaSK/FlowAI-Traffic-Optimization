"""Video vehicle detection using a pretrained Ultralytics YOLO model."""
from pathlib import Path
import cv2
import pandas as pd
from ultralytics import YOLO

VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

def analyze_video(video_path: str, model_name: str = "yolo11n.pt",
                  confidence: float = 0.35, max_frames: int = 900):
    """Analyze up to max_frames and return annotated preview plus per-frame counts.

    The first run downloads model weights if not cached. Use only videos you are
    authorized to process. Detection counts are estimates, not official traffic counts.
    """
    model = YOLO(model_name)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    rows, preview = [], None
    frame_no = 0
    while frame_no < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        frame_no += 1
        result = model.track(frame, persist=True, verbose=False, conf=confidence,
                             classes=list(VEHICLE_CLASSES.keys()))[0]
        counts = {name: 0 for name in VEHICLE_CLASSES.values()}
        if result.boxes is not None:
            for cls in result.boxes.cls.tolist():
                label = VEHICLE_CLASSES.get(int(cls))
                if label:
                    counts[label] += 1
        rows.append({"frame": frame_no, **counts, "total_vehicles": sum(counts.values())})
        if frame_no % 3 == 0 or preview is None:
            preview = result.plot()
    cap.release()
    if preview is not None:
        preview = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
    return pd.DataFrame(rows), preview
