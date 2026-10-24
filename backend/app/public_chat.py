"""Public widget transport, ephemeral attachments and optional speech transcription.

Feedback is stored separately; chat content stays transient unless explicitly shared with feedback.
"""
import asyncio
import json
import os
import re
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta, timezone
from io import BytesIO
from secrets import token_urlsafe
from threading import Lock
from typing import Literal

import pymupdf
import pytesseract
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from groq import Groq
from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .config import settings
from .db import session
from .public_assistant import _check_rate_limit, handle_public_assistant
from .voice import validate_audio


@asynccontextmanager
async def lifespan(app):
    async def sweep():
        while True:
            cleanup_uploads()
            await asyncio.sleep(30)
    task = asyncio.create_task(sweep())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task
    with _upload_lock:
        _uploads.clear()


router = APIRouter(prefix="/api/public/assistant", tags=["public chat"], lifespan=lifespan)
register_heif_opener()
MAX_FILE = 10*1024*1024
TTL = min(86400, max(60, int(os.getenv("PUBLIC_UPLOAD_TTL_SECONDS", str(settings().public_upload_ttl_seconds)))))
_uploads: dict[str, dict] = {}
_upload_lock = Lock()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    attachments: list[str] = Field(default_factory=list, max_length=5)
    language: Literal["en"] = "en"


def cleanup_uploads():
    with _upload_lock:
        for key in list(_uploads):
            if _uploads[key]["expires"] <= time.monotonic():
                del _uploads[key]


def extract_file(content, mime):
    text = ""
    actual = ""
    if content.startswith(b"%PDF-"):
        actual = "application/pdf"
        try:
            with pymupdf.open(stream=content, filetype="pdf") as document:
                if document.is_encrypted or len(document) > 20:
                    raise HTTPException(422, "Use an unlocked PDF with at most 20 pages.")
                text = "\n".join(page.get_text()[:10000] for page in document)[:30000]
        except (pymupdf.FileDataError, RuntimeError):
            raise HTTPException(422, "The PDF cannot be read. Try a different file.") from None
    else:
        try:
            with Image.open(BytesIO(content)) as image:
                actual = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp", "HEIF": "image/heic"}.get(image.format, "")
                if not actual or image.width*image.height > 20000000:
                    raise HTTPException(422, "Use a JPG, PNG or WebP below 20 million pixels. HEIC is also supported.")
                image.load()
                if settings().tesseract_cmd:
                    pytesseract.pytesseract.tesseract_cmd = settings().tesseract_cmd
                try:
                    text = pytesseract.image_to_string(image, timeout=8)[:30000]
                except (pytesseract.TesseractNotFoundError, RuntimeError):
                    raise HTTPException(503, "Image reading is unavailable on this server. Use a text PDF or type your question.") from None
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning):
            raise HTTPException(422, "This file is not a readable supported image or PDF.") from None
    if mime != actual and not (actual == "image/heic" and mime == "image/heif"):
        raise HTTPException(415, "File content does not match its declared type.")
    if re.search(r"passport|identity card|credit card|card number|national insurance|\bP<|(?:\d[ -]?){13,19}", text, re.I):
        raise HTTPException(422, "Identity and payment documents cannot be used in public chat. The file was discarded.")
    if not text.strip():
        raise HTTPException(422, "No readable text found. Use a text PDF or type a short question.")
    return actual, text


@router.post("/upload")
def upload(request: Request, file: UploadFile = File(...), consent: bool = Form(False)):
    _check_rate_limit("upload:"+(request.client.host if request.client else "unknown"))
    if not consent:
        raise HTTPException(422, "Confirm temporary processing before uploading. Do not upload identity or payment documents.")
    cleanup_uploads()
    content = file.file.read(MAX_FILE+1)
    if not content or len(content) > MAX_FILE:
        raise HTTPException(413, "Use a non-empty file below 10 MB.")
    mime, text = extract_file(content, file.content_type)
    key = token_urlsafe(32)
    with _upload_lock:
        if len(_uploads) >= 100:
            raise HTTPException(503, "Temporary attachment capacity reached. Please type your question.")
        _uploads[key] = {"text": text, "expires": time.monotonic()+max(1, TTL-30)}
    return {"attachment_id": key, "mime": mime, "size": len(content),
            "expires_at": (datetime.now(timezone.utc)+timedelta(seconds=max(1, TTL-30))).isoformat(),
            "notice": "Raw file discarded immediately. Extracted text is temporary, untrusted context; no AI provider receives it."}


@router.delete("/upload/{attachment_id}")
def remove_upload(attachment_id: str):
    with _upload_lock:
        _uploads.pop(attachment_id, None)
    return {"deleted": True}


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def stream(body: ChatRequest, request: Request, db: Session = Depends(session)):
    if not body.message.strip():
        raise HTTPException(422, "Enter a question.")
    cleanup_uploads()
    with _upload_lock:
        if any(key not in _uploads for key in body.attachments):
            raise HTTPException(410, "An attachment expired or was removed. Attach it again or send text only.")
        contexts = [_uploads.pop(key)["text"] for key in body.attachments]
    # Attachments are data; never execute instructions or turn extracted policy wording into coverage claims.
    result = await handle_public_assistant(body, request, db)
    reply = result.reply
    if contexts:
        reply += " I read the attachment as untrusted text. I cannot verify its policy terms or your coverage; ask a general question about an insurance term."
    async def events():
        yield sse("meta", {"mode": "reviewed-knowledge", "notice": "Pre-reviewed guidance delivered progressively; no model generation."})
        words = reply.split(" ")
        for i in range(0, len(words), 4):
            if await request.is_disconnected():
                return
            yield sse("token", {"text": (" " if i else "")+" ".join(words[i:i+4])})
            await asyncio.sleep(.035)
        yield sse("suggestions", {"items": ["What's an excess?", "What isn't covered?", "Talk to an adviser"]})
        if result.ticket_ref:
            yield sse("handoff", {"ticket_ref": result.ticket_ref, "delivery": "demo-only"})
        yield sse("done", {"intent": result.intent, "actions": [{"label": "Contact & support", "href": "/contact"}, {"label": "Get a synthetic quote", "href": "/get-cover/quote"}]})
    return StreamingResponse(events(), media_type="text/event-stream", headers={"X-Accel-Buffering": "no"})


@router.post("/transcribe")
def transcribe(request: Request, file: UploadFile = File(...), consent: bool = Form(False), language: Literal["en"] = Form("en")):
    _check_rate_limit("speech:"+(request.client.host if request.client else "unknown"))
    if not consent:
        raise HTTPException(422, "Consent to sending this recording to Groq is required.")
    key = os.environ.get("GROQ_API_KEY", settings().groq_api_key)
    if not key:
        raise HTTPException(503, "Voice transcription is not configured. Please type your message.")
    content = file.file.read(MAX_FILE+1)
    validate_audio(content)
    try:
        result = Groq(api_key=key, timeout=20).audio.transcriptions.create(
            file=("recording.webm", content), model="whisper-large-v3-turbo", language="en")
        return {"text": result.text[:2000], "language": language, "retained": False}
    except Exception:
        raise HTTPException(503, "Transcription could not finish. Try again or type your message.") from None


class Handoff(BaseModel):
    topic: Literal["General question", "Complaint", "Extra support"] = "General question"


@router.post("/handoff")
async def handoff(body: Handoff, request: Request, db: Session = Depends(session)):
    return await handle_public_assistant(ChatRequest(message=f"human adviser {body.topic}"), request, db)
