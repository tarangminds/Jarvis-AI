from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from fastapi.responses import JSONResponse, FileResponse
from gtts import gTTS
import uuid
import os
import requests
import re

app = FastAPI()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_KEY = os.getenv("JARVIS_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://jarvis-ai-10.onrender.com")  # default to deployed URL

class PromptRequest(BaseModel):
    text: str

def clean_text(text: str) -> str:
    return re.sub(r'[*_`]', '', text)

def generate_text_with_gemini(prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

@app.post("/generate-and-speak")
async def generate_and_speak(request: PromptRequest, authorization: str = Header(None)):
    if authorization != f"Bearer {API_KEY}":
        raise HTTPException(status_code=403, detail="Unauthorized")

    generated_text = generate_text_with_gemini(request.text)
    full_text = "Hello, I am Jarvis, your AI assistant.\n\n" + generated_text
    tts_text = clean_text(full_text)

    filename = f"speech_{uuid.uuid4().hex}.mp3"
    filepath = f"/tmp/{filename}"
    tts = gTTS(text=tts_text, lang='en')
    tts.save(filepath)

    audio_url = f"{BASE_URL}/audio/{filename}"

    return JSONResponse({
        "message": "Audio generated successfully",
        "text": full_text,
        "audio_url": audio_url
    })

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    filepath = f"/tmp/{filename}"
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(filepath, media_type="audio/mpeg")

