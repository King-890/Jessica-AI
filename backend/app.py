from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
from contextlib import asynccontextmanager
from .routes.auth import validate_token
from .ai_core import jessica_core
from .speak import speak
from .memory import save_interaction
from .vector_routes import router as vector_router
from .vector_memory import search as vector_search, store_interaction as vector_store
from configs.settings import settings
from .updater import run_periodic_updates, update_jessica
from .cron import run_cron
from .voice_loop import start_background_listener
from .voice.listener import start as start_voice_listener, stop as stop_voice_listener
import yaml
from .system_watcher import start as start_watcher, stop as stop_watcher, router as system_router, set_publisher as set_watcher_publisher
from .memory_routes import router as memory_router
from .log_stream import router as log_router, publish_log_event
from .config_routes import router as config_router
from .knowledge_fetcher import run_knowledge_updates
from .diagnostics_routes import router as diagnostics_router
from .dashboard_routes import router as dashboard_router
from .performance_routes import router as performance_router
from .update_routes import router as updates_router
from .ide_routes import router as ide_router
from .voice_routes import router as voice_router
from .security import AuthTokenMiddleware, RolePermissionMiddleware, ResponseValidationMiddleware
from .knowledge_routes import router as knowledge_router
from .memory_summary_routes import router as memory_summary_router
from .security import SupabaseAuthMiddleware
from .routes.auth_status import router as auth_status_router
from .status_routes import router as status_router
import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initial state mirrors settings
    app.state.auto_update_enabled = settings.enable_auto_update
    app.state.cron_update_enabled = settings.enable_cron_update
    app.state.cron_update_expression = settings.cron_update_expression
    app.state.start_time = time.time()

    # --- Startup ---
    # Launch auto updater in the background if enabled
    if settings.enable_auto_update:
        app.state.update_task = asyncio.create_task(
            run_periodic_updates(settings.auto_update_interval_hours)
        )
    # Or use cron schedule if enabled
    if settings.enable_cron_update:
        app.state.update_cron_task = asyncio.create_task(
            run_cron(update_jessica, settings.cron_update_expression)
        )
    # Voice wake-word listener
    if settings.enable_voice_mode:
        try:
            # Load voice settings if available
            wake_phrase = "hey jessica"
            adapter = "speech_recognition"
            whisper_model = "base"
            try:
                with open(os.path.join("configs", "voice_settings.yaml"), "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                wake_phrase = cfg.get("wake_phrase", wake_phrase)
                adapter = cfg.get("stt_adapter", adapter)
                whisper_model = cfg.get("whisper_model", whisper_model)
            except Exception:
                pass
            start_voice_listener(wake_phrase=wake_phrase, adapter=adapter, whisper_model=whisper_model)
            app.state.voice_mode_enabled = True
        except Exception:
            app.state.voice_mode_enabled = False
    # System watcher
    try:
        start_watcher(app)
        # Attach log stream publisher for live SSE
        set_watcher_publisher(publish_log_event)
    except Exception:
        pass
    # Knowledge auto-updates
    if settings.enable_knowledge_auto_update:
        try:
            app.state.knowledge_task = asyncio.create_task(
                run_knowledge_updates(settings.knowledge_auto_update_interval_hours)
            )
        except Exception:
            pass

    # Yield to run application
    try:
        yield
    finally:
        # --- Shutdown ---
        task = getattr(app.state, "update_task", None)
        if task:
            task.cancel()
        cron_task = getattr(app.state, "update_cron_task", None)
        if cron_task:
            cron_task.cancel()
        # Stop voice listener
        try:
            stop_voice_listener()
        except Exception:
            pass
        try:
            stop_watcher(app)
        except Exception:
            pass
        # Stop knowledge updater
        try:
            kt = getattr(app.state, "knowledge_task", None)
            if kt:
                kt.cancel()
        except Exception:
            pass


app = FastAPI(lifespan=lifespan)

# Allow local UI origins
allowed_origins = [
    "http://127.0.0.1",
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security & validation middlewares
app.add_middleware(AuthTokenMiddleware, require_api_token=settings.require_api_token)
app.add_middleware(SupabaseAuthMiddleware)
app.add_middleware(RolePermissionMiddleware)
app.add_middleware(ResponseValidationMiddleware)

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/generate")
async def generate(req: Request):
    data = await req.json()
    token = data.get("token")
    message = data.get("message", "")

    if not validate_token(token):
        return JSONResponse({"error": "Invalid token"}, status_code=401)

    # Retrieve semantic context before generation
    try:
        related = vector_search(message, k=5)
    except Exception:
        related = []
    context_lines = []
    for item in related:
        txt = (item.get("content") or "").strip()
        if txt:
            context_lines.append(f"- {txt[:300]}")
    context_blob = "\n".join(context_lines)
    enriched = message if not context_blob else f"{message}\n\nRelevant context:\n{context_blob}"

    response = jessica_core(enriched)
    # Speak the response and record the interaction
    speak(response)
    save_interaction(message, response)
    # Store interaction vectors
    try:
        vector_store(message, response, tags=["chat"])
    except Exception:
        pass
    return {"response": response}


app.include_router(system_router)
app.include_router(memory_router)
app.include_router(memory_summary_router)
app.include_router(log_router)
app.include_router(config_router)
app.include_router(auth_status_router)
app.include_router(status_router)
app.include_router(vector_router)
app.include_router(diagnostics_router)
app.include_router(dashboard_router)
app.include_router(performance_router)
app.include_router(updates_router)
app.include_router(voice_router)
app.include_router(knowledge_router)
app.include_router(ide_router)