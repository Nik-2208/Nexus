"""Production FastAPI server powering NEXUS platform and browser extension."""

import os
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, Header, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from nexus.config import BASE_DIR, DEFAULT_MODEL_FILENAME
from nexus.storage.db import NexusDatabase
from nexus.engine.workflow import NexusWorkflowEngine
from nexus.providers.demo import DemoProvider
from nexus.providers.local_gemma import LocalGemmaProvider

from nexus.providers.service import AIProviderService

app = FastAPI(title="NEXUS AI Failure Intelligence Engine")

# Permit loopback cross-origin requests from Chrome Extension (chrome-extension://)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^(chrome-extension://.*|http://127\.0\.0\.1:.*|http://localhost:.*)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

db = NexusDatabase()
workflow = NexusWorkflowEngine()
ai_service = AIProviderService(db=db)


# --- Pydantic Request Models ---
class PairRequest(BaseModel):
    pairing_code: str


class ProviderTogglePayload(BaseModel):
    provider: str  # 'local_gemma' or 'gemini'


class SessionEventPayload(BaseModel):
    provider: str
    url: str
    title: str
    event_type: str = "navigation"


class SelectionCapturePayload(BaseModel):
    provider: str
    url: str
    title: str
    content: str


class ImportTextPayload(BaseModel):
    provider: str
    title: str
    content: str
    import_method: str = "text"


class LocalChatPayload(BaseModel):
    message: str


# --- Public Web Endpoints ---
@app.get("/")
def get_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def get_status():
    provider_info = ai_service.get_status()
    active_name = provider_info["active_provider"]
    local_info = provider_info["local_gemma"]
    gemini_info = provider_info["gemini"]

    # Active provider status message
    if active_name == "local_gemma":
        if local_info["is_connected"]:
            status_msg = f"Local Gemma: Connected ({local_info['discovered_model']})"
        else:
            status_msg = f"Local Gemma: Offline ({local_info['details']})"
    else:
        if gemini_info["is_connected"]:
            status_msg = f"Gemini API: Connected ({gemini_info['discovered_model']})"
        else:
            status_msg = f"Gemini API: Not Ready ({gemini_info['details']})"

    return {
        "active_provider": active_name,
        "model_status": status_msg,
        "local_gemma": local_info,
        "gemini": gemini_info,
    }


@app.post("/api/provider")
def toggle_provider(payload: ProviderTogglePayload):
    try:
        active = ai_service.set_active_provider(payload.provider)
        status_info = ai_service.get_status()
        return {"status": "updated", "active_provider": active, "details": status_info}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Pairing & Extension Endpoints ---
@app.get("/api/pairing_code")
def get_pairing_code():
    code = db.generate_pairing_code()
    return {"pairing_code": code}


@app.post("/api/extension/pair")
def pair_extension(payload: PairRequest):
    token = db.verify_and_claim_pairing_code(payload.pairing_code)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired pairing code.")
    return {"token": token, "status": "paired"}


@app.post("/api/extension/event")
def record_event(payload: SessionEventPayload, x_nexus_token: Optional[str] = Header(None)):
    if not x_nexus_token or not db.validate_token(x_nexus_token):
        raise HTTPException(status_code=401, detail="Unauthorized extension request.")
    res = db.record_session_event(
        provider=payload.provider,
        url=payload.url,
        title=payload.title,
        event_type=payload.event_type,
    )
    return {"status": "recorded", "session": res}


@app.post("/api/capture")
def capture_selection(payload: SelectionCapturePayload, x_nexus_token: Optional[str] = Header(None)):
    if not x_nexus_token or not db.validate_token(x_nexus_token):
        raise HTTPException(status_code=401, detail="Unauthorized extension capture.")
    conv_id = db.store_conversation(
        provider=payload.provider,
        title=payload.title,
        content=payload.content,
        import_method="capture",
        source_url=payload.url,
    )
    return {"status": "captured", "conversation_id": conv_id}


# --- Conversations & Import ---
@app.get("/api/conversations")
def list_conversations():
    return db.list_conversations()


@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str):
    conv = db.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conv


@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    db.delete_conversation(conv_id)
    return {"status": "deleted"}


@app.post("/api/import_text")
def import_text(payload: ImportTextPayload):
    cid = db.store_conversation(
        provider=payload.provider,
        title=payload.title,
        content=payload.content,
        import_method=payload.import_method,
    )
    return {"status": "imported", "conversation_id": cid}


# --- Sessions & Activity ---
@app.get("/api/sessions")
def list_sessions():
    return db.list_tracked_sessions()


@app.get("/api/events")
def list_events():
    return db.list_activity_events()


# --- Failure Analysis Pipeline ---
@app.post("/api/run_analysis")
def run_analysis_endpoint():
    active_provider = ai_service.get_active_provider()
    report = workflow.run_analysis(provider=active_provider)
    return report.model_dump()


# --- Local & Gemini AI Chat ---
@app.post("/api/chat")
def ai_chat(payload: LocalChatPayload):
    # 1. Record incoming user message into SQLite
    db.store_chat_message(conversation_id="default", role="user", content=payload.message)

    try:
        res = ai_service.chat_or_analyze(payload.message)
        reply = res.get("choices", [{}])[0].get("message", {}).get("content", "No response content.")
        active_name = ai_service.get_active_provider_name()

        # 2. Record assistant reply into SQLite
        db.store_chat_message(conversation_id="default", role="assistant", content=reply)

        # 3. Run failure diagnostics pipeline on every database update
        try:
            active_provider = ai_service.get_active_provider()
            report = workflow.run_analysis(provider=active_provider)
            diagnostics_summary = {
                "findings_count": len(report.findings),
                "critical_violations": report.metrics.get("critical_violations", 0),
                "observed_decision_flips": report.metrics.get("observed_decision_flips", 0),
                "assumptions_identified": report.metrics.get("assumptions_identified", 0),
            }
        except Exception:
            diagnostics_summary = None

        return {
            "role": "assistant",
            "content": reply,
            "provider": active_name,
            "is_live_inference": True,
            "diagnostics": diagnostics_summary,
        }
    except Exception as e:
        active_name = ai_service.get_active_provider_name()
        err_msg = f"[{active_name.upper()} ERROR] {str(e)}"
        db.store_chat_message(conversation_id="default", role="assistant", content=err_msg)
        return {
            "role": "assistant",
            "content": err_msg,
            "provider": active_name,
            "is_live_inference": False,
        }


@app.get("/api/chat/messages")
def get_chat_history(conversation_id: str = "default"):
    return db.list_chat_messages(conversation_id=conversation_id)
