import time

class FatigueAnalyzer:

    def __init__(self):

        self.eye_start=None
        self.eye_duration=0

        self.yawn_count=0
        self.blink_count=0

        self.head_tilt_count=0

        self.last_eye_state=False
        self.last_yawn_state=False
        self.last_head_tilt_state=False

    def update(self,eyes_closed,yawn,head_tilt,head_down):

        current=time.time()

        if eyes_closed:

            if self.eye_start is None:
                self.eye_start=current

            self.eye_duration=current-self.eye_start

        else:

            if self.last_eye_state:
                self.blink_count+=1

            self.eye_start=None
            self.eye_duration=0

        # Edge-triggered yawn count (increment only on transition from False to True)
        if yawn:
            if not self.last_yawn_state:
                self.yawn_count+=1

        # Edge-triggered head tilt/down count
        tilt_or_down = head_tilt or head_down
        if tilt_or_down:
            if not self.last_head_tilt_state:
                self.head_tilt_count+=1

        self.last_eye_state=eyes_closed
        self.last_yawn_state=yawn
        self.last_head_tilt_state=tilt_or_down

    def fatigue_score(self):

        score=0

        if self.eye_duration>2:
            score+=40

        if self.eye_duration>3:
            score+=30

        if self.yawn_count>3:
            score+=20

        if self.blink_count>25:
            score+=10

        if self.head_tilt_count>10:
            score+=20

        return min(score,100)