import speech_recognition as sr
import pyttsx3

class AudioService:
    def __init__(self):
        # We no longer initialize pyttsx3 here to avoid Windows threading crashes
        self.recognizer = sr.Recognizer()

    def speak(self, text: str):
        """Reads the provided text out loud in a thread-safe way."""
        print(f"[AUDIO] Speaking: {text}")
        try:
            # Initialize the engine locally on the current thread
            engine = pyttsx3.init()
            rate = engine.getProperty('rate')
            engine.setProperty('rate', rate - 20)
            
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[AUDIO FATAL ERROR during speech] {e}")

    def listen(self) -> str:
        """Listens to the default microphone and returns the transcribed text."""
        try:
            # Using device_index=1 based on your hardware list
            with sr.Microphone(device_index=1) as source:
                print("\n[AUDIO] Calibrating to background noise... Please wait 1 second.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print("[AUDIO] Listening! Speak now...")
                audio_data = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                print("[AUDIO] Processing speech...")
                text = self.recognizer.recognize_google(audio_data)
                print(f"[AUDIO] I heard: '{text}'")
                return text
                
        except sr.WaitTimeoutError:
            print("[AUDIO] You didn't say anything.")
            return ""
        except sr.UnknownValueError:
            print("[AUDIO] Sorry, I couldn't understand that.")
            return ""
        except sr.RequestError as e:
            print(f"[AUDIO] Network error connecting to speech service: {e}")
            return ""
        except Exception as e:
            print(f"[AUDIO FATAL ERROR during listening] {e}")
            return ""