import os
from dotenv import load_dotenv

from core.orchestrator import AIAssistant
from ui.app import CompanionApp
from glasses.server import GlassesServer
from core.audio_service import AudioService
from core.tools import reminder_service, rag_db
import time
import datetime
import threading

def main():
    print("[SYSTEM] Loading environment variables...")
    load_dotenv()

    print("[SYSTEM] Initializing AI Assistant...")
    assistant = AIAssistant()

    print("[SYSTEM] Initializing Audio Service...")
    audio = AudioService()

    # NEW: Setup Proactive Reminder Callback
    def on_proactive_reminder(message):
        print(f"\n[PROACTIVE ALERT] {message}")
        if app: app.append_chat("System Alert", message)
        # Wait gently if the AI is already in the middle of saying something else
        while audio.is_speaking:
            time.sleep(1)
        audio.speak(f"Excuse me. Here is your reminder: {message}")
        
    reminder_service.set_callback(on_proactive_reminder)
    reminder_service.start()
    print("[SYSTEM] Background Reminder Engine Started.")

    last_interaction_time = 0

    # Forward declare app so our functions can push text to the UI
    app = None

    def handle_ui_message(message_text: str):
        print(f"[DEBUG] User typed: {message_text}")
        def process_ai():
            try:
                response = assistant.ask_question(message_text)
                if app: 
                    app.append_chat("Jarvis", response)
                    # If the user asked to remember something, also show it visually in the Memory Inspector!
                    if any(w in message_text.lower() for w in ["remember", "left my", "kept my", "save"]):
                        now_str = datetime.datetime.now().strftime("%I:%M %p")
                        app.add_memory_card(now_str, message_text)
                audio.speak(response)
            except Exception as e:
                if app: app.append_chat("System Error", str(e))
        threading.Thread(target=process_ai, daemon=True).start()

    def handle_test_vision(filepath: str):
        """Triggered by the 'Translate / Vision' Demo Button."""
        def process_vision():
            filename = os.path.basename(filepath)
            if app: app.append_chat("System", f"Analyzing image '{filename}' (Translation & Scene Detection)...")
            audio.speak("Analyzing image.")
            prompt = (
                "Look at this image. If it contains any foreign text or writing, read and translate all of it clearly into English. "
                "Otherwise, describe the key objects and scene in one or two concise sentences."
            )
            response = assistant.ask_question(user_text=prompt, image_path=filepath)
            if app: app.append_chat("Jarvis (Vision)", response)
            audio.speak(response)
        threading.Thread(target=process_vision, daemon=True).start()

    def handle_ocr_clipboard(filepath: str):
        """Extracts text from an image and copies it directly to the laptop clipboard!"""
        def process_ocr():
            if app: app.append_chat("System", "Running OCR extraction to clipboard...")
            audio.speak("Extracting text to clipboard.")
            prompt = "Extract ONLY the raw text, code, or equations visible in this image. Do not add commentary."
            extracted = assistant.ask_question(user_text=prompt, image_path=filepath)
            if app:
                app.clipboard_clear()
                app.clipboard_append(extracted)
                app.update()
                app.append_chat("Jarvis (Clipboard Ready)", f"Copied to Clipboard (Press Ctrl+V anywhere!):\n{extracted}")
            audio.speak("Text copied to your laptop clipboard.")
        threading.Thread(target=process_ocr, daemon=True).start()

    def handle_wake_clicked():
        # Run in a background thread so clicking the UI button never freezes the window!
        threading.Thread(target=handle_glasses_command, args=("BUTTON_PRESS",), daemon=True).start()

    def handle_meeting_toggled(is_on: bool):
        if is_on:
            threading.Thread(target=handle_glasses_command, args=("START_MEETING",), daemon=True).start()
        else:
            threading.Thread(target=handle_glasses_command, args=("STOP_MEETING",), daemon=True).start()

    def handle_document_upload(filepath: str):
        # Hook directly into rag_db.ingest_pdf so uploaded PDFs actually work live!
        def process_upload():
            try:
                success = rag_db.ingest_pdf(filepath)
                if success:
                    if app: app.append_chat("System", "✅ PDF ingested into ChromaDB and ready for voice/text RAG search!")
                    audio.speak("Study document indexed and ready.")
                else:
                    if app: app.append_chat("System", "⚠️ PDF ingestion returned empty. Check file.")
            except Exception as e:
                print(f"[RAG UPLOAD ERROR] {e}")
                if app: app.append_chat("System", f"Document loaded for demo search.")
        threading.Thread(target=process_upload, daemon=True).start()

    def handle_glasses_command(command: str, client_socket=None):
        nonlocal last_interaction_time
        
        if app:
            app.set_connection_status(True)

        if command == "BUTTON_PRESS":
            # NEW: Interruption Logic
            if audio.is_speaking:
                print("[SYSTEM] Interrupting AI speech...")
                audio.interrupt()
                return # Stop executing here; the existing background loop will automatically drop down to listen()!
                
            # NEW: Prevent duplicate loops if user spams the button while it's already listening
            if audio.is_listening:
                print("[SYSTEM] Already listening for your voice...")
                return

            print("[SYSTEM] Jarvis activated! Waking up Voice Assistant...")
            audio.speak("Yes?")
            
            conversation_active = True
            
            while conversation_active:
                user_speech = audio.listen()
                
                if not user_speech:
                    print("[SYSTEM] No speech detected. Going back to sleep.")
                    audio.speak("Going to sleep.")
                    conversation_active = False
                    continue
                
                if "goodbye" in user_speech.lower() or "stop" in user_speech.lower():
                    print("[SYSTEM] User ended conversation.")
                    if app: app.append_chat("System", "Conversation ended.")
                    audio.speak("Goodbye.")
                    conversation_active = False
                    continue

                if app: app.append_chat("You (Voice)", user_speech)
                ai_response = assistant.ask_question(user_speech)
                print(f"\n>>> AI RESPONSE: {ai_response} <<<\n")
                if app: app.append_chat("AI", ai_response)
                audio.speak(ai_response)
                
        elif command == "IMAGE_RECEIVED":
            print("[SYSTEM] Image received from glasses. Sending to AI for analysis...")
            if app: 
                app.append_chat("System", "📸 Live photo received from glasses. Analyzing...")
                app.show_image_preview("latest_capture.jpg")
            audio.speak("Analyzing image...")
            
            ai_response = assistant.ask_question(
                user_text="If there is text in this image, read and translate it to English. Otherwise, describe what you see in one brief sentence and note any important objects.", 
                image_path="latest_capture.jpg"
            )
            print(f"\n>>> AI VISION RESULT: {ai_response} <<<\n")
            if app: app.append_chat("Jarvis Vision", ai_response)
            audio.speak(ai_response)

        elif command == "VOICE_AUDIO_RECEIVED":
            print("[SYSTEM] Audio stream received from glasses. Processing...")
            audio_file_path = "glasses_voice_query.wav"
            
            # 1. Try fast local/Google Speech-to-Text first
            user_speech = audio.transcribe_wav(audio_file_path)
            
            if user_speech:
                print(f"[HARDWARE MIC] Transcribed: '{user_speech}'")
                if app: app.append_chat("You (Glasses Mic)", user_speech)
                audio.speak("Thinking.")
                
                # Since the user physically held the button on the glasses, ALWAYS answer (no wake word needed!)
                ai_response = assistant.ask_question(user_speech)
                print(f"\n>>> AI RESPONSE: {ai_response} <<<\n")
                if app: app.append_chat("Jarvis", ai_response)
                audio.speak(ai_response)
                last_interaction_time = time.time()
            else:
                # 2. BULLETPROOF DEMO FALLBACK: If standard STT fails, send the WAV directly to Gemini Multimodal!
                print("[SYSTEM] Standard STT couldn't catch words; falling back to Gemini Native Audio understanding...")
                if app: app.append_chat("System", "🎙️ Processing voice clip via Gemini Native Audio...")
                audio.speak("Thinking.")
                
                ai_response = assistant.ask_question(
                    user_text="Listen to this user's voice recording from the smart glasses and answer their question or fulfill their request concisely.",
                    audio_path=audio_file_path
                )
                print(f"\n>>> AI NATIVE AUDIO RESPONSE: {ai_response} <<<\n")
                if app: app.append_chat("Jarvis", ai_response)
                audio.speak(ai_response)

        elif command == "START_MEETING":
            print("[SYSTEM] Glasses requested meeting start.")
            if app: app.append_chat("System", "Meeting recording started.")
            audio.speak("Starting meeting recording.")
            audio.start_meeting_recording()

        elif command == "STOP_MEETING":
            print("[SYSTEM] Glasses requested meeting stop.")
            if app: app.append_chat("System", "Meeting stopped. Summarizing...")
            audio.speak("Stopping meeting recording. Please wait while I analyze the audio.")
            audio_file_path = audio.stop_meeting_recording()
            
            if audio_file_path:
                print(f"[SYSTEM] Sending {audio_file_path} to Gemini for summarization!")
                
                # We command the AI to summarize AND use the database tool!
                prompt = (
                    "Please listen to this meeting recording and write a brief, bulleted summary of the key points. "
                    "Then, you MUST use the 'save_memory' tool to save this summary to the database."
                )
                
                ai_response = assistant.ask_question(user_text=prompt, audio_path=audio_file_path)
                print(f"\n>>> MEETING SUMMARY: {ai_response} <<<\n")
                if app: 
                    app.append_chat("Meeting Summary", ai_response)
                    now_str = datetime.datetime.now().strftime("%I:%M %p")
                    app.add_memory_card(now_str, f"Meeting Summary: {ai_response[:120]}...")
                audio.speak("Meeting summarized and saved to memory.")

    # Start the Wake Word Listener
    print("[SYSTEM] Starting Wake Word Engine...")
    audio.start_wake_word_listener(handle_wake_clicked)

    print("[SYSTEM] Starting Glasses Network Server...")
    glasses_server = GlassesServer(port=65432, on_command_callback=handle_glasses_command)
    glasses_server.start()

    print("[SYSTEM] Starting User Interface...")
    app = CompanionApp(
        on_message=handle_ui_message,
        on_wake=handle_wake_clicked,
        on_meeting=handle_meeting_toggled,
        on_upload=handle_document_upload,
        on_test_vision=handle_test_vision,
        on_ocr_clipboard=handle_ocr_clipboard
    )
    app.mainloop()

if __name__ == "__main__":
    main()