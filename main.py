from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import re
import json
from typing import Optional, List

app = FastAPI()

class VideoRequest(BaseModel):
    video_id: str
    language: Optional[str] = None

class TranscriptResponse(BaseModel):
    text: str
    duration: float
    offset: float
    lang: str

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'

@app.post("/transcribe")
async def transcribe_video(request: VideoRequest):
    try:
        # Faz a requisição para a página do vídeo
        async with httpx.AsyncClient() as client:
            headers = {
                'User-Agent': USER_AGENT
            }
            if request.language:
                headers['Accept-Language'] = request.language

            response = await client.get(
                f'https://www.youtube.com/watch?v={request.video_id}',
                headers=headers
            )
            
            html = response.text
            
            # Procura pelos dados de legendas
            captions_data = html.split('"captions":')[1].split(',"videoDetails')[0]
            captions = json.loads(captions_data)
            
            if 'playerCaptionsTracklistRenderer' not in captions:
                raise Exception("No captions available")
                
            caption_tracks = captions['playerCaptionsTracklistRenderer'].get('captionTracks', [])
            
            if not caption_tracks:
                raise Exception("No caption tracks found")
                
            # Pega a primeira legenda ou a do idioma especificado
            target_track = None
            if request.language:
                target_track = next(
                    (track for track in caption_tracks if track['languageCode'] == request.language),
                    caption_tracks[0]
                )
            else:
                target_track = caption_tracks[0]
                
            # Obtém o XML da legenda
            transcript_response = await client.get(
                target_track['baseUrl'],
                headers=headers
            )
            
            transcript_xml = transcript_response.text
            
            # Parse do XML para extrair o texto
            pattern = r'<text start="([^"]*)" dur="([^"]*)">([^<]*)<\/text>'
            matches = re.finditer(pattern, transcript_xml)
            
            transcript = []
            for match in matches:
                transcript.append({
                    "text": match.group(3),
                    "duration": float(match.group(2)),
                    "offset": float(match.group(1)),
                    "lang": target_track['languageCode']
                })
            
            return {
                "video_id": request.video_id,
                "transcript": transcript,
                "success": True,
                "language": target_track['languageCode']
            }
            
    except Exception as e:
        return {
            "video_id": request.video_id,
            "success": False,
            "error": str(e)
        }