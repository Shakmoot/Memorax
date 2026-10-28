from core.orchestrator import AIAssistant

def main():
    print("[SYSTEM] Initializing AI Assistant...")
    assistant = AIAssistant()
    
    # Change this to the exact name of your saved image file
    image_file = "foreign_sign.jpg" 
    
    prompt = "Please read and translate all the foreign text in this image into English."
    
    print(f"[SYSTEM] Sending {image_file} to Gemini for translation...")
    
    try:
        response = assistant.ask_question(user_text=prompt, image_path=image_file)
        print(f"\n>>> TRANSLATION RESULT <<<\n{response}\n")
    except Exception as e:
        print(f"\n[ERROR] Could not process the image: {e}")
        print("Make sure the image file is in the same folder as this script!")

if __name__ == "__main__":
    main()