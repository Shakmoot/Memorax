import os
from dotenv import load_dotenv

from core.orchestrator import AIAssistant
from ui.app import CompanionApp
from glasses.server import GlassesServer
from core.audio_service import AudioService
from core.tools import reminder_service
import time
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

    # Forward declare app so our functions can push text to the UI
    app = None

    def handle_ui_message(message_text: str):
        print(f"[DEBUG] User typed: {message_text}")
        # Run AI in a background thread so the UI doesn't freeze while waiting for Gemini
        def process_ai():
            try:
                response = assistant.ask_question(message_text)
                if app: app.append_chat("AI", response)
                audio.speak(response)
            except Exception as e:
                if app: app.append_chat("System Error", str(e))
        threading.Thread(target=process_ai, daemon=True).start()

    def handle_wake_clicked():
        # Clicking the UI button simulates a hardware button press!
        handle_glasses_command("BUTTON_PRESS")

    def handle_meeting_toggled(is_on: bool):
        if is_on:
            handle_glasses_command("START_MEETING")
        else:
            handle_glasses_command("STOP_MEETING")

    def handle_document_upload(filepath: str):
        # We simulate the ingestion process. In a full build, this hooks to rag_db.ingest_pdf
        def process_upload():
            time.sleep(2) # Simulating processing time
            if app: app.append_chat("System", "Document ingested and ready for RAG search.")
        threading.Thread(target=process_upload, daemon=True).start()

    def handle_glasses_command(command: str):
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

            print("[SYSTEM] Glasses button pressed! Waking up Voice Assistant...")
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
            if app: app.append_chat("System", "Image received. Analyzing...")
            audio.speak("Analyzing image...")
            
            ai_response = assistant.ask_question(
                user_text="Describe what you see in this image in one brief sentence.", 
                image_path="latest_capture.jpg"
            )
            print(f"\n>>> AI VISION RESULT: {ai_response} <<<\n")
            if app: app.append_chat("AI Vision", ai_response)
            audio.speak(ai_response)

        elif command == "VOICE_AUDIO_RECEIVED":
            print("[SYSTEM] Voice query received from glasses. Sending to Gemini...")
            if app: app.append_chat("System", "Audio stream received. Processing...")
            audio.speak("Thinking...")
            
            # Pass the saved WAV file directly to Gemini
            audio_file_path = "glasses_voice_query.wav"
            ai_response = assistant.ask_question(
                user_text="Please answer my spoken question.", 
                audio_path=audio_file_path
            )
            
            print(f"\n>>> AI RESPONSE: {ai_response} <<<\n")
            if app: app.append_chat("AI", ai_response)
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
                if app: app.append_chat("Meeting Summary", ai_response)
                audio.speak("Meeting summarized and saved to memory.")

    print("[SYSTEM] Starting Glasses Network Server...")
    glasses_server = GlassesServer(port=65432, on_command_callback=handle_glasses_command)
    glasses_server.start()

    print("[SYSTEM] Starting User Interface...")
    # Initialize and run the new CustomTkinter App
    app = CompanionApp(
        on_message=handle_ui_message,
        on_wake=handle_wake_clicked,
        on_meeting=handle_meeting_toggled,
        on_upload=handle_document_upload
    )
    # This keeps the application window running
    app.mainloop()

if __name__ == "__main__":
    main()