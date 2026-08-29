import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, field_validator

from app.graph.workflow import workflow_result_async
from app.latex_executer import render_latex_to_pdf
from app.resume_builder_tool import resume_builder

logger = logging.getLogger(__name__)

app = FastAPI()

GENERATED_PDFS_DIR = Path(__file__).resolve().parent.parent / "generated_pdfs"
GENERATED_PDFS_DIR.mkdir(parents=True, exist_ok=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/")
async def root():
    return {"message": "Welcome to Resume Agent API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/download-pdf/{filename}")
async def download_pdf(filename: str):
    pdf_path = GENERATED_PDFS_DIR / filename
    if not pdf_path.exists():
        # Also check Downloads as fallback
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


@app.post("/workflow-result")
async def workflow_result(request: WorkflowRequest):
    async def event_generator():
        final_state = {}

        try:
            queue = asyncio.Queue()

            async def consume_workflow():
                try:
                    async for event in workflow_result_async(
                        resume_text=request.resume_text,
                        job_description=request.job_description,
                        full_name=request.full_name,
                        email=request.email,
                        phone=request.phone,
                        linkedin_url=request.linkedin_url,
                        github_url=request.github_url,
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

            final_state["full_name"] = request.full_name
            final_state["email"] = request.email
            final_state["phone"] = request.phone
            final_state["linkedin_url"] = request.linkedin_url
            final_state["github_url"] = request.github_url

            if not final_state.get("resume_text"):
                raise ValueError("Final workflow state is missing resume_text.")

            output_filename = _build_output_filename(
                full_name=request.full_name,
                role=final_state.get("role"),
            )
            output_path = GENERATED_PDFS_DIR / output_filename

            # 1. Try LaTeX compilation
            pdf_path = None
            latex_code = ""
            try:
                latex_code = await asyncio.to_thread(resume_builder, final_state)
                
                pdf_path = await asyncio.to_thread(
                    render_latex_to_pdf,
                    latex_source=latex_code,
                    output_pdf=output_path,
                )

            except Exception as exc:
                logger.error(f"Failed to generate PDF: {exc}")
                raise

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