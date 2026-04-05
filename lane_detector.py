import cv2
import numpy as np

class LaneDetector:

    def detect_lane_departure(self, frame):

        height, width = frame.shape[:2]

        roi = frame[int(height*0.6):height, :]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        blur = cv2.GaussianBlur(gray,(5,5),0)

        edges = cv2.Canny(blur,50,150)

        lines = cv2.HoughLinesP(
            edges,
            1,
            np.pi/180,
            50,
            minLineLength=100,
            maxLineGap=50
        )

        if lines is None:
            return True

        return False