import speech_recognition as sr
import pyttsx3
import pyaudio
import wave
import threading

class AudioService:
    def __init__(self):
        # We no longer initialize pyttsx3 here to avoid Windows threading crashes
        self.recognizer = sr.Recognizer()
        
        # Variables for continuous meeting recording
        self.is_recording = False
        self.frames = []
        self.recording_thread = None
        self.meeting_filename = "latest_meeting.wav"

    def speak(self, text: str):
        """Reads the provided text out loud in a thread-safe way."""
        print(f"[AUDIO] Speaking: {text}")
        try:
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

    # ---------------------------------------------------------
    # NEW: CONTINUOUS MEETING RECORDING METHODS
    # ---------------------------------------------------------
    
    def start_meeting_recording(self):
        """Starts recording audio continuously in the background."""
        if self.is_recording:
            print("[AUDIO] Already recording a meeting!")
            return

        self.is_recording = True
        self.frames = []
        
        # Start the recording loop on a background thread so the app doesn't freeze
        self.recording_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.recording_thread.start()
        print("[AUDIO] Meeting recording STARTED. Background thread running...")

    def _record_loop(self):
        """The internal loop that runs on the background thread."""
        chunk = 1024
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 44100
        
        p = pyaudio.PyAudio()
        stream = None
        
        try:
            print(f"[AUDIO-DEBUG] Attempting to open audio stream on Mic Index 1...")
            try:
                # First attempt: Index 1 at 44.1kHz
                stream = p.open(format=audio_format, channels=channels, rate=rate, 
                                input=True, input_device_index=1, frames_per_buffer=chunk)
            except Exception as stream_err:
                print(f"[AUDIO-DEBUG] Failed to open Index 1. Trying default Windows settings... Error: {stream_err}")
                # Fallback: Let PyAudio choose the default microphone and use 48kHz
                rate = 48000
                stream = p.open(format=audio_format, channels=channels, rate=rate, 
                                input=True, frames_per_buffer=chunk)
                                
            print("[AUDIO-DEBUG] Stream opened successfully! Capturing audio...")
            
            while self.is_recording:
                data = stream.read(chunk, exception_on_overflow=False)
                self.frames.append(data)
                
        except Exception as e:
            print(f"[AUDIO FATAL] Background thread crashed: {e}")
            
        finally:
            print(f"[AUDIO-DEBUG] Stopping stream. Captured {len(self.frames)} audio frames.")
            if stream:
                stream.stop_stream()
                stream.close()
            p.terminate()
            
            # Ensure we save whatever frames we got before the crash
            if len(self.frames) > 0:
                wf = wave.open(self.meeting_filename, 'wb')
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(audio_format))
                wf.setframerate(rate)
                wf.writeframes(b''.join(self.frames))
                wf.close()
                print(f"[AUDIO-DEBUG] Successfully wrote file to {self.meeting_filename}")
            else:
                print("[AUDIO-DEBUG] No audio frames were captured, so no file was saved.")

    def stop_meeting_recording(self) -> str:
        """Stops the background recording and saves the file."""
        if not self.is_recording:
            return ""
            
        print("[AUDIO] Stopping meeting recording... Saving file...")
        self.is_recording = False
        
        # Wait for the background thread to finish writing the file
        if self.recording_thread:
            self.recording_thread.join()
            
        print(f"[AUDIO] Meeting saved successfully to {self.meeting_filename}")
        return self.meeting_filename