import customtkinter as ctk

# Set the theme to dark mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Create the main window
app = ctk.CTk()
app.title("AI Smart Glasses - Companion App")
app.geometry("500x600")

# --- NEW: HARDWARE STATUS BAR ---
# Create an invisible layout frame at the top for our status
status_frame = ctk.CTkFrame(master=app, fg_color="transparent")
# fill="x" makes the frame stretch across the whole width of the window
status_frame.pack(pady=(15, 5), fill="x", padx=25)

# Create the status text and put it on the left side
status_label = ctk.CTkLabel(master=status_frame, text="🔴 Glasses Disconnected", text_color="red", font=("Arial", 14, "bold"))
status_label.pack(side="left")

# Create a variable to track if we are connected or not
is_connected = False

# Function to pretend we are connecting/disconnecting the glasses
def toggle_connection():
    global is_connected # This tells Python we want to change the variable we made above
    is_connected = not is_connected # Flip it (False becomes True, True becomes False)
    
    chat_history.configure(state="normal")
    
    if is_connected:
        status_label.configure(text="🟢 Glasses Connected", text_color="#2ecc71") # Green color
        connect_button.configure(text="Disconnect")
        chat_history.insert("end", "System: Glasses connected successfully via TCP.\n\n")
    else:
        status_label.configure(text="🔴 Glasses Disconnected", text_color="red")
        connect_button.configure(text="Connect")
        chat_history.insert("end", "System: Glasses disconnected.\n\n")
        
    chat_history.configure(state="disabled")
    chat_history.see("end")

# Create a button to toggle the connection, and put it on the right side
connect_button = ctk.CTkButton(master=status_frame, text="Connect", width=80, command=toggle_connection)
connect_button.pack(side="right")
# --------------------------------

# Create a text box for the chat history
chat_history = ctk.CTkTextbox(master=app, width=450, height=400)
chat_history.pack(pady=10) 

# Create the dummy function that acts like our AI for now
def send_message():
    user_text = input_box.get()
    
    if user_text.strip() == "":
        return 
        
    chat_history.configure(state="normal")
    chat_history.insert("end", f"You: {user_text}\n\n")
    chat_history.insert("end", f"AI: I heard you say '{user_text}'. (Real AI coming later!)\n\n")
    chat_history.configure(state="disabled")
    chat_history.see("end")
    input_box.delete(0, "end")

# Create a layout frame to hold the input box and button side-by-side
input_frame = ctk.CTkFrame(master=app, fg_color="transparent")
input_frame.pack(pady=10)

# Create the input text box
input_box = ctk.CTkEntry(master=input_frame, width=350, placeholder_text="Type your message...")
input_box.pack(side="left", padx=10)

# Create the Send button and tell it to run 'send_message' when clicked
send_button = ctk.CTkButton(master=input_frame, text="Send", width=80, command=send_message)
send_button.pack(side="left")

# Add initial system message
chat_history.insert("0.0", "System: AI Glasses Chat Interface Initialized...\n\n")
chat_history.configure(state="disabled")

# Tell the computer to keep the window open and running in a loop
app.mainloop()