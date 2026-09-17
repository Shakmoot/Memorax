import speech_recognition as sr
import pyttsx3
import pyaudio
import wave
import threading
import queue # NEW: Import the queue library
import time

class AudioService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.5 
        
        # Variables for continuous meeting recording
        self.is_recording = False
        self.frames = []
        self.recording_thread = None
        self.meeting_filename = "latest_meeting.wav"
        
        # Interruption and State flags
        self.is_speaking = False
        self.stop_requested = False
        self.is_listening = False
        self.wake_word_active = False

        # NEW: The Dedicated TTS Queue and Thread
        self.tts_queue = queue.Queue()
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()

    # NEW: The dedicated worker thread that handles ALL speech safely
    def _tts_worker(self):
        """This runs forever in the background, waiting for text to speak."""
        # Initialize the engine EXACTLY ONCE on this specific thread to prevent lockups
        engine = pyttsx3.init()
        rate = engine.getProperty('rate')
        engine.setProperty('rate', rate - 20)
        
        def on_word(name, location, length):
            if self.stop_requested:
                engine.stop()
                
        engine.connect('started-word', on_word)
        
        while True:
            # Wait until there is text in the queue
            text = self.tts_queue.get()
            if text is None: break
            
            self.is_speaking = True
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[AUDIO FATAL ERROR] TTS Engine crashed: {e}")
            finally:
                self.is_speaking = False
                self.tts_queue.task_done()

    def speak(self, text: str):
        """Adds text to the queue instead of trying to speak it directly."""
        print(f"[AUDIO] Speaking: {text}")
        self.stop_requested = False
        self.tts_queue.put(text)

    def interrupt(self):
        """Signals the TTS engine to stop speaking immediately."""
        self.stop_requested = True
        # Clear any remaining queued sentences
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except queue.Empty:
                break

    def start_wake_word_listener(self, wake_callback):
        """Starts a background thread to listen for the wake word."""
        if not self.wake_word_active:
            self.wake_callback = wake_callback
            self.wake_word_active = True
            threading.Thread(target=self._wake_word_loop, daemon=True).start()
            print("[AUDIO] Wake word engine active. Say 'Hey Jarvis' to wake me up.")

    def _wake_word_loop(self):
        """Background loop continuously scanning for the wake word."""
        wake_recognizer = sr.Recognizer()
        
        while self.wake_word_active:
            # If the AI is already talking, recording a meeting, or listening to a query, pause the wake word!
            if self.is_listening or self.is_speaking or self.is_recording:
                time.sleep(1)
                continue
            
            try:
                # We open the mic just long enough to grab a snippet of sound
                # FIX: Removed device_index=1 to automatically use your default microphone
                with sr.Microphone() as source:
                    wake_recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    audio = wake_recognizer.listen(source, timeout=1, phrase_time_limit=2)
                
                # Process the snippet AFTER releasing the mic so the main thread can use it if needed
                text = wake_recognizer.recognize_google(audio).lower()
                
                # FIX: Print everything it hears so you can verify the mic is working!
                print(f"[WAKE-DEBUG] I heard: '{text}'") 
                
                # FIX: Updated wake words to Jarvis
                if "hey jarvis" in text or "jarvis" in text or "wake up" in text:
                    print(f"\n[WAKE WORD DETECTED] Heard: '{text}'")
                    if self.wake_callback:
                        self.wake_callback()
                        # Sleep briefly to give the main thread time to take control of the microphone
                        time.sleep(3)
                        
            except sr.WaitTimeoutError:
                pass # Normal, nobody spoke
            except sr.UnknownValueError:
                pass # Heard noise, but no recognizable words
            except Exception as e:
                print(f"[WAKE-DEBUG] Microphone Error: {e}")
                time.sleep(0.5) # Prevent CPU spam on network/mic errors

    def speak(self, text: str):
        """Reads the provided text out loud in a thread-safe way, with interruption support."""
        print(f"[AUDIO] Speaking: {text}")
        self.is_speaking = True
        self.stop_requested = False
        
        try:
            # Initialize the engine locally on the current thread
            engine = pyttsx3.init()
            rate = engine.getProperty('rate')
            engine.setProperty('rate', rate - 20)
            
            def on_word(name, location, length):
                if self.stop_requested:
                    print("[AUDIO] Speech interrupted by user.")
                    engine.stop()
                    
            engine.connect('started-word', on_word)
            
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[AUDIO FATAL ERROR during speech] {e}")
        finally:
            self.is_speaking = False

    def interrupt(self):
        """Signals the TTS engine to stop speaking immediately."""
        if self.is_speaking:
            self.stop_requested = True

    def listen(self) -> str:
        """Listens to the default microphone and returns the transcribed text."""
        self.is_listening = True
        try:
            # FIX: Removed device_index=1 to automatically use your default microphone here too
            with sr.Microphone() as source:
                print("\n[AUDIO] Calibrating to background noise... Please wait 1 second.")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print("[AUDIO] Listening! Speak now... (I will listen until you stop talking)")
                
                # NEW: Removed phrase_time_limit. It will now record until it detects silence.
                audio_data = self.recognizer.listen(source, timeout=5)
                
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
        finally:
            self.is_listening = False

    def start_meeting_recording(self):
        """Starts recording audio continuously in the background."""
        if self.is_recording:
            print("[AUDIO] Already recording a meeting!")
            return

        self.is_recording = True
        self.frames = []
        
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
                stream = p.open(format=audio_format, channels=channels, rate=rate, 
                                input=True, input_device_index=1, frames_per_buffer=chunk)
            except Exception as stream_err:
                print(f"[AUDIO-DEBUG] Failed to open Index 1. Trying default... Error: {stream_err}")
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
        
        if self.recording_thread:
            self.recording_thread.join()
            
        print(f"[AUDIO] Meeting saved successfully to {self.meeting_filename}")
        return self.meeting_filename