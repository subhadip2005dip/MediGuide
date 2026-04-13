from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import os
import requests

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.1
)


class TranslateTextRequest(BaseModel):
    text: str
    source_language: str
    target_language: str


class TranslateTextResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    target_language_name: str
    tts_lang: str


SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "deepgram_lang": "en-IN", "tts_lang": "en-IN", "google_tts_lang": "en-US"},
    "hi": {"name": "हिंदी (Hindi)", "deepgram_lang": "hi", "tts_lang": "hi-IN", "google_tts_lang": "hi-IN"},
}

@router.get("/languages")
async def get_languages():
    """Return list of supported languages for the UI."""
    return {
        "languages": [
            {"code": code, "name": info["name"], "tts_lang": info["tts_lang"]}
            for code, info in SUPPORTED_LANGUAGES.items()
        ]
    }

@router.post("/text", response_model=TranslateTextResponse)
async def translate_text(req: TranslateTextRequest):
    target_info = SUPPORTED_LANGUAGES.get(req.target_language, SUPPORTED_LANGUAGES["en"])

    if req.source_language == req.target_language:
        return TranslateTextResponse(
            original_text=req.text,
            translated_text=req.text,
            source_language=req.source_language,
            target_language=req.target_language,
            target_language_name=target_info["name"],
            tts_lang=target_info["tts_lang"],
        )

    source_info = SUPPORTED_LANGUAGES.get(req.source_language, SUPPORTED_LANGUAGES["en"])

    prompt = f"""
    Translate this medical sentence from {source_info['name']} to {target_info['name']}.
    Keep it natural, concise, and medically accurate.
    Only output the translated text, nothing else.

    Text: {req.text}
    """

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        translated = response.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return TranslateTextResponse(
        original_text=req.text,
        translated_text=translated,
        source_language=req.source_language,
        target_language=req.target_language,
        target_language_name=target_info["name"],
        tts_lang=target_info["tts_lang"],
    )

@router.post("/audio")
async def translate_audio(
    audio: UploadFile = File(...),
    sourceLang: str = Form(...),
    targetLang: str = Form(...)
):
    try:
        audio_bytes = await audio.read()

        lang_info = SUPPORTED_LANGUAGES.get(sourceLang, SUPPORTED_LANGUAGES["en"])
        deepgram_lang = lang_info["deepgram_lang"]

        print(f"Transcribing audio - Language: {sourceLang} ({deepgram_lang}), Audio size: {len(audio_bytes)} bytes")

        dg_res = requests.post(
            "https://api.deepgram.com/v1/listen",
            headers={
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "audio/webm"
            },
            params={
                "model": "nova-2",
                "language": deepgram_lang,
                "smart_format": "true",
                "detect_language": "false"
            },
            data=audio_bytes
        )

        dg_data = dg_res.json()

        # If language-specific request fails, retry with language detection
        if not dg_res.ok:
            error_msg = dg_data.get("error", {}).get("message", f"HTTP {dg_res.status_code}")
            print(f"Deepgram API error for language {deepgram_lang}: {error_msg}, retrying with auto-detection...")

            dg_res = requests.post(
                "https://api.deepgram.com/v1/listen",
                headers={
                    "Authorization": f"Token {DEEPGRAM_API_KEY}",
                    "Content-Type": "audio/webm"
                },
                params={
                    "model": "nova-2",
                    "smart_format": "true",
                    "detect_language": "true"
                },
                data=audio_bytes
            )

            dg_data = dg_res.json()

            if not dg_res.ok:
                error_msg = dg_data.get("error", {}).get("message", f"HTTP {dg_res.status_code}")
                print(f"Deepgram auto-detection also failed: {error_msg}")
                return {"error": f"Speech recognition failed: {error_msg}"}

        if "results" not in dg_data:
            print(f"Deepgram response missing 'results' key. Full response: {dg_data}")
            return {"error": "Speech recognition failed - invalid response format"}

        try:
            transcript = dg_data["results"]["channels"][0]["alternatives"][0]["transcript"]
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error extracting transcript from Deepgram response: {e}")
            print(f"Deepgram response: {dg_data}")
            return {"error": "Speech recognition failed - could not extract transcript"}

        if not transcript or not transcript.strip():
            return {"error": "No speech detected"}

        translated = await translate_text(
            TranslateTextRequest(
                text=transcript,
                source_language=sourceLang,
                target_language=targetLang
            )
        )

        return translated

    except Exception as e:
        print(f"Translation error for languages {sourceLang} -> {targetLang}: {str(e)}")
        return {"error": str(e)}
