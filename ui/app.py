def start_ui(on_message_callback):
    print("\n--- MOCK UI STARTED ---")
    print("Type your message (or 'exit' to quit):")
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            print("Closing UI...")
            break
            
        # Trigger the callback in main.py just like a real UI would
        response = on_message_callback(user_input)
        print(f"Assistant: {response}")