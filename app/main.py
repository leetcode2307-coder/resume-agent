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
from pydantic import BaseModel, field_validator

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
    resume_text: str
    job_description: str
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None

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
                if age > timedelta(minutes=10):
                    job_data["status"] = "error"
                    job_data["error"] = (
                        "Job timed out after 10 minutes. "
                        "The worker may have crashed. Please try again."
                    )
                    await redis_client.set(f"job:{job_id}", json.dumps(job_data), ex=3600)
            except Exception:
                pass

    return job_data

@app.post("/workflow-result")
@limiter.limit("5/minute")
async def workflow_result(request: Request, payload: WorkflowRequest, user = Depends(get_current_user)):
    async def event_generator():
        final_state = {}

        try:
            queue = asyncio.Queue()

            async def consume_workflow():
                try:
                    async for event in workflow_result_async(
                        resume_text=payload.resume_text,
                        job_description=payload.job_description,
                        full_name=payload.full_name,
                        email=payload.email,
                        phone=payload.phone,
                        linkedin_url=payload.linkedin_url,
                        github_url=payload.github_url,
                    ):
                        await queue.put(("event", event))
                    await queue.put(("done", None))
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    await queue.put(("error", e))

            consumer_task = asyncio.create_task(consume_workflow())

            while True:
                try:
                    msg_type, msg_data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    
                    if msg_type == "done":
                        break
                    elif msg_type == "error":
                        raise msg_data
                        
                    event = msg_data
                    if not isinstance(event, dict):
                        continue

                    if event.get("event") == "workflow_error":
                        yield "data: " + json.dumps(event, default=str) + "\n\n"
                        consumer_task.cancel()
                        return

                    if event.get("event") == "workflow_state_ready":
                        final_state = dict(event.get("data", {}).get("state", {}))
                        continue

                    yield "data: " + json.dumps(event, default=str) + "\n\n"
                    
                except asyncio.TimeoutError:
                    # Keep-alive ping to prevent client/proxy from dropping the idle connection
                    yield 'data: {"event": "ping"}\n\n'
                    continue

            if not final_state:
                final_state = {}

            final_state["full_name"] = payload.full_name
            final_state["email"] = payload.email
            final_state["phone"] = payload.phone
            final_state["linkedin_url"] = payload.linkedin_url
            final_state["github_url"] = payload.github_url

            if not final_state.get("resume_text"):
                raise ValueError("Final workflow state is missing resume_text.")

            output_filename = _build_output_filename(
                full_name=payload.full_name,
                role=final_state.get("role"),
            )
            output_path = GENERATED_PDFS_DIR / output_filename

            # 1. Try LaTeX compilation
            pdf_path = None
            latex_code = ""
            latex_code = await asyncio.to_thread(resume_builder, final_state)

            try:
                pdf_path = await asyncio.to_thread(
                    render_latex_to_pdf,
                    latex_source=latex_code,
                    output_pdf=output_path,
                )
            except Exception as pdf_exc:
                logger.warning(f"PDF rendering failed, latex_code preserved: {pdf_exc}")

            final_response = {
                "event": "workflow_completed",
                "agent": "workflow",
                "data": {
                    "state": final_state,
                    "pdf_filename": output_filename if pdf_path else None,
                    "pdf_path": str(pdf_path) if pdf_path else None,
                    "latex_code": latex_code,
                },
            }

            yield "data: " + json.dumps(final_response, default=str) + "\n\n"

        except asyncio.CancelledError:
            logger.warning("Client disconnected while streaming workflow events.")
            raise
        except Exception as exc:
            logger.exception("Workflow request failed")
            yield "data: " + json.dumps(
                {
                    "event": "workflow_error",
                    "agent": "workflow",
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
                default=str,
            ) + "\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

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
