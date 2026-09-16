import os
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class CompanionApp(ctk.CTk):
    def __init__(self, on_message, on_wake, on_meeting, on_upload):
        super().__init__()
        
        # Attach the callback functions passed from main.py
        self.on_message = on_message
        self.on_wake = on_wake
        self.on_meeting = on_meeting
        self.on_upload = on_upload
        
        self.title("AI Smart Glasses - Companion App")
        self.geometry("600x750")
        
        self._build_header()
        self._build_tabs()
        
    def _build_header(self):
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(15, 5), fill="x", padx=25)
        
        # Status Label (Combined from Member 3 & 4)
        self.status_label = ctk.CTkLabel(
            self.header_frame, 
            text="🔴 Glasses Disconnected", 
            text_color="red", 
            font=("Roboto", 16, "bold")
        )
        self.status_label.pack(side="left")
        
        # Meeting Mode Toggle (from Member 4)
        self.meeting_switch = ctk.CTkSwitch(
            self.header_frame,
            text="Meeting Mode",
            command=self._meeting_toggled,
            font=("Roboto", 14)
        )
        self.meeting_switch.pack(side="right", padx=10)
        
        # Wake Button (from Member 4)
        self.wake_button = ctk.CTkButton(
            self, 
            text="Wake Assistant", 
            command=self.on_wake,
            font=("Roboto", 18, "bold"),
            width=200, height=50, corner_radius=25
        )
        self.wake_button.pack(pady=10)

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(self, width=550, height=550)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.tabview.add("Live Chat")
        self.tabview.add("Memory Inspector")
        self.tabview.add("Document Manager")
        
        self._build_chat_tab()
        self._build_memory_tab()
        self._build_doc_tab()

    def _build_chat_tab(self):
        tab = self.tabview.tab("Live Chat")
        
        self.chat_history = ctk.CTkTextbox(tab, wrap="word")
        self.chat_history.pack(pady=10, fill="both", expand=True)
        self.chat_history.insert("0.0", "System: AI Glasses Chat Interface Initialized...\n\n")
        self.chat_history.configure(state="disabled")
        
        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.pack(pady=10, fill="x")
        
        self.input_box = ctk.CTkEntry(input_frame, placeholder_text="Type your message...")
        self.input_box.pack(side="left", padx=(0, 10), fill="x", expand=True)
        
        send_button = ctk.CTkButton(input_frame, text="Send", width=80, command=self._send_message)
        send_button.pack(side="right")

    def _build_memory_tab(self):
        tab = self.tabview.tab("Memory Inspector")
        self.memory_scroll = ctk.CTkScrollableFrame(tab)
        self.memory_scroll.pack(pady=10, fill="both", expand=True)
        
        # Placeholder memory to show the layout works
        self.add_memory_card("09:15 AM", "Keys left on the kitchen counter.")

    def _build_doc_tab(self):
        tab = self.tabview.tab("Document Manager")
        self.doc_list = ctk.CTkScrollableFrame(tab, label_text="Uploaded Study Materials")
        self.doc_list.pack(pady=10, fill="both", expand=True)
        
        upload_btn = ctk.CTkButton(tab, text="Browse for PDF", command=self._upload_doc, font=("Roboto", 14, "bold"))
        upload_btn.pack(pady=10)

    def _send_message(self):
        text = self.input_box.get()
        if text.strip():
            self.append_chat("You", text)
            self.input_box.delete(0, "end")
            if self.on_message:
                self.on_message(text)

    def _meeting_toggled(self):
        is_on = self.meeting_switch.get() == 1
        if self.on_meeting:
            self.on_meeting(is_on)

    def _upload_doc(self):
        filepath = ctk.filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if filepath:
            filename = os.path.basename(filepath)
            ctk.CTkLabel(self.doc_list, text=f"📄 {filename}", font=("Roboto", 14)).pack(anchor="w", pady=5, padx=10)
            self.append_chat("System", f"Document '{filename}' queued for AI Study Mode.")
            if self.on_upload:
                self.on_upload(filepath)

    def append_chat(self, sender, message):
        """Thread-safe way to add text to the chat box."""
        def update():
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", f"{sender}: {message}\n\n")
            self.chat_history.configure(state="disabled")
            self.chat_history.see("end")
        
        # .after(0, ...) ensures Tkinter processes the update safely on the main UI thread
        self.after(0, update)

    def set_connection_status(self, is_connected):
        """Updates the hardware status indicator."""
        def update():
            if is_connected:
                self.status_label.configure(text="🟢 Glasses Connected", text_color="#2ecc71")
                self.append_chat("System", "Hardware connected via TCP.")
            else:
                self.status_label.configure(text="🔴 Glasses Disconnected", text_color="red")
                self.append_chat("System", "Hardware disconnected.")
        self.after(0, update)

    def add_memory_card(self, time_str, text):
        """Adds a visual memory card to the inspector."""
        def update():
            card = ctk.CTkFrame(self.memory_scroll, fg_color="#2b2b2b", corner_radius=10)
            card.pack(pady=5, fill="x", padx=10)
            ctk.CTkLabel(card, text=time_str, text_color="gray", font=("Roboto", 12)).pack(side="left", padx=10, pady=10)
            ctk.CTkLabel(card, text=text, font=("Roboto", 14), wraplength=350, justify="left").pack(side="left", padx=10, pady=10)
        self.after(0, update)