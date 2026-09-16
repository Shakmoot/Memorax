import customtkinter as ctk
import threading
import time

# Set the overall appearance to dark mode and color theme to blue
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Wearable AI Glasses - Desktop Companion")
app.geometry("900x600") 

# --- LEFT PANEL (Your Control Panel) ---
sidebar_frame = ctk.CTkFrame(master=app, width=250, corner_radius=0)
sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)

# 1. Status Label
status_label = ctk.CTkLabel(
    master=sidebar_frame,
    text="Status: 🔴 Disconnected",
    font=("Roboto", 16, "bold")
)
status_label.pack(pady=(30, 20))

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

# --- RIGHT PANEL (The Main Area) ---
main_frame = ctk.CTkFrame(master=app, corner_radius=10)
main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

# --- TABBED INTERFACE ---
tabview = ctk.CTkTabview(master=main_frame)
tabview.pack(fill="both", expand=True)

chat_tab = tabview.add("Live Chat")
memory_tab = tabview.add("Memory Inspector")
docs_tab = tabview.add("RAG Documents")

# ==========================================
# --- TAB 1: LIVE CHAT CONTENTS ---
# ==========================================
chat_title = ctk.CTkLabel(master=chat_tab, text="Live AI Chat Log", font=("Roboto", 24, "bold"))
chat_title.pack(pady=10)

chat_history_box = ctk.CTkTextbox(master=chat_tab, width=400, height=300)
chat_history_box.pack(fill="both", expand=True, padx=20, pady=10)
chat_history_box.insert("0.0", "AI: Welcome to the smart glasses companion app. I am ready.\n")
chat_history_box.configure(state="disabled") 

input_frame = ctk.CTkFrame(master=chat_tab, fg_color="transparent")
input_frame.pack(fill="x", padx=20, pady=(0, 20)) 

def send_message():
    user_text = message_entry.get()
    if user_text.strip() == "":
        return
        
    # 1. Update UI with the user's message immediately
    chat_history_box.configure(state="normal")
    chat_history_box.insert("end", f"You: {user_text}\n")
    chat_history_box.see("end")
    chat_history_box.configure(state="disabled")
    
    # Clear the input box
    message_entry.delete(0, "end")
    
    # 2. Start the background thread to fetch the AI response
    # We hand the order to the "cook" (the background thread) and keep the UI moving!
    threading.Thread(target=get_ai_response, args=(user_text,)).start()

def get_ai_response(user_text):
    # This function runs in the background! The UI will NOT freeze.
    
    # Simulate network delay (the AI thinking for 2 seconds)
    time.sleep(2)
    
    # The AI has finished thinking, now update the UI with the answer
    chat_history_box.configure(state="normal")
    chat_history_box.insert("end", f"AI: This is a threaded background response to '{user_text}'\n\n")
    chat_history_box.see("end")
    chat_history_box.configure(state="disabled")

message_entry = ctk.CTkEntry(master=input_frame, placeholder_text="Type a message to the AI...", font=("Roboto", 14), height=40)
message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

send_button = ctk.CTkButton(master=input_frame, text="Send", command=send_message, font=("Roboto", 14, "bold"), width=80, height=40)
send_button.pack(side="right")

# ==========================================
# --- TAB 2: MEMORY INSPECTOR CONTENTS ---
# ==========================================
memory_title = ctk.CTkLabel(master=memory_tab, text="AI Visual & Object Memory", font=("Roboto", 24, "bold"))
memory_title.pack(pady=10)

search_frame = ctk.CTkFrame(master=memory_tab, fg_color="transparent")
search_frame.pack(fill="x", padx=20, pady=10)

memory_search_entry = ctk.CTkEntry(master=search_frame, placeholder_text="Search memories (e.g., 'keys')...", height=40)
memory_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

def search_memory():
    print(f"Searching database for: {memory_search_entry.get()}")

search_btn = ctk.CTkButton(master=search_frame, text="Search", command=search_memory, width=80, height=40)
search_btn.pack(side="right")

memory_list = ctk.CTkScrollableFrame(master=memory_tab, corner_radius=10)
memory_list.pack(fill="both", expand=True, padx=20, pady=10)

dummy_memories = [
    "🔑 Object: Car Keys | Location: Coffee Table | Time: 10:31 AM",
    "☕ Object: Mug | Location: Office Desk | Time: 09:15 AM",
    "📝 Note: Wifi Password | Location: Fridge Door | Time: Yesterday",
    "💼 Event: Met with John | Context: Discussed Q3 Budget | Time: Monday"
]

for memory_text in dummy_memories:
    ctk.CTkLabel(master=memory_list, text=memory_text, font=("Roboto", 14), anchor="w", fg_color="#2b2b2b", corner_radius=5, padx=10, pady=10).pack(fill="x", pady=5)

# ==========================================
# --- TAB 3: RAG DOCUMENTS CONTENTS ---
# ==========================================
docs_title = ctk.CTkLabel(master=docs_tab, text="Study Mode: PDF Knowledge Base", font=("Roboto", 24, "bold"))
docs_title.pack(pady=10)

def open_file_dialog():
    # This opens the native Windows/Mac file picker
    file_path = ctk.filedialog.askopenfilename(
        title="Select a PDF to upload",
        filetypes=[("PDF files", "*.pdf")]
    )
    if file_path:
        print(f"Selected file to upload: {file_path}")

upload_btn = ctk.CTkButton(
    master=docs_tab, 
    text="➕ Upload New PDF", 
    command=open_file_dialog,
    font=("Roboto", 16, "bold"),
    height=45
)
upload_btn.pack(pady=20)

# Scrollable list for loaded documents
ctk.CTkLabel(master=docs_tab, text="Currently Loaded Documents:", font=("Roboto", 16)).pack(anchor="w", padx=20)

docs_list = ctk.CTkScrollableFrame(master=docs_tab, corner_radius=10)
docs_list.pack(fill="both", expand=True, padx=20, pady=10)

# Dummy Documents Data
dummy_docs = [
    "📄 Chapter_4_Networking.pdf (Processed)",
    "📄 History_Notes_Final.pdf (Processed)",
    "📄 Product_Manual_v2.pdf (Processed)"
]

for doc_text in dummy_docs:
    ctk.CTkLabel(master=docs_list, text=doc_text, font=("Roboto", 14), anchor="w", fg_color="#2b2b2b", corner_radius=5, padx=10, pady=10).pack(fill="x", pady=5)

# Start the application!
if __name__ == "__main__":
    app.mainloop()