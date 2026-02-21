import os
from pathlib import Path
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_audio(audio_path: str) -> str:
    p = Path(audio_path)
    if not p.exists():
        raise FileNotFoundError(f"No existe el archivo: {audio_path}")

    transcription = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=p.open("rb")
    )

    return transcription.text
