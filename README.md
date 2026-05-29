# AI Driver Drowsiness & Distraction Monitoring System

An advanced, real-time Computer Vision system designed to monitor driver state, detect fatigue (blinking, yawning, head tilts/nods), flag distractions (mobile phone usage, lane departures), play non-blocking audio alerts, and visualize live analytics on a futuristic dark-mode dashboard.

---

## 💡 Why We Built It (The Motivation)

Driver fatigue, drowsiness, and inattentiveness are among the leading causes of severe road accidents worldwide. 
* According to the **World Health Organization (WHO)** and global transport authorities, over 20% of commercial vehicle accidents are directly linked to driver exhaustion.
* Traditional safety systems only react *after* a collision or lanes are crossed.
* This project was built to provide a **proactive, edge-intelligent safety shield** that monitors driver state directly and alerts them *before* an accident happens.

### 🛡️ How It Helps (The Impact)
* **Pre-empts Collisions**: By detecting micro-sleeps (prolonged eye closures) and yawning sequences, the system triggers alerts before the driver loses control.
* **Reduces Distraction**: Detects when a driver looks down at their phone or shifts focus away from the windshield for more than 3 seconds.
* **Low-Cost Fleet Deployment**: Works on a standard low-cost webcam and runs efficiently on local hardware without requiring expensive cloud GPUs.
* **Telemetry Audits**: Logs all distraction and drowsiness events locally, allowing fleet managers to audit driver safety history.

---

## 🚀 Key Features

### 🌌 1. Cyberpunk HUD Overlay (Visual UI)
* **Neon Landmarks**: Draws glowing contours around the driver's eyelids and mouth to verify tracking.
* **Targeting Corners**: Places futuristic corner brackets around the driver's face, displaying live indicators: `EAR` (Eye Aspect Ratio), `MOUTH` (yawn gap), and `TILT` (head roll angle).
* **Crimson Vignette Warnings**: Flashes a pulsing red border overlay across the screen when danger or distractions are detected.

### 📊 2. Live Telemetry Sidebar
* **Dynamic Badges**: Color-coded status alerts (Safe Green, Warning Yellow, Danger Red, No Driver Gray).
* **Fatigue Level Gauge**: Shows the live fatigue percentage score based on aggregate factors.
* **Event Counters**: Keeps track of total blinks, yawns, and head tilts during the drive.

### 📈 3. Real-Time Embedded Graph
* An integrated line chart rendering directly onto the OpenCV window showing a scrolling history of the driver's fatigue score over the last 100 frames.

### 🔊 4. Asynchronous Speech Alerts
* Uses a separate background thread to play alarm sirens and speak alert messages (e.g., *"Warning. Eyes closed detected"*). This ensures the video processing thread never freezes during audio playback.

---

## 🛠️ How It Works (The Engine)

```
[Camera Feed] ───► [Video Processing Thread] ───► [OpenCV Canvas Render (1200x720)]
                        │             │
                 (Face Mesh)       (YOLOv8)
                        ▼             ▼
             MediaPipe Landmarks  Cell Phone BBoxes
                        │
      ┌─────────────────┴─────────────────┐
      ▼                                   ▼
[Eye Aspect Ratio (EAR)]        [Head Pitch/Roll Ratio]
- Eye closure duration         - Front/Back nods (pitch)
- Yawning distance             - Left/Right tilts (roll)
```

1. **Facial Feature Extraction**: Uses a custom-pinned version of **MediaPipe Face Mesh** (`0.10.14`) to parse 3D facial contours.
2. **Scale-Invariant Pitch Math**: Calculates head tilts forward (looking down) and backward (looking up) using a robust ratio comparing lower face height to total face height.
   $$\text{Pitch Ratio} = \frac{\text{chin.y} - \text{nose.y}}{\text{chin.y} - \text{forehead.y}}$$
   - Looks Down: Ratio $< 0.36$
   - Looks Up: Ratio $> 0.62$
3. **Confirmation Timers**: Glances are ignored; warnings for eye closures, yawns, looking down, and looking up are only triggered if the state continues for more than 3 seconds.
4. **Phone Detection**: Runs a local **YOLOv8** nano network (`yolov8n.pt`) to detect cell phones in the frame.
5. **Lane Detection**: Employs Canny Edge and Hough Line transforms on the lower portion of the frame to verify lanes.

---

## 📂 Project Architecture

* **[main.py](file:///c:/Users/samee/OneDrive/Desktop/Major%20Projects/Drowsiness-Detection-Project/main.py)**: The central controller coordinates webcam streaming, HUD rendering, widgets, and the main thread.
* **[fatigue_analyzer.py](file:///c:/Users/samee/OneDrive/Desktop/Major%20Projects/Drowsiness-Detection-Project/fatigue_analyzer.py)**: Tracks blinks, yawns, and tilts using edge-trigger transitions (prevents frame double-counting).
* **[fatigue_predictor.py](file:///c:/Users/samee/OneDrive/Desktop/Major%20Projects/Drowsiness-Detection-Project/fatigue_predictor.py)**: Performs logical evaluations to predict upcoming exhaustion risks.
* **[alert_system.py](file:///c:/Users/samee/OneDrive/Desktop/Major%20Projects/Drowsiness-Detection-Project/alert_system.py)**: Offloads pygame audio mixer and SAPI5/pyttsx3 text-to-speech to background threads.
* **[phone_detector.py](file:///c:/Users/samee/OneDrive/Desktop/Major%20Projects/Drowsiness-Detection-Project/phone_detector.py)**: Runs local YOLOv8 object detection.
* **[lane_detector.py](file:///c:/Users/samee/OneDrive/Desktop/Major%20Projects/Drowsiness-Detection-Project/lane_detector.py)**: Processes edge detection for road markings.

---

## ⚙️ Quick Start Installation

1. **Clone or navigate** to the project directory:
   ```powershell
   cd "C:\Users\samee\OneDrive\Desktop\Major Projects\Drowsiness-Detection-Project"
   ```

2. **Launch the launcher script**:
   ```powershell
   .\run.bat
   ```
   *The launcher batch file will automatically locate Python 3.10, set up a virtual environment (`.venv`), install all requirements, and boot up the system.*