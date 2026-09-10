import customtkinter as ctk

# Set the theme to dark mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Create the main window
app = ctk.CTk()
app.title("AI Smart Glasses - Companion App")
app.geometry("500x600")

# Create a text box for the chat history
chat_history = ctk.CTkTextbox(master=app, width=450, height=400)
chat_history.pack(pady=20) 

# Create the dummy function that acts like our AI for now
def send_message():
    # Get the text that the user typed into the input box
    user_text = input_box.get()
    
    if user_text.strip() == "":
        return # Do nothing if the box is empty
        
    # Make sure we can write into the chat history box
    chat_history.configure(state="normal")
    
    # Insert the user's message
    chat_history.insert("end", f"You: {user_text}\n\n")
    
    # Insert the dummy AI response
    chat_history.insert("end", f"AI: I heard you say '{user_text}'. (Real AI coming later!)\n\n")
    
    # Lock the chat history again so the user can't accidentally type inside it
    chat_history.configure(state="disabled")
    
    # Scroll to the very bottom of the chat history
    chat_history.see("end")
    
    # Clear the input box so it is ready for the next message
    input_box.delete(0, "end")

# Create a layout frame to hold the input box and button side-by-side
input_frame = ctk.CTkFrame(master=app, fg_color="transparent")
input_frame.pack(pady=10)

# Create the input text box
input_box = ctk.CTkEntry(master=input_frame, width=350, placeholder_text="Type your message...")
# Pack it on the left side of our frame
input_box.pack(side="left", padx=10)

# Create the Send button and tell it to run 'send_message' when clicked
send_button = ctk.CTkButton(master=input_frame, text="Send", width=80, command=send_message)
# Pack it on the right side next to the input box
send_button.pack(side="left")

# Add a dummy message just so we can see it working, then lock it initially
chat_history.insert("0.0", "System: AI Glasses Chat Interface Initialized...\n\n")
chat_history.configure(state="disabled")

# Tell the computer to keep the window open and running in a loop
app.mainloop()