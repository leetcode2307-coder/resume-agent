import asyncio
import json
import logging
import os
from pathlib import Path

import redis.asyncio as aioredis

from app.graph.workflow import workflow_result_async
from app.latex_executer import render_latex_to_pdf
from app.resume_builder_tool import resume_builder
from app.storage import upload_pdf_to_s3
# We can't import GENERATED_PDFS_DIR from app.main easily without causing circular imports
# or triggering FastAPI initialization. Let's redefine it here or move it.
GENERATED_PDFS_DIR = Path(__file__).resolve().parent.parent / "generated_pdfs"
GENERATED_PDFS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# redis_client instantiated inside process_job_async to avoid event loop issues

def _build_output_filename(full_name: str | None, role: str | None) -> str:
    from datetime import datetime, timezone
    import uuid
    import re
    def _slugify(value: str, max_length: int = 40) -> str:
        value = (value or "").strip().lower()
        value = re.sub(r"[^a-z0-9\s_-]", "", value)
        value = re.sub(r"[\s_-]+", "_", value).strip("_")
        return value[:max_length] or "candidate"
    
    name_part = _slugify(full_name) if full_name else "candidate"
    role_part = _slugify(role) if role else "resume"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    unique_suffix = uuid.uuid4().hex[:6]
    return f"{name_part}_{role_part}_{timestamp}_{unique_suffix}.pdf"

async def process_job_async(job_id: str, request: dict):
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        final_state = {}
        
        job_data_str = await redis_client.get(f"job:{job_id}")
        if job_data_str:
            job_data = json.loads(job_data_str)
            job_data["status"] = "running"
            await redis_client.set(f"job:{job_id}", json.dumps(job_data))
        else:
            job_data = {"status": "running", "events": [], "result": None, "error": None}
            await redis_client.set(f"job:{job_id}", json.dumps(job_data))

        async for event in workflow_result_async(
            resume_text=request.get("resume_text", ""),
            job_description=request.get("job_description", ""),
            full_name=request.get("full_name"),
            email=request.get("email"),
            phone=request.get("phone"),
            linkedin_url=request.get("linkedin_url"),
            github_url=request.get("github_url"),
        ):
            if not isinstance(event, dict):
                continue
            
            job_data_str = await redis_client.get(f"job:{job_id}")
            job_data = json.loads(job_data_str) if job_data_str else {"status": "running", "events": []}
            job_data["events"].append(event)
            
            if event.get("event") == "workflow_error":
                job_data["status"] = "error"
                job_data["error"] = event.get("error")
                await redis_client.set(f"job:{job_id}", json.dumps(job_data))
                return

            if event.get("event") == "workflow_state_ready":
                final_state = dict(event.get("data", {}).get("state", {}))
                
            await redis_client.set(f"job:{job_id}", json.dumps(job_data))
                
        if not final_state:
            final_state = {}

        final_state.update({
            "full_name": request.get("full_name"),
            "email": request.get("email"),
            "phone": request.get("phone"),
            "linkedin_url": request.get("linkedin_url"),
            "github_url": request.get("github_url"),
        })

        output_filename = _build_output_filename(request.get("full_name"), final_state.get("role"))
        output_path = GENERATED_PDFS_DIR / output_filename

        latex_code = await asyncio.to_thread(resume_builder, final_state)
        pdf_path = None
        try:
            pdf_path = await asyncio.to_thread(
                render_latex_to_pdf,
                latex_source=latex_code,
                output_pdf=output_path,
            )
            if pdf_path:
                await asyncio.to_thread(upload_pdf_to_s3, str(pdf_path), output_filename)
        except Exception as pdf_exc:
            logger.warning(f"PDF generation failed (latex_code still preserved): {pdf_exc}")

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
        
        job_data_str = await redis_client.get(f"job:{job_id}")
        job_data = json.loads(job_data_str) if job_data_str else {"status": "running", "events": []}
        job_data["events"].append(final_response)
        job_data["result"] = final_response["data"]
        job_data["status"] = "completed"
        await redis_client.set(f"job:{job_id}", json.dumps(job_data))

    except Exception as exc:
        logger.exception(f"Job {job_id} failed")
        job_data_str = await redis_client.get(f"job:{job_id}")
        job_data = json.loads(job_data_str) if job_data_str else {"status": "error", "events": []}
        job_data["status"] = "error"
        job_data["error"] = str(exc)
        await redis_client.set(f"job:{job_id}", json.dumps(job_data))
    finally:
        await redis_client.aclose()
