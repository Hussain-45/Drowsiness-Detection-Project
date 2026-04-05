from ultralytics import YOLO

class PhoneDetector:

    def __init__(self):

        self.model = YOLO("yolov8n.pt")

    def detect_phone(self, frame):

        results = self.model(frame, verbose=False)

        for r in results:

            for box in r.boxes:

                cls = int(box.cls[0])

                if r.names[cls] == "cell phone":

                    return True

        return False