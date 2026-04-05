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


EYE_THRESHOLD=0.20
YAWN_THRESHOLD=0.06

CONFIRM_TIME=3
VOICE_COOLDOWN=5


last_voice_alert=0

eyes_start=None
yawn_start=None
tilt_start=None
down_start=None


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

        if results.multi_face_landmarks:

            landmarks=results.multi_face_landmarks[0].landmark

            ear=(eye_ratio(landmarks,LEFT_EYE)+eye_ratio(landmarks,RIGHT_EYE))/2
            eyes_closed=ear<EYE_THRESHOLD

            mouth_open=distance(landmarks[MOUTH[0]],landmarks[MOUTH[1]])
            yawn=mouth_open>YAWN_THRESHOLD

            angle=head_tilt_angle(landmarks)
            head_tilt=abs(angle)>20

            nose=landmarks[NOSE]
            chin=landmarks[CHIN]
            head_down=(chin.y-nose.y)<0.05

            fatigue.update(eyes_closed,yawn,head_tilt,head_down)

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
                trigger_alert("Driver looking down")

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


        # ---------- MODERN UI ---------- #

        win_w = 1200
        win_h = 720

        canvas = np.ones((win_h, win_w, 3), dtype=np.uint8) * 255

        frame_h, frame_w = frame.shape[:2]

        scale = min((win_w*0.65)/frame_w,(win_h*0.55)/frame_h)

        new_w = int(frame_w * scale)
        new_h = int(frame_h * scale)

        resized = cv2.resize(frame,(new_w,new_h))

        x_offset = (win_w-new_w)//2
        y_offset = 120

        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized


        cv2.rectangle(canvas,(0,0),(win_w,80),(0,0,0),-1)

        cv2.putText(canvas,
                    "AI DRIVER MONITORING SYSTEM",
                    (win_w//2-300,50),
                    cv2.FONT_HERSHEY_TRIPLEX,
                    1.0,
                    (0,255,255),
                    2,
                    cv2.LINE_AA)


        panel_y = y_offset + new_h + 20

        cv2.rectangle(canvas,(0,panel_y),(win_w,panel_y+120),(235,235,235),-1)


        cv2.putText(canvas,
                    f"Status : {status}",
                    (win_w//2 - 200, panel_y + 40),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.9,
                    (0,180,0),
                    2,
                    cv2.LINE_AA)


        cv2.putText(canvas,
                    f"Fatigue Score : {score}%",
                    (win_w//2 - 200, panel_y + 75),
                    cv2.FONT_HERSHEY_DUPLEX,
                    0.9,
                    (255,140,0),
                    2,
                    cv2.LINE_AA)


        bar_width = 320
        bar_value = int(score * 3)

        bar_x = win_w//2 - 200
        bar_y = panel_y + 90

        cv2.rectangle(canvas,
                      (bar_x, bar_y),
                      (bar_x + bar_value, bar_y + 20),
                      (0,255,0),
                      -1)

        cv2.rectangle(canvas,
                      (bar_x, bar_y),
                      (bar_x + bar_width, bar_y + 20),
                      (50,50,50),
                      2)


        cv2.imshow("AI Driver Monitoring System",canvas)

        key=cv2.waitKey(1)

        if key==27:
            break

        if key==ord("g"):
            plt.plot(fatigue_history)
            plt.title("Driver Fatigue Timeline")
            plt.xlabel("Time")
            plt.ylabel("Fatigue Score")
            plt.show()

cap.release()
cv2.destroyAllWindows()