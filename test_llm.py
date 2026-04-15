import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY", "")

client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model='gemini-3.1-flash-lite-preview',
        contents='Say "OK" in one word.',
    )
    print(f"SUCCESS: {response.text.strip()}")
except Exception as e:
    error = str(e)
    if "503" in error or "UNAVAILABLE" in error:
        print(f"HEAVY TRAFFIC: Model is overloaded. {error}")
    elif "429" in error or "ResourceExhausted" in error:
        print(f"QUOTA EXCEEDED: {error}")
    else:
        print(f"ERROR: {error}")
