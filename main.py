from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class VideoRequest(BaseModel):
    video_id: str
    language: Optional[str] = None

@app.post("/transcribe")
async def transcribe_video(request: VideoRequest):
    try:
        # Primeiro, vamos listar todas as legendas disponíveis
        transcript_list = YouTubeTranscriptApi.list_transcripts(request.video_id)
        
        try:
            # Tenta pegar a legenda no idioma especificado
            if request.language:
                transcript = transcript_list.find_transcript([request.language])
            else:
                # Se não especificou idioma, tenta pegar qualquer uma disponível
                transcript = transcript_list.find_manually_created_transcript()
                if not transcript:
                    transcript = transcript_list.find_generated_transcript()
        
            formatted_transcript = ''
            for entry in transcript.fetch():
                formatted_transcript += f"[{entry['start']:.2f}s] {entry['text']}\n"
            
            return {
                "video_id": request.video_id,
                "transcript": formatted_transcript,
                "language": transcript.language_code,
                "success": True
            }
            
        except Exception:
            # Se não encontrou no idioma especificado, lista os idiomas disponíveis
            available_transcripts = transcript_list.manual_transcripts
            available_transcripts.update(transcript_list.generated_transcripts)
            
            available_languages = [
                {"code": t.language_code, "name": t.language} 
                for t in available_transcripts.values()
            ]
            
            return {
                "video_id": request.video_id,
                "success": False,
                "error": "Legenda não encontrada no idioma especificado",
                "available_languages": available_languages
            }
            
    except Exception as e:
        available_languages = []
        error_message = "Não foi possível encontrar legendas para este vídeo. " + \
                       "Verifique se o vídeo tem legendas habilitadas."
        
        return {
            "video_id": request.video_id,
            "success": False,
            "error": error_message,
            "available_languages": available_languages
        }