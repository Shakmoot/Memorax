import speech_recognition as sr

print("--- AVAILABLE MICROPHONES ---")
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f"Microphone {index}: {name}")
print("-----------------------------")