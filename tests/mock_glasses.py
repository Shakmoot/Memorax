import socket
import time

def simulate_button_press():
    host = '127.0.0.1'  # Localhost (your PC)
    port = 65432        # The port your server is listening on
    
    print("[MOCK ESP32] Connecting to phone...")
    
    try:
        # Create a socket and connect
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            
            # Send the button press command
            message = "BUTTON_PRESS"
            print(f"[MOCK ESP32] Sending command: {message}")
            s.sendall(message.encode('utf-8'))
            
        print("[MOCK ESP32] Command sent and connection closed.")
        
    except ConnectionRefusedError:
        print("[MOCK ESP32] ERROR: Could not connect. Is main.py running?")

if __name__ == "__main__":
    print("Press ENTER to simulate pressing the button on the smart glasses.")
    print("Type 'exit' to quit.")
    
    while True:
        user_input = input(">> ")
        if user_input.lower() == 'exit':
            break
        simulate_button_press()