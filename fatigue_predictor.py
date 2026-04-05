import numpy as np

class FatiguePredictor:

    def predict(self, blink_rate, yawns, head_tilt):

        score = 0

        if blink_rate > 25:
            score += 40

        if yawns > 2:
            score += 30

        if head_tilt > 5:
            score += 30

        if score > 60:
            return True

        return False