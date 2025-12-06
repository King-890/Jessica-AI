from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from configs.settings import Settings
from api.middleware import LocalhostOnlyMiddleware
from api.errors import register_exception_handlers
from api.routes.internal import router as internal_router
from api.routes.ws import router as ws_router
from api.routes.memory import router as memory_router
from api.routes.files import router as files_router
from api.routes.system import router as system_router
from api.routes.projects import router as projects_router
from api.routes.codegen import router as codegen_router
from api.routes.plugins import router as plugins_router
from api.routes.scheduler import router as scheduler_router
from api.routes.terminal import router as terminal_router
from api.routes.browser import router as browser_router
from api.routes.search import router as search_router
from api.routes.ws_terminal import router as ws_terminal_router
from scheduler.worker import worker_singleton
from api.security import RateLimitMiddleware, ApiTokenMiddleware
from api.routes.voice import router as voice_router
from api.routes.watchdog import router as watchdog_router
from watchdog.worker import watchdog_singleton


settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        worker_singleton.start()
    except Exception:
        # In production, log error; keep app running
        pass
    try:
        if settings.enable_watchdog:
            watchdog_singleton.start()
    except Exception:
        pass
        
    yield
    
    # Shutdown
    try:
        worker_singleton.stop()
    except Exception:
        pass
    try:
        watchdog_singleton.stop()
    except Exception:
        pass

app = FastAPI(title="Jessica AI Assistant Internal API", lifespan=lifespan)

# Enforce local-only access via middleware (configurable)
if settings.enforce_local_only:
    app.add_middleware(LocalhostOnlyMiddleware)

# Restrict CORS to local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

# Internal routes under /internal
app.include_router(internal_router, prefix="/internal")
app.include_router(ws_router)
app.include_router(memory_router, prefix="/memory")
app.include_router(files_router, prefix="/files")
app.include_router(system_router, prefix="/system")
app.include_router(projects_router, prefix="/projects")
app.include_router(codegen_router, prefix="/codegen")
app.include_router(plugins_router, prefix="/plugins")
app.include_router(scheduler_router, prefix="/scheduler")
app.include_router(terminal_router, prefix="/terminal")
app.include_router(browser_router, prefix="/browser")
app.include_router(search_router, prefix="/search")
app.include_router(ws_terminal_router)
app.include_router(voice_router)
app.include_router(watchdog_router)


@app.get("/health")
def root_health():
    return {"status": "ok"}


# Security middlewares
app.add_middleware(RateLimitMiddleware, settings=settings)
app.add_middleware(ApiTokenMiddleware, settings=settings)