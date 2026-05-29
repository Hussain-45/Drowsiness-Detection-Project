import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import cv2
import mediapipe as mp
import numpy as np
import time
import matplotlib.pyplot as plt

from fatigue_analyzer import FatigueAnalyzer
from fatigue_predictor import FatiguePredictor
from phone_detector import PhoneDetector
from lane_detector import LaneDetector
from alert_system import AlertSystem
from logger import log_event


mp_face_mesh = mp.solutions.face_mesh

cap = cv2.VideoCapture(0)

fatigue = FatigueAnalyzer()
predictor = FatiguePredictor()
phone_detector = PhoneDetector()
lane_detector = LaneDetector()
alerts = AlertSystem()


LEFT_EYE=[33,160,158,133,153,144]
RIGHT_EYE=[362,385,387,263,373,380]
MOUTH=[13,14]

NOSE=1
CHIN=152
LEFT_EAR=234
RIGHT_EAR=454
FOREHEAD=10


EYE_THRESHOLD=0.20
YAWN_THRESHOLD=0.06

CONFIRM_TIME=3
VOICE_COOLDOWN=5


last_voice_alert=0

eyes_start=None
yawn_start=None
tilt_start=None
down_start=None
up_start=None


fatigue_history=[]


def distance(p1,p2):
    return np.linalg.norm(np.array([p1.x,p1.y])-np.array([p2.x,p2.y]))


def eye_ratio(landmarks,eye):

    p1,p2,p3,p4,p5,p6=[landmarks[i] for i in eye]

    vertical=distance(p2,p6)+distance(p3,p5)
    horizontal=distance(p1,p4)

    return vertical/(2.0*horizontal)


def head_tilt_angle(landmarks):

    left=landmarks[LEFT_EAR]
    right=landmarks[RIGHT_EAR]

    dx=right.x-left.x
    dy=right.y-left.y

    return np.degrees(np.arctan2(dy,dx))


cv2.namedWindow("AI Driver Monitoring System", cv2.WINDOW_NORMAL)


with mp_face_mesh.FaceMesh(refine_landmarks=True) as face_mesh:

    while cap.isOpened():

        ret,frame=cap.read()

        if not ret:
            break

        frame=cv2.flip(frame,1)

        phone_detected=phone_detector.detect_phone(frame)
        lane_departure=lane_detector.detect_lane_departure(frame)

        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)

        results=face_mesh.process(rgb)

        status="No Face"
        score=0
        head_down=False
        head_up=False

        if results.multi_face_landmarks:

            landmarks=results.multi_face_landmarks[0].landmark

            ear=(eye_ratio(landmarks,LEFT_EYE)+eye_ratio(landmarks,RIGHT_EYE))/2
            eyes_closed=ear<EYE_THRESHOLD

            mouth_open=distance(landmarks[MOUTH[0]],landmarks[MOUTH[1]])
            yawn=mouth_open>YAWN_THRESHOLD

            angle=head_tilt_angle(landmarks)
            head_tilt=abs(angle)>20

            forehead=landmarks[FOREHEAD]
            nose=landmarks[NOSE]
            chin=landmarks[CHIN]

            # Scale-invariant head pitch (forward/backward tilt) calculation
            total_face_h = chin.y - forehead.y
            pitch_ratio = (chin.y - nose.y) / total_face_h if total_face_h > 0 else 0.5

            head_down = pitch_ratio < 0.36
            head_up = pitch_ratio > 0.62

            fatigue.update(eyes_closed,yawn,head_tilt,head_down or head_up)

            score=fatigue.fatigue_score()

            fatigue_history.append(score)

            if len(fatigue_history)>200:
                fatigue_history.pop(0)

            fatigue_predicted = predictor.predict(
                fatigue.blink_count,
                fatigue.yawn_count,
                fatigue.head_tilt_count
            )

            current=time.time()

            def trigger_alert(message):

                global last_voice_alert

                if current-last_voice_alert>VOICE_COOLDOWN:

                    alerts.speak(message)
                    alerts.alarm()
                    log_event(message)

                    last_voice_alert=current


            if eyes_closed:
                if eyes_start is None:
                    eyes_start=current
                if current-eyes_start>CONFIRM_TIME:
                    trigger_alert("Eyes closed detected")
            else:
                eyes_start=None


            if yawn:
                if yawn_start is None:
                    yawn_start=current
                if current-yawn_start>CONFIRM_TIME:
                    trigger_alert("Yawning detected")
            else:
                yawn_start=None


            if head_tilt:
                if tilt_start is None:
                    tilt_start=current
                if current-tilt_start>CONFIRM_TIME:
                    trigger_alert("Head tilt detected")
            else:
                tilt_start=None


            if head_down:
                if down_start is None:
                    down_start = current
                if current - down_start > CONFIRM_TIME:
                    trigger_alert("Driver looking down")
            else:
                down_start = None

            if head_up:
                if up_start is None:
                    up_start = current
                if current - up_start > CONFIRM_TIME:
                    trigger_alert("Driver looking up")
            else:
                up_start = None

            if phone_detected:
                trigger_alert("Mobile phone detected")

            if lane_departure:
                trigger_alert("Lane departure detected")

            if fatigue_predicted:
                trigger_alert("Fatigue risk detected")


            if score>70:
                status="DROWSY"

            elif score>40:
                status="WARNING"

            else:
                status="ALERT"


        # ---------- FUTURISTIC DASHBOARD UI ---------- #

        win_w = 1200
        win_h = 720

        # Design colors (BGR)
        BG_COLOR = (25, 15, 11)        # Deep Slate Blue/Navy
        PANEL_COLOR = (59, 41, 30)     # Muted Slate Panel
        COLOR_ALERT = (113, 204, 46)   # Emerald Green
        COLOR_WARNING = (15, 196, 241)  # Amber Yellow
        COLOR_DANGER = (68, 68, 239)   # Crimson Red
        HUD_COLOR = (255, 230, 0)      # Cyberpunk Gold

        canvas = np.zeros((win_h, win_w, 3), dtype=np.uint8)
        canvas[:, :] = BG_COLOR

        # 1. Header Title
        cv2.rectangle(canvas, (0, 0), (win_w, 80), (15, 10, 8), -1)
        cv2.line(canvas, (0, 80), (win_w, 80), (80, 80, 80), 1)
        cv2.putText(canvas,
                    "AI DRIVER MONITORING SYSTEM",
                    (win_w // 2 - 250, 50),
                    cv2.FONT_HERSHEY_TRIPLEX,
                    0.9,
                    (255, 230, 0),
                    2,
                    cv2.LINE_AA)

        # 2. Camera Frame Resize and Placement (Max Area 760x580)
        frame_h, frame_w = frame.shape[:2]
        scale = min(760 / frame_w, 580 / frame_h)
        new_w = int(frame_w * scale)
        new_h = int(frame_h * scale)
        resized = cv2.resize(frame, (new_w, new_h))

        x_offset = 20 + (760 - new_w) // 2
        y_offset = 100 + (580 - new_h) // 2

        # Draw frame into canvas
        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

        # Face Mesh HUD overlays
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            def get_pt(idx):
                pt = landmarks[idx]
                return (int(pt.x * new_w) + x_offset, int(pt.y * new_h) + y_offset)

            # Eyelid neon contours
            left_pts = np.array([get_pt(i) for i in LEFT_EYE], dtype=np.int32)
            right_pts = np.array([get_pt(i) for i in RIGHT_EYE], dtype=np.int32)
            cv2.polylines(canvas, [left_pts], isClosed=True, color=HUD_COLOR, thickness=1, lineType=cv2.LINE_AA)
            cv2.polylines(canvas, [right_pts], isClosed=True, color=HUD_COLOR, thickness=1, lineType=cv2.LINE_AA)

            # Mouth yawn tracking indicator line
            m_top = get_pt(MOUTH[0])
            m_bottom = get_pt(MOUTH[1])
            cv2.line(canvas, m_top, m_bottom, (0, 255, 255), 2, cv2.LINE_AA)
            cv2.circle(canvas, m_top, 3, (0, 165, 255), -1)
            cv2.circle(canvas, m_bottom, 3, (0, 165, 255), -1)

            # Face Tracking bounding brackets
            face_indices = LEFT_EYE + RIGHT_EYE + [NOSE, CHIN, LEFT_EAR, RIGHT_EAR]
            face_pts = [get_pt(i) for i in face_indices]
            xs = [p[0] for p in face_pts]
            ys = [p[1] for p in face_pts]
            min_x, max_x = min(xs) - 20, max(xs) + 20
            min_y, max_y = min(ys) - 30, max(ys) + 20

            length = 20
            # Top-Left Bracket
            cv2.line(canvas, (min_x, min_y), (min_x + length, min_y), HUD_COLOR, 2, cv2.LINE_AA)
            cv2.line(canvas, (min_x, min_y), (min_x, min_y + length), HUD_COLOR, 2, cv2.LINE_AA)
            # Top-Right Bracket
            cv2.line(canvas, (max_x, min_y), (max_x - length, min_y), HUD_COLOR, 2, cv2.LINE_AA)
            cv2.line(canvas, (max_x, min_y), (max_x, min_y + length), HUD_COLOR, 2, cv2.LINE_AA)
            # Bottom-Left Bracket
            cv2.line(canvas, (min_x, max_y), (min_x + length, max_y), HUD_COLOR, 2, cv2.LINE_AA)
            cv2.line(canvas, (min_x, max_y), (min_x, max_y - length), HUD_COLOR, 2, cv2.LINE_AA)
            # Bottom-Right Bracket
            cv2.line(canvas, (max_x, max_y), (max_x - length, max_y), HUD_COLOR, 2, cv2.LINE_AA)
            cv2.line(canvas, (max_x, max_y), (max_x, max_y - length), HUD_COLOR, 2, cv2.LINE_AA)

            # HUD Live Info
            cv2.putText(canvas,
                        f"TRACKING ACTIVE | EAR: {ear:.2f} | MOUTH: {mouth_open:.2f} | TILT: {angle:+.1f}",
                        (min_x, min_y - 12),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        HUD_COLOR,
                        1,
                        cv2.LINE_AA)

        # 3. Sidebar (Right Panel)
        cv2.rectangle(canvas, (800, 100), (1180, 680), PANEL_COLOR, -1)
        cv2.rectangle(canvas, (800, 100), (1180, 680), (80, 80, 80), 1)

        # Badge dynamic color
        if status == "DROWSY":
            badge_color = COLOR_DANGER
        elif status == "WARNING":
            badge_color = COLOR_WARNING
        elif status == "No Face":
            badge_color = (130, 130, 130)  # Gray for no driver detected
        else:
            badge_color = COLOR_ALERT

        # Driver Status Badge
        cv2.rectangle(canvas, (820, 120), (1160, 170), badge_color, -1)
        cv2.putText(canvas,
                    f"STATUS: {status}",
                    (840, 153),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.7,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA)

        # Fatigue Level Indicator
        cv2.putText(canvas,
                    f"FATIGUE LEVEL: {score}%",
                    (820, 205),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (220, 220, 220),
                    1,
                    cv2.LINE_AA)

        # Outer bar
        cv2.rectangle(canvas, (820, 220), (1160, 235), (70, 70, 70), -1)
        # Inner bar
        bar_fill = int((score / 100.0) * 340)
        cv2.rectangle(canvas, (820, 220), (820 + bar_fill, 235), badge_color, -1)

        # Telemetry stats
        y_tel = 275
        cv2.putText(canvas, "DRIVER TELEMETRY", (820, y_tel), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.line(canvas, (820, y_tel + 5), (1160, y_tel + 5), (80, 80, 80), 1)

        metrics = [
            ("Total Blinks", fatigue.blink_count),
            ("Total Yawns", fatigue.yawn_count),
            ("Total Head Tilts/Downs", fatigue.head_tilt_count),
            ("Phone Distraction", "YES" if phone_detected else "NO"),
            ("Lane Departure", "YES" if lane_departure else "NO")
        ]

        for i, (name, val) in enumerate(metrics):
            y_pos = y_tel + 35 + i * 25
            cv2.putText(canvas, f"{name}:", (820, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (190, 190, 190), 1, cv2.LINE_AA)

            # Colored alerting flags
            v_color = (255, 255, 255)
            if val == "YES":
                v_color = COLOR_DANGER
            elif val == "NO":
                v_color = COLOR_ALERT

            cv2.putText(canvas, f"{val}", (1060, y_pos), cv2.FONT_HERSHEY_DUPLEX, 0.48, v_color, 1, cv2.LINE_AA)

        # 4. Embedded Scrolling Graph
        cv2.putText(canvas, "FATIGUE HISTORY TIMELINE", (820, 445), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.line(canvas, (820, 450), (1160, 450), (80, 80, 80), 1)

        g_x, g_y = 820, 470
        g_w, g_h = 340, 180
        cv2.rectangle(canvas, (g_x, g_y), (g_x + g_w, g_y + g_h), (15, 10, 8), -1)
        cv2.rectangle(canvas, (g_x, g_y), (g_x + g_w, g_y + g_h), (80, 80, 80), 1)

        # Graph threshold gridlines
        y_40 = g_y + g_h - int(40 * (g_h / 100.0))
        y_70 = g_y + g_h - int(70 * (g_h / 100.0))
        cv2.line(canvas, (g_x, y_40), (g_x + g_w, y_40), (40, 100, 40), 1, cv2.LINE_4)
        cv2.line(canvas, (g_x, y_70), (g_x + g_w, y_70), (40, 40, 120), 1, cv2.LINE_4)
        cv2.putText(canvas, "70%", (g_x + g_w - 30, y_70 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (68, 68, 239), 1, cv2.LINE_AA)
        cv2.putText(canvas, "40%", (g_x + g_w - 30, y_40 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (113, 204, 46), 1, cv2.LINE_AA)

        # Plot data points
        history_subset = fatigue_history[-100:]
        if len(history_subset) > 1:
            step_x = g_w / 99.0
            for i in range(1, len(history_subset)):
                x1 = g_x + int((i - 1) * step_x)
                y1 = g_y + g_h - int(history_subset[i - 1] * (g_h / 100.0))
                x2 = g_x + int(i * step_x)
                y2 = g_y + g_h - int(history_subset[i] * (g_h / 100.0))

                val = history_subset[i]
                if val > 70:
                    line_color = COLOR_DANGER
                elif val > 40:
                    line_color = COLOR_WARNING
                else:
                    line_color = COLOR_ALERT

                cv2.line(canvas, (x1, y1), (x2, y2), line_color, 2, cv2.LINE_AA)

        # 5. Pulsing Vignette alert glow
        if status == "DROWSY" or phone_detected or lane_departure or head_down or head_up:
            pulse = int(6 + 4 * np.sin(time.time() * 8))
            cv2.rectangle(canvas, (0, 0), (win_w, win_h), COLOR_DANGER, pulse)

        cv2.imshow("AI Driver Monitoring System", canvas)

        key = cv2.waitKey(1)

        if key == 27:
            break

        if key == ord("g"):
            plt.plot(fatigue_history)
            plt.title("Driver Fatigue Timeline")
            plt.xlabel("Time")
            plt.ylabel("Fatigue Score")
            plt.show()

cap.release()
cv2.destroyAllWindows()