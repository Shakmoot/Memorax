import os, time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
keys = [os.getenv("GEMINI_API_KEY"), os.getenv("GEMINI_API_KEY_2"), os.getenv("GEMINI_API_KEY_3")]
models = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

for i, key in enumerate(keys, 1):
    if not key:
        continue
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=15000))
    for model in models:
        t0 = time.time()
        try:
            r = client.models.generate_content(model=model, contents="Say hello")
            print(f"key{i} {model}: OK {time.time()-t0:.1f}s -> {r.text[:40]}")
        except Exception as e:
            print(f"key{i} {model}: FAIL {time.time()-t0:.1f}s -> {str(e)[:90]}")