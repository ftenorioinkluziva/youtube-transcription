from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI()

class VideoRequest(BaseModel):
    video_id: str
    language: Optional[str] = "pt"

class TranscriptionResponse(BaseModel):
    video_id: str
    transcript: str
    success: bool
    error: Optional[str] = None

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_video(request: VideoRequest):
    try:
        # Obtém a transcrição
        transcript = YouTubeTranscriptApi.get_transcript(
            request.video_id, 
            languages=[request.language]
        )
        
        # Formata o texto da transcrição
        formatted_transcript = ''
        for entry in transcript:
            formatted_transcript += f"[{entry['start']:.2f}s] {entry['text']}\n"
        
        return TranscriptionResponse(
            video_id=request.video_id,
            transcript=formatted_transcript,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao transcrever vídeo: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)