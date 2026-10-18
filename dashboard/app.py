import os
import threading
import time
from collections import deque

import cv2
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration, VideoProcessorBase

from traffic.optimizer import choose_green_times, congestion_level
from traffic.simulation import run_simulation, summarize

st.set_page_config(
    page_title="FlowAI | Intelligent Traffic Control",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { color-scheme: dark; }
.stApp { background: #0b1220; color: #e7eef8; }
[data-testid="stSidebar"] { background: #101a2b; border-right: 1px solid #24334a; }
.block-container { padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1500px; }
h1, h2, h3 { color: #f2f7ff !important; letter-spacing: -0.02em; }
p, label, .stCaption { color: #aab9ce; }
.hero { padding:1.35rem 1.5rem; border-radius:18px; background:linear-gradient(115deg,#122a43 0%,#12384a 52%,#17304c 100%); border:1px solid #28506a; margin-bottom:1.2rem; }
.hero-kicker { color:#65e5c0; font-size:.78rem; font-weight:800; letter-spacing:.16em; text-transform:uppercase; }
.hero h1 { margin:.35rem 0; font-size:2.1rem; }
.hero p { margin:0; color:#b9cde0; max-width:850px; }
.metric-card { background:#111d2f; border:1px solid #253750; border-radius:15px; padding:1rem 1.1rem; min-height:110px; }
.metric-label { color:#8fa5bf; font-size:.78rem; text-transform:uppercase; letter-spacing:.08em; }
.metric-value { color:#f2f7ff; font-size:1.8rem; font-weight:750; margin-top:.35rem; }
.metric-note { color:#61dfb8; font-size:.78rem; margin-top:.15rem; }
.section-card { background:#101b2c; border:1px solid #253750; border-radius:16px; padding:1rem 1.1rem; }
.status-dot { color:#62e6b7; font-weight:800; }
.stButton > button { border-radius:10px; font-weight:700; min-height:2.7rem; }
.small-muted { color:#8fa5bf; font-size:.82rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="hero-kicker">Intelligent Mobility • Live Operations</div>
  <h1>FlowAI Traffic Command Center</h1>
  <p>Live camera vehicle detection, adaptive signal recommendations and multi-junction performance analytics in one workspace.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🚦 FlowAI")
    st.caption("TRAFFIC INTELLIGENCE PLATFORM")
    page = st.radio("Workspace", ["Live Camera", "Video Analysis", "Signal Optimizer", "Network Simulation", "About & Setup"], label_visibility="collapsed")
    st.divider()
    st.markdown("**System status**")
    st.markdown('<span class="status-dot">●</span> Dashboard online', unsafe_allow_html=True)
    st.caption("Camera access requires browser permission and HTTPS or localhost.")
    st.divider()
    st.caption("Academic prototype. It does not control physical traffic signals.")

class LiveVehicleProcessor(VideoProcessorBase):
    def __init__(self):
        self.lock = threading.Lock()
        self.model = None
        self.error = None
        self.latest = {"cars": 0, "motorcycles": 0, "buses": 0, "trucks": 0, "total": 0, "fps": 0.0}
        self.total_frames = 0
        self.started_at = time.time()
        self.history = deque(maxlen=120)
        self.last_error_log = 0.0

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        try:
            from ultralytics import YOLO
            if self.model is None:
                self.model = YOLO("yolo11n.pt")
            h, w = image.shape[:2]
            if w > 960:
                scale = 960 / w
                image = cv2.resize(image, (int(w * scale), int(h * scale)))
            result = self.model.predict(
                image, verbose=False, conf=0.30, imgsz=640,
                classes=[2, 3, 5, 7], device="cpu"
            )[0]
            counts = {2: 0, 3: 0, 5: 0, 7: 0}
            if result.boxes is not None:
                for cls in result.boxes.cls.tolist():
                    counts[int(cls)] = counts.get(int(cls), 0) + 1
            annotated = result.plot()
            self.total_frames += 1
            elapsed = max(time.time() - self.started_at, 0.001)
            snapshot = {
                "cars": counts.get(2, 0),
                "motorcycles": counts.get(3, 0),
                "buses": counts.get(5, 0),
                "trucks": counts.get(7, 0),
                "total": sum(counts.values()),
                "fps": round(self.total_frames / elapsed, 1),
            }
            with self.lock:
                self.latest = snapshot
                self.error = None
                self.history.append({"time": time.strftime("%H:%M:%S"), **snapshot})
            return type(frame).from_ndarray(annotated, format="bgr24")
        except Exception as exc:
            with self.lock:
                self.error = f"{type(exc).__name__}: {exc}"
            cv2.putText(image, "AI inference error - check telemetry panel", (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return type(frame).from_ndarray(image, format="bgr24")

    def get_stats(self):
        with self.lock:
            return dict(self.latest), list(self.history), self.error

def metric(label, value, note="Live estimate"):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

if page == "Live Camera":
    st.subheader("Live camera intelligence")
    st.markdown('<div class="small-muted">Allow camera access when prompted. Point the camera at visible vehicles or test with a road video displayed on another screen.</div>', unsafe_allow_html=True)
    left, right = st.columns([1.55, 1], gap="large")
    with left:
        st.markdown("#### Camera feed")
        ctx = webrtc_streamer(
            key="flowai-live-camera",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=LiveVehicleProcessor,
            media_stream_constraints={"video": True, "audio": False},
            rtc_configuration=RTCConfiguration(
                {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
            ),
            async_processing=True,
        )
        st.caption("Click START to enable the webcam. Click STOP to release it.")
    with right:
        st.markdown("#### Detection telemetry")
        processor = ctx.video_processor if ctx else None
        if processor is not None:
            stats, history, error = processor.get_stats()
            c1, c2 = st.columns(2)
            with c1:
                metric("Vehicles in current frame", stats["total"])
                metric("Cars", stats["cars"])
            with c2:
                metric("Processing FPS", stats["fps"])
                metric("Motorcycles", stats["motorcycles"])
            c3, c4 = st.columns(2)
            with c3:
                metric("Buses", stats["buses"])
            with c4:
                metric("Trucks", stats["trucks"])
            if error:
                st.error("AI detection error: " + error)
                st.info("If this mentions a model download, check internet access. If it mentions torch or ultralytics, install the missing package in this virtual environment.")
            if history:
                hist_df = pd.DataFrame(history)
                st.plotly_chart(px.line(hist_df, x="time", y="total", title="Recent frame detections",
                                        markers=False, template="plotly_dark"), use_container_width=True)
                st.download_button("Export live telemetry CSV", hist_df.to_csv(index=False).encode(),
                                   "flowai_live_telemetry.csv", "text/csv")
            else:
                st.info("Camera processor connected. Waiting for the first analyzed frame...")
        else:
            st.info("Click START in the camera panel to populate live metrics.")
            metric("Vehicles in current frame", "—", "Waiting for camera")
            metric("Processing FPS", "—", "Waiting for camera")
    # Trigger Streamlit reruns while the webcam is active so shared stats are read again.
    if ctx.state.playing:
        st_autorefresh(interval=1000, key="flowai_live_telemetry_refresh")
    st.markdown("#### How to interpret the live feed")
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="section-card"><b>01 · Detect</b><p class="small-muted">YOLO identifies common vehicle classes in each camera frame.</p></div>', unsafe_allow_html=True)
    with b:
        st.markdown('<div class="section-card"><b>02 · Measure</b><p class="small-muted">Counts are from the current frame; the same vehicle can appear again in later frames.</p></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="section-card"><b>03 · Optimize</b><p class="small-muted">Use approach demand in Signal Optimizer to compare timing recommendations.</p></div>', unsafe_allow_html=True)

elif page == "Video Analysis":
    st.subheader("Traffic video analysis")
    st.write("Upload a traffic clip to run YOLO vehicle detection and export frame-level counts. The same vehicle may appear in multiple frames.")
    uploaded = st.file_uploader("Choose a video", type=["mp4", "mov", "avi", "mkv"])
    v1, v2 = st.columns(2)
    confidence = v1.slider("Detection confidence", 0.10, 0.90, 0.35, 0.05)
    max_frames = v2.slider("Maximum frames to analyze", 30, 1800, 300, 30)
    if uploaded is not None:
        st.video(uploaded)
        if st.button("Analyze uploaded video", type="primary"):
            import tempfile
            from pathlib import Path
            from traffic.video_analyzer import analyze_video
            suffix = Path(uploaded.name).suffix or ".mp4"
            tmp_name = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded.getbuffer())
                    tmp_name = tmp.name
                with st.spinner("Loading YOLO and analyzing frames. First run may download model weights..."):
                    rows, preview = analyze_video(tmp_name, confidence=confidence, max_frames=max_frames)
                st.session_state["video_analysis_rows"] = rows
                st.session_state["video_analysis_preview"] = preview
                st.session_state["video_analysis_name"] = uploaded.name
            except Exception as exc:
                st.error(f"Video analysis failed: {type(exc).__name__}: {exc}")
                st.info("Check internet access for first-time model download and confirm the uploaded file is a valid video.")
            finally:
                if tmp_name:
                    try: os.unlink(tmp_name)
                    except OSError: pass
    if "video_analysis_rows" in st.session_state:
        rows = st.session_state["video_analysis_rows"]
        preview = st.session_state.get("video_analysis_preview")
        if preview is not None:
            st.markdown("#### Annotated sample frame")
            st.image(preview, use_container_width=True)
        if not rows.empty:
            total = int(rows["total_vehicles"].sum())
            peak = int(rows["total_vehicles"].max())
            m1, m2, m3 = st.columns(3)
            with m1: metric("Frames analyzed", len(rows), "Processed video frames")
            with m2: metric("Vehicle detections", total, "Frame-level detections, not unique vehicles")
            with m3: metric("Peak vehicles in frame", peak, "Highest single-frame count")
            st.plotly_chart(px.line(rows, x="frame", y="total_vehicles", title="Vehicles detected per analyzed frame", template="plotly_dark"), use_container_width=True)
            st.dataframe(rows.head(100), use_container_width=True, hide_index=True)
            st.download_button("Download frame counts CSV", rows.to_csv(index=False).encode("utf-8"), "flowai_video_analysis.csv", "text/csv")

elif page == "Signal Optimizer":
    st.subheader("Adaptive signal timing")
    st.write("Enter vehicle demand estimates for each approach. FlowAI allocates green time within configured bounds.")
    c1, c2, c3, c4 = st.columns(4)
    defaults = {"North": 18, "East": 7, "South": 12, "West": 4}
    demand = {}
    for col, name in zip([c1, c2, c3, c4], defaults):
        with col:
            demand[name] = st.number_input(f"{name} approach", min_value=0, max_value=100, value=defaults[name], step=1)
    x, y, z = st.columns(3)
    with x: min_green = st.slider("Minimum green (sec)", 5, 20, 10)
    with y: max_green = st.slider("Maximum green (sec)", 20, 60, 45)
    with z: cycle = st.slider("Target cycle (sec)", 60, 180, 100)
    if max_green < min_green:
        st.warning("Maximum green must be greater than or equal to minimum green.")
    if st.button("Calculate adaptive timings", type="primary"):
        if max_green < min_green:
            st.error("Please set maximum green to at least the minimum green.")
            st.stop()
        allocation = choose_green_times(demand, min_green=min_green, max_green=max_green, total_cycle=cycle)
        result = pd.DataFrame([{"Approach": k, "Demand": demand[k], "Congestion": congestion_level(demand[k]), "Suggested green (sec)": v} for k, v in allocation.items()])
        st.session_state["opt_result"] = result
    if "opt_result" in st.session_state:
        result = st.session_state["opt_result"]
        st.dataframe(result, use_container_width=True, hide_index=True)
        st.plotly_chart(px.bar(result, x="Approach", y="Suggested green (sec)", color="Congestion", title="Recommended green time by approach", template="plotly_dark"), use_container_width=True)
        st.download_button("Download timing plan", result.to_csv(index=False).encode(), "adaptive_signal_plan.csv", "text/csv")

elif page == "Network Simulation":
    st.subheader("Network performance lab")
    st.write("Run a repeatable synthetic simulation to compare fixed-time and adaptive policies across intersections.")
    a, b, c = st.columns(3)
    minutes = a.slider("Duration (minutes)", 10, 120, 30, 5)
    junctions = b.slider("Intersections", 1, 8, 4)
    seed = c.number_input("Random seed", 1, 9999, 7)
    if st.button("Run network simulation", type="primary"):
        with st.spinner("Simulating demand and queue behaviour..."):
            st.session_state["sim_results"] = run_simulation(minutes, int(seed), junctions)
    if "sim_results" in st.session_state:
        data = st.session_state["sim_results"]
        summary = summarize(data)
        st.dataframe(summary, use_container_width=True, hide_index=True)
        x, y = st.columns(2)
        with x:
            queue = data.groupby(["minute", "policy"], as_index=False)["queue"].mean()
            st.plotly_chart(px.line(queue, x="minute", y="queue", color="policy", title="Mean queue by minute", template="plotly_dark"), use_container_width=True)
        with y:
            st.plotly_chart(px.bar(summary, x="policy", y="avg_wait_seconds", title="Estimated mean waiting time (seconds)", template="plotly_dark"), use_container_width=True)
        served = data.groupby(["intersection", "policy"], as_index=False).agg(served=("vehicles_served", "sum"))
        st.plotly_chart(px.bar(served, x="intersection", y="served", color="policy", barmode="group", title="Estimated vehicles served by junction", template="plotly_dark"), use_container_width=True)
        st.download_button("Export simulation CSV", data.to_csv(index=False).encode(), "flowai_simulation_results.csv", "text/csv")

else:
    st.subheader("Project overview & setup")
    st.markdown("""
**FlowAI** is an academic prototype combining computer vision and traffic-control experimentation.

**Camera requirements**
- Use a modern browser and grant camera permission.
- Open on `localhost` for local camera access.
- Internet may be needed to download `yolo11n.pt` on first inference.
- CPU inference can be slow on older laptops.

**Known limitations**
- Live counts are detections per frame, not unique vehicle counts.
- The optimizer uses supplied demand values; it does not yet map live detections into lane-specific signal phases.
- The simulator is synthetic and not calibrated to real roads.
- Do not connect this prototype to physical traffic lights without authorization and certified safety controls.
""")
