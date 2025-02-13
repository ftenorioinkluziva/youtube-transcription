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
            
            # Tenta encontrar os dados de legendas de diferentes maneiras
            try:
                # Primeira tentativa: procurar por captions
                if '"captions":' not in html:
                    return {
                        "video_id": request.video_id,
                        "success": False,
                        "error": "No captions data found in the video page"
                    }

                # Divide e pega a parte que contém os dados das legendas
                captions_parts = html.split('"captions":')
                if len(captions_parts) < 2:
                    return {
                        "video_id": request.video_id,
                        "success": False,
                        "error": "Could not parse captions data"
                    }

                # Pega o JSON das legendas
                captions_json = captions_parts[1].split(',"videoDetails')[0].strip()
                captions = json.loads(captions_json)
                
                if not captions or 'playerCaptionsTracklistRenderer' not in captions:
                    return {
                        "video_id": request.video_id,
                        "success": False,
                        "error": "No captions renderer found"
                    }

                caption_tracks = captions['playerCaptionsTracklistRenderer'].get('captionTracks', [])
                
                if not caption_tracks:
                    return {
                        "video_id": request.video_id,
                        "success": False,
                        "error": "No caption tracks available"
                    }

                # Pega a primeira legenda disponível
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
                
                if not transcript:
                    return {
                        "video_id": request.video_id,
                        "success": False,
                        "error": "Could not extract transcript text"
                    }

                return {
                    "video_id": request.video_id,
                    "transcript": transcript,
                    "success": True,
                    "language": target_track['languageCode']
                }
                
            except json.JSONDecodeError as e:
                return {
                    "video_id": request.video_id,
                    "success": False,
                    "error": f"Failed to parse JSON: {str(e)}"
                }
                
    except Exception as e:
        return {
            "video_id": request.video_id,
            "success": False,
            "error": f"Error processing video: {str(e)}"
        }