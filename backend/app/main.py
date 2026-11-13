import os
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, HttpUrl
from openai import OpenAI

app = FastAPI(title="YouTube Video Intelligence Pro API", version="0.2.0")
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_AUDIO = {".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"}
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    transcript: str | None = None


class TranscriptRequest(BaseModel):
    url: HttpUrl
    timestamps: bool = True


def extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    video_id = None
    if host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/").split("/")[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            from urllib.parse import parse_qs
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            video_id = parsed.path.split("/")[2]
    if not video_id or not VIDEO_ID_RE.fullmatch(video_id):
        raise HTTPException(status_code=400, detail="URL do YouTube inválida ou ID não reconhecido.")
    return video_id


async def get_oembed(url: str) -> dict:
    endpoint = "https://www.youtube.com/oembed"
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=False) as client:
            response = await client.get(endpoint, params={"url": url, "format": "json"})
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title"),
                "author_name": data.get("author_name"),
                "thumbnail_url": data.get("thumbnail_url"),
                "provider_name": data.get("provider_name"),
                "source": "youtube_oembed",
            }
    except (httpx.HTTPError, ValueError):
        pass
    return {"source": "unavailable"}


async def get_apify_transcript(url: str, timestamps: bool = True) -> dict:
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise HTTPException(status_code=503, detail="APIFY_TOKEN não configurado no servidor.")
    endpoint = "https://api.apify.com/v2/acts/scrape-creators~best-youtube-transcripts-scraper/run-sync-get-dataset-items"
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(endpoint, params={"token": token}, json={"videoUrls": [url]})
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Provedor de transcrição respondeu HTTP {response.status_code}.")
        rows = response.json()
        if not isinstance(rows, list) or not rows:
            return {"status": "unavailable", "reason": "O provedor não retornou resultados."}
        row = rows[0]
        full_text = row.get("transcript_only_text")
        segments = row.get("transcript") if timestamps else None
        if not full_text and not segments:
            return {"status": "unavailable", "reason": "O vídeo não possui legendas acessíveis ou o ator não retornou transcrição.", "video_id": row.get("id")}
        return {"status": "ok", "video_id": row.get("id"), "text": full_text, "segments": segments, "source": "Apify Best Youtube Transcripts Scraper"}
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="A consulta de transcrição excedeu o tempo limite.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Não foi possível conectar ao provedor de transcrição.") from exc


@app.post("/v1/youtube/transcript")
async def youtube_transcript(payload: TranscriptRequest):
    url = str(payload.url)
    extract_video_id(url)
    result = await get_apify_transcript(url, payload.timestamps)
    return {"url": url, "transcript": result}


class YouTubeAnalysisRequest(BaseModel):
    url: HttpUrl
    timestamps: bool = False


@app.post("/v1/youtube/analyze")
async def youtube_analyze(payload: YouTubeAnalysisRequest):
    """Extract an accessible transcript and analyze it with a low-cost OpenAI model."""
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY não configurada. Adicione-a nos Environment Variables do Render.")
    url = str(payload.url)
    video_id = extract_video_id(url)
    metadata = await get_oembed(url)
    transcript_result = await get_apify_transcript(url, payload.timestamps)
    if transcript_result.get("status") != "ok" or not transcript_result.get("text"):
        raise HTTPException(status_code=422, detail={
            "message": "Não foi possível obter uma transcrição para este vídeo.",
            "transcript": transcript_result,
            "metadata": metadata,
        })

    # Keep the request bounded to control API cost; never imply omitted portions were analyzed.
    transcript_text = transcript_result["text"]
    max_chars = int(os.getenv("MAX_ANALYSIS_CHARS", "60000"))
    analyzed_text = transcript_text[:max_chars]
    truncated = len(transcript_text) > len(analyzed_text)
    model = os.getenv("OPENAI_ANALYSIS_MODEL", "gpt-4o-mini")
    system_prompt = (
        "Você é um analista audiovisual e pesquisador rigoroso. Analise SOMENTE o conteúdo "
        "da transcrição fornecida. Não invente imagens, sons, fatos externos, fontes ou citações. "
        "Separe claramente: (1) o que o apresentador afirma, (2) interpretações/inferências, "
        "(3) pontos que exigem verificação externa. Não trate alegações como fatos comprovados. "
        "Se a transcrição estiver incompleta ou truncada, declare essa limitação. "
        "Responda em português brasileiro, com títulos e linguagem clara."
    )
    user_prompt = (
        f"URL: {url}\\nTítulo: {metadata.get('title') or 'não disponível'}\\n"
        f"Canal: {metadata.get('author_name') or 'não disponível'}\\n"
        f"Transcrição (pode estar limitada a {max_chars} caracteres):\\n"
        f"{analyzed_text}\\n\\n"
        "Produza: resumo executivo; tema e objetivo; tópicos principais; argumentos e evidências "
        "citadas pelo próprio vídeo; afirmações factuais que precisam de checagem; possíveis "
        "falhas lógicas/retóricas; conclusões; perguntas em aberto. Para cada afirmação não "
        "verificada, indique 'não verificada nesta etapa'. Não faça fact-check externo."
    )
    try:
        client = OpenAI()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1800,
        )
        report = completion.choices[0].message.content or ""
        usage = completion.usage
        return {
            "status": "analyzed",
            "video_id": video_id,
            "url": url,
            "metadata": metadata,
            "transcript_source": transcript_result.get("source"),
            "transcript_characters_total": len(transcript_text),
            "transcript_characters_analyzed": len(analyzed_text),
            "transcript_truncated": truncated,
            "analysis_model": model,
            "analysis": report,
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else None,
                "completion_tokens": usage.completion_tokens if usage else None,
                "total_tokens": usage.total_tokens if usage else None,
            },
            "scope_note": "Análise baseada apenas na transcrição. Imagens, áudio original e verificação externa ainda não foram analisados.",
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha na análise com IA: {type(exc).__name__}") from exc

@app.get("/health")
def health():
    return {"status": "ok", "service": "youtube-video-intelligence-pro-api"}


@app.post("/v1/analyze")
async def analyze(payload: AnalyzeRequest):
    url = str(payload.url)
    video_id = extract_video_id(url)
    metadata = await get_oembed(url)
    transcript = (payload.transcript or "").strip()
    return {
        "video_id": video_id,
        "url": url,
        "metadata": metadata,
        "transcript": {
            "status": "provided" if transcript else "missing",
            "text": transcript or None,
            "characters": len(transcript),
        },
        "analysis_status": "ready_for_analysis" if transcript else "awaiting_authorized_transcript_or_media",
        "limitations": [
            "Metadados públicos via oEmbed não equivalem a acesso ao conteúdo audiovisual.",
            "Este MVP não contorna vídeos privados, restrições, autenticação ou mecanismos de proteção.",
            "Sem legenda acessível ou mídia fornecida/autorizada, não há base para resumir o conteúdo."
        ],
    }


@app.post("/v1/transcribe")
async def transcribe(file: UploadFile = File(...), language: str | None = Form(default=None)):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY não configurada no servidor.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_AUDIO:
        raise HTTPException(status_code=415, detail=f"Formato não suportado. Use: {', '.join(sorted(ALLOWED_AUDIO))}")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo excede 25 MB. Divida o áudio em partes menores.")
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(data)
            temp_path = temp.name
        client = OpenAI()
        with open(temp_path, "rb") as audio:
            result = client.audio.transcriptions.create(
                model=os.getenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-transcribe"),
                file=audio,
                language=language or None,
            )
        return {"status": "transcribed", "model": os.getenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-transcribe"), "text": result.text}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha na transcrição: {type(exc).__name__}") from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        await file.close()
