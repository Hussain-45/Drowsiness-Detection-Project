import pygame
import pyttsx3
import threading

class AlertSystem:

    def __init__(self):
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"Warning: Could not initialize pygame mixer: {e}")

    def alarm(self):
        try:
            pygame.mixer.music.load("alarm.wav")
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Warning: Could not play alarm: {e}")

    def _speak_worker(self, message):
        try:
            # Initialize pyttsx3 engine in the background thread for COM safety on Windows
            engine = pyttsx3.init()
            engine.setProperty("rate", 150)
            engine.say(message)
            engine.runAndWait()
        except Exception as e:
            print(f"Warning: Text-to-speech failed: {e}")

    def speak(self, message):
        # Run speech asynchronously so it does not block the main video loop
        threading.Thread(target=self._speak_worker, args=(message,), daemon=True).start()

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