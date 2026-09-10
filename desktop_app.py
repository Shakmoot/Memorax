import customtkinter as ctk

# Set the overall appearance to dark mode and color theme to blue
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Wearable AI Glasses - Desktop Companion")
# Make the window much larger to fit both panels!
app.geometry("900x600") 

# --- LEFT PANEL (Your Control Panel) ---
# We create a Frame on the left side of the app.
sidebar_frame = ctk.CTkFrame(master=app, width=250, corner_radius=0)
# pack() puts it on the screen. side="left" pushes it to the left edge.
# fill="y" makes it stretch all the way from the top to the bottom!
sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)

# --- RIGHT PANEL (The Chat Area) ---
# We create another Frame for the chat that takes up the rest of the space.
main_frame = ctk.CTkFrame(master=app, corner_radius=10)
# expand=True tells this box to take up all the remaining horizontal space.
main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)


# 1. Status Label
status_label = ctk.CTkLabel(
    master=sidebar_frame, # NOTICE: We put this inside sidebar_frame, not app!
    text="Status: 🔴 Disconnected",
    font=("Roboto", 16, "bold")
)
status_label.pack(pady=(30, 20)) # Adds spacing at the top

# 2. Wake Assistant Button
def wake_ai_clicked():
    print("Wake Assistant clicked! AI is listening...")

wake_button = ctk.CTkButton(
    master=sidebar_frame, 
    text="Wake Assistant", 
    command=wake_ai_clicked,
    font=("Roboto", 18, "bold"),
    height=50,
    corner_radius=25
)
# padx=20 gives the button some breathing room on the left and right sides
wake_button.pack(pady=20, padx=20) 

# 3. Meeting Mode Toggle
def meeting_mode_toggled():
    print(f"Meeting Mode: {meeting_switch.get()}")

meeting_switch = ctk.CTkSwitch(
    master=sidebar_frame,
    text="Meeting Mode",
    command=meeting_mode_toggled,
    font=("Roboto", 14)
)
meeting_switch.pack(pady=20)

# We will put a simple title here for now so you can see where the chat will go.
chat_title = ctk.CTkLabel(
    master=main_frame, # This goes in the right box!
    text="Live AI Chat Log",
    font=("Roboto", 24, "bold")
)
chat_title.pack(pady=20)

# A large empty text box to represent where the chat history will appear
chat_history_box = ctk.CTkTextbox(master=main_frame, width=400, height=300)
chat_history_box.pack(fill="both", expand=True, padx=20, pady=10)
chat_history_box.insert("0.0", "AI: Welcome to the smart glasses companion app. I am ready.\n")
# Make it read-only so the user can't type over the history
chat_history_box.configure(state="disabled") 


# --- NEW: Chat Input Area ---
def send_message_clicked():
    user_text = chat_input.get().strip()
    if user_text == "":
        return # Do nothing if the box is empty
    
    # 1. Temporarily enable the history box so we can insert text via code
    chat_history_box.configure(state="normal")
    
    # 2. Add the user's message to the bottom ("end") of the chat
    chat_history_box.insert("end", f"You: {user_text}\n")
    
    # 3. Add a fake AI response
    chat_history_box.insert("end", f"AI: I heard you say '{user_text}'.\n\n")
    
    # 4. Disable the box again and clear the typing area
    chat_history_box.configure(state="disabled")
    chat_input.delete(0, "end")

# Create a small horizontal layout at the bottom for the input and button
input_frame = ctk.CTkFrame(master=main_frame, fg_color="transparent")
input_frame.pack(fill="x", padx=20, pady=(0, 20))

chat_input = ctk.CTkEntry(
    master=input_frame, 
    placeholder_text="Type a message to the AI...",
    font=("Roboto", 14),
    height=40
)
# expand=True makes the typing box take up most of the horizontal space
chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10))

send_msg_button = ctk.CTkButton(
    master=input_frame,
    text="Send",
    font=("Roboto", 14, "bold"),
    width=80,
    height=40,
    command=send_message_clicked
)
send_msg_button.pack(side="right")

if __name__ == "__main__":
    app.mainloop()