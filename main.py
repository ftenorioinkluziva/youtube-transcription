from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class VideoRequest(BaseModel):
    video_id: str
    language: Optional[str] = None  # Torna o parâmetro opcional

@app.post("/transcribe")
async def transcribe_video(request: VideoRequest):
    try:
        # Se não especificar o idioma, pega a primeira legenda disponível
        if request.language:
            transcript = YouTubeTranscriptApi.get_transcript(request.video_id, languages=[request.language])
        else:
            transcript = YouTubeTranscriptApi.get_transcript(request.video_id)
        
        # Formata o texto da transcrição
        formatted_transcript = ''
        for entry in transcript:
            formatted_transcript += f"[{entry['start']:.2f}s] {entry['text']}\n"
        
        return {
            "video_id": request.video_id,
            "transcript": formatted_transcript,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao transcrever vídeo: {str(e)}"
        )