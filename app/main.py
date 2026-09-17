import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import os
import redis.asyncio as aioredis
from app.celery_app import run_workflow_task
from app.storage import get_presigned_url, USE_S3
from fastapi.responses import RedirectResponse

from fastapi import Request, Depends
from app.auth import get_current_user
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
limiter = Limiter(key_func=get_remote_address, storage_uri=REDIS_URL)


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator, Field

from app.graph.workflow import workflow_result_async
from app.latex_executer import render_latex_to_pdf
from app.resume_builder_tool import resume_builder

from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)

app = FastAPI()
from app.auth_routes import router as auth_router
app.include_router(auth_router)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

GENERATED_PDFS_DIR = Path(__file__).resolve().parent.parent / "generated_pdfs"
GENERATED_PDFS_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://majestic-cheesecake-80d98b.netlify.app",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WorkflowRequest(BaseModel):
    resume_text: str = Field(..., max_length=50000, description="The resume text content.")
    job_description: str = Field(..., max_length=50000, description="The job description content.")
    full_name: str | None = Field(None, max_length=150)
    email: str | None = Field(None, max_length=150)
    phone: str | None = Field(None, max_length=50)
    linkedin_url: str | None = Field(None, max_length=500)
    github_url: str | None = Field(None, max_length=500)

    @field_validator("resume_text", "job_description", mode="before")
    @classmethod
    def validate_required_text(cls, value, info):
        if value is None or str(value).strip() == "":
            raise ValueError(f"{info.field_name} is required.")
        return str(value).strip()


def _slugify(value: str, max_length: int = 40) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\s_-]", "", value)
    value = re.sub(r"[\s_-]+", "_", value).strip("_")
    return value[:max_length] or "candidate"


def _build_output_filename(full_name: str | None, role: str | None) -> str:
    name_part = _slugify(full_name) if full_name else "candidate"
    role_part = _slugify(role) if role else "resume"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid.uuid4().hex[:6]
    return f"{name_part}_{role_part}_{timestamp}_{unique_suffix}.pdf"


@app.get("/api")
async def api_root():
    return {"message": "Welcome to Resume Agent API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/health-full")
async def health_full():
    results = {}
    
    # 1. Redis Check
    try:
        await redis_client.ping()
        results["Redis"] = "Connected"
    except Exception as e:
        results["Redis"] = f"Failed: {str(e)}"
        
    # 2. OpenRouter Config Check
    import os
    if os.getenv("OPENROUTER_API_KEY"):
        results["OpenRouter"] = "Configured"
    else:
        results["OpenRouter"] = "Missing API Key"
        
    # 3. Supabase Check
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
        results["Supabase"] = "Configured"
    else:
        results["Supabase"] = "Missing Config"

    # 4. Storage Config Check
    from app.storage import USE_S3
    results["Storage"] = "S3 Configured" if USE_S3 else "Local Storage"
    
    return results



@app.get("/download-pdf/{filename}")
async def download_pdf(filename: str):
    if USE_S3:
        url = get_presigned_url(filename)
        if url:
            return RedirectResponse(url)
            
    # Local fallback
    pdf_path = GENERATED_PDFS_DIR / filename
    if not pdf_path.exists():
        dl_path = Path.home() / "Downloads" / filename
        if dl_path.exists():
            pdf_path = dl_path
        else:
            raise HTTPException(status_code=404, detail="PDF file not found.")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



@app.post("/jobs")
@limiter.limit("5/minute")
async def create_job(request: Request, payload: WorkflowRequest, user = Depends(get_current_user)):
    job_id = str(uuid.uuid4())
    job_data = {
        "status": "pending",
        "inputs": payload.model_dump(),
        "events": [],
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    # TTL of 2 hours — expired/zombie jobs are auto-cleaned from Redis
    await redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=7200)
    
    # Queue the Celery task
    run_workflow_task.delay(job_id, payload.model_dump())
    
    return {"job_id": job_id}

@app.get("/jobs/{job_id}")
@limiter.limit("120/minute")
async def get_job(request: Request, job_id: str, user = Depends(get_current_user)):
    job_data_str = await redis_client.get(f"job:{job_id}")
    if not job_data_str:
        raise HTTPException(404, "Job not found")
    job_data = json.loads(job_data_str)

    # Auto-timeout: if job is stuck in running/pending for >10 minutes, mark it as error
    if job_data.get("status") in ("running", "pending"):
        created_at_str = job_data.get("created_at")
        if created_at_str:
            try:
                from datetime import timedelta
                created_at = datetime.fromisoformat(created_at_str)
                age = datetime.now(timezone.utc) - created_at
                if age > timedelta(minutes=5):
                    job_data["status"] = "error"
                    job_data["error"] = (
                        "Job timed out after 5 minutes. "
                        "The worker may have crashed. Please try again."
                    )
                    await redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=3600)
            except Exception:
                pass

    return job_data



# Serve Flutter Web frontend in production
frontend_build = Path(__file__).resolve().parent.parent / "frontend" / "build" / "web"
if frontend_build.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_build)), name="static")
    
    @app.get("/{full_path:path}")
    async def serve_flutter_app(full_path: str):
        # Serve static files if they exist
        file_path = frontend_build / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Fallback to index.html for Flutter path routing
        return FileResponse(frontend_build / "index.html")
