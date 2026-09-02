import socket
import time
import os

def send_payload(command: str, payload: bytes = b""):
    host = '127.0.0.1'
    port = 65432
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            
            # Format the header: COMMAND:SIZE\n
            header = f"{command}:{len(payload)}\n"
            print(f"[MOCK ESP32] Sending Header: {header.strip()}")
            
            # Send Header then Payload
            s.sendall(header.encode('utf-8'))
            if payload:
                s.sendall(payload)
                
            print("[MOCK ESP32] Transmission complete.")
            
    except ConnectionRefusedError:
        print("[MOCK ESP32] ERROR: Could not connect. Is main.py running?")

def simulate_button_press():
    send_payload("BUTTON_PRESS")

def simulate_image_capture():
    # We will generate a dummy byte array to simulate a 50KB JPEG image
    # (In reality, the ESP32 would read this from the camera buffer)
    dummy_image_bytes = os.urandom(50000) 
    print("[MOCK ESP32] 'Click!' - Captured 50KB image.")
    send_payload("IMAGE", dummy_image_bytes)

if __name__ == "__main__":
    print("MOCK SMART GLASSES CLIENT")
    print("1. Type 'btn' to simulate the physical button press.")
    print("2. Type 'img' to simulate sending a captured photo.")
    print("3. Type 'exit' to quit.")
    
    while True:
        user_input = input("\n>> ").strip().lower()
        if user_input == 'exit':
            break
        elif user_input == 'btn':
            simulate_button_press()
        elif user_input == 'img':
            simulate_image_capture()
        else:
            print("Invalid command.")