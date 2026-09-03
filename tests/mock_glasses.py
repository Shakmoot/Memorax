import socket
import cv2  # OpenCV for webcam
import time

def send_payload(command: str, payload: bytes = b""):
    host = '127.0.0.1'
    port = 65432
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            
            header = f"{command}:{len(payload)}\n"
            print(f"[MOCK ESP32] Sending Header: {header.strip()}")
            
            s.sendall(header.encode('utf-8'))
            if payload:
                s.sendall(payload)
                
            print("[MOCK ESP32] Transmission complete.")
            
    except ConnectionRefusedError:
        print("[MOCK ESP32] ERROR: Could not connect. Is main.py running?")

def simulate_button_press():
    send_payload("BUTTON_PRESS")

def capture_real_image():
    print("[MOCK ESP32] Warming up webcam...")
    # Open the default camera (index 0)
    cap = cv2.VideoCapture(0)
    
    # Wait a second for the camera sensor to adjust to the light
    time.sleep(1)
    
    # Read a frame
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("[MOCK ESP32] ERROR: Failed to grab a frame from the webcam.")
        return
    
    # Compress the raw frame into a JPEG image in memory
    # We use 80% quality to simulate the compression of a cheap ESP32 camera
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
    ret, buffer = cv2.imencode('.jpg', frame, encode_param)
    
    if not ret:
        print("[MOCK ESP32] ERROR: Failed to encode image to JPEG.")
        return
        
    image_bytes = buffer.tobytes()
    print(f"[MOCK ESP32] 'Click!' - Captured {len(image_bytes)} byte real image.")
    send_payload("IMAGE", image_bytes)

if __name__ == "__main__":
    print("--- ADVANCED MOCK SMART GLASSES ---")
    print("1. Type 'btn' to send a button press.")
    print("2. Type 'img' to snap a REAL photo with your webcam and send it.")
    print("3. Type 'exit' to quit.")
    
    while True:
        user_input = input("\n>> ").strip().lower()
        if user_input == 'exit':
            break
        elif user_input == 'btn':
            simulate_button_press()
        elif user_input == 'img':
            capture_real_image()
        else:
            print("Invalid command.")