import pygame
import pyttsx3

class AlertSystem:

    def __init__(self):

        pygame.mixer.init()

        self.engine = pyttsx3.init()

        self.engine.setProperty("rate",150)

    def alarm(self):

        pygame.mixer.music.load("alarm.wav")
        pygame.mixer.music.play()

    def speak(self,message):

        self.engine.say(message)
        self.engine.runAndWait()

    def eyes_alert(self):

        self.alarm()
        self.speak("Warning. Eyes closed detected")

    def yawn_alert(self):

        self.alarm()
        self.speak("Yawning detected. Please stay alert")

    def head_tilt_alert(self):

        self.alarm()
        self.speak("Head tilt detected")

    def head_down_alert(self):

        self.alarm()
        self.speak("Driver looking down")

    def fatigue_alert(self):

        self.alarm()
        self.speak("Driver fatigue detected. Please take a break")