import socket
import threading
import wave
import array

class GlassesServer:
    def __init__(self, port, on_command_callback):
        self.port = port
        self.on_command_callback = on_command_callback
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while True:
            client, addr = self.server_socket.accept()
            threading.Thread(target=self._handle_client, args=(client, addr), daemon=True).start()

    def _handle_client(self, client_socket, addr):
        print(f"[NETWORK] Connection received from {addr}")
        try:
            # 1. Read the header character by character until newline
            header_data = b""
            while b"\n" not in header_data:
                chunk = client_socket.recv(1)
                if not chunk:
                    break
                header_data += chunk
            
            header_str = header_data.decode('utf-8').strip()
            print(f"[NETWORK] Received header: {header_str}")
            
            # 2. Parse the command and payload length
            if ":" in header_str:
                command, length_str = header_str.split(':', 1)
                payload_length = int(length_str)
            else:
                command = header_str
                payload_length = 0

            # 3. Route the commands
            if command == "IMAGE":
                # Read the binary image payload
                payload = bytearray()
                bytes_received = 0
                
                print(f"[NETWORK] Incoming Image: Expecting {payload_length} bytes...")
                
                while bytes_received < payload_length:
                    # Request chunks
                    chunk = client_socket.recv(min(4096, payload_length - bytes_received))
                    if not chunk:
                        print(f"[NETWORK] Warning: Connection closed early. Got {bytes_received}/{payload_length} bytes.")
                        break # Break out, but KEEP the payload we have!
                        
                    payload.extend(chunk)
                    bytes_received += len(chunk)
                
                print(f"[NETWORK] Image download complete: {bytes_received} bytes received.")
                    
                # Save the image (Even if it's slightly truncated, it often still opens!)
                if bytes_received > 0:
                    with open("latest_capture.jpg", "wb") as f:
                        f.write(payload)
                    print("[NETWORK] Image saved to disk.")
                    # Trigger the callback in main.py, passing the socket for 2-way comms
                    self.on_command_callback("IMAGE_RECEIVED", client_socket)
                else:
                    print("[NETWORK] Error: Received 0 bytes for image.")

            elif command in ["AUDIO_STREAM", "AUDIO_STREAM_V2"]:
                payload = bytearray()
                print(f"[NETWORK] Incoming Audio Stream ({command})...")
                
                if command == "AUDIO_STREAM":
                    # Raw continuous stream until client closes connection (matches record_mic.py!)
                    try:
                        while True:
                            chunk = client_socket.recv(4096)
                            if not chunk:
                                break
                            payload.extend(chunk)
                    except Exception as stream_err:
                        print(f"[NETWORK] Warning: Raw audio stream interrupted: {stream_err}")
                else:
                    # Chunked V2 stream
                    try:
                        while True:
                            header_data = b""
                            while b"\n" not in header_data:
                                char = client_socket.recv(1)
                                if not char:
                                    break
                                header_data += char
                                
                            if not header_data:
                                break
                                
                            header_str = header_data.decode('utf-8').strip()
                            if header_str == "END":
                                break
                                
                            if header_str.startswith("CHUNK:"):
                                chunk_length = int(header_str.split(":")[1])
                                bytes_received = 0
                                while bytes_received < chunk_length:
                                    chunk = client_socket.recv(min(4096, chunk_length - bytes_received))
                                    if not chunk:
                                        break
                                    payload.extend(chunk)
                                    bytes_received += len(chunk)
                    except Exception as stream_err:
                        print(f"[NETWORK] Warning: Audio stream interrupted: {stream_err}")
                    
                print(f"[NETWORK] Audio stream ended. Total received: {len(payload)} bytes.")
                
                # Ensure even number of bytes for 16-bit PCM
                if len(payload) % 2 != 0:
                    payload = payload[:-1]

                # Process if we received at least 0.25 seconds of audio (8000 bytes)
                if len(payload) >= 8000:
                    wav_filename = "glasses_voice_query.wav"
                    try:
                        # AUTO-NORMALIZE & CLEAN AUDIO FOR PERFECT SPEECH RECOGNITION
                        samples = array.array('h', payload)
                        if len(samples) > 0:
                            # Remove any residual DC offset
                            avg_dc = int(sum(samples) / len(samples))
                            samples = array.array('h', [max(-32768, min(32767, s - avg_dc)) for s in samples])
                            
                            # Normalize peak volume to 85% of max 16-bit range so quiet voices are crystal clear
                            peak = max(abs(max(samples)), abs(min(samples)), 1)
                            if peak < 28000:
                                gain = min(8.0, 28000.0 / peak)
                                samples = array.array('h', [max(-32768, min(32767, int(s * gain))) for s in samples])

                        with wave.open(wav_filename, 'wb') as wf:
                            wf.setnchannels(1)          # Mono
                            wf.setsampwidth(2)          # 16-bit (2 bytes per sample)
                            wf.setframerate(16000)      # 16 kHz
                            wf.writeframes(samples.tobytes())
                        print(f"[NETWORK] Saved & normalized {wav_filename} ({len(payload)/32000:.2f}s) successfully.")
                        self.on_command_callback("VOICE_AUDIO_RECEIVED", client_socket)
                    except Exception as wave_err:
                        print(f"[NETWORK] Failed to save WAV file: {wave_err}")
                else:
                    print(f"[NETWORK] Ignored short/blank audio clip ({len(payload)} bytes). Hold the button while speaking.")

            else:
                # Forward all other commands (BUTTON_PRESS, START_MEETING, STOP_MEETING)
                self.on_command_callback(command, client_socket)
                
        except Exception as e:
            print(f"[NETWORK] Error handling client {addr}: {e}")
        finally:
            client_socket.close()