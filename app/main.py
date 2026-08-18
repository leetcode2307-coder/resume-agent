import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from app.latex_executer import render_latex_to_pdf
from app.resume_builder_tool import resume_builder
from app.graph.workflow import workflow_result_async


app = FastAPI()


class WorkflowRequest(BaseModel):
    resume_text: str
    job_description: str

    # Optional contact info supplied by the user. These are passed straight
    # through to the LaTeX resume — never inferred or fabricated by the LLM.
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None


def _slugify(value: str, max_length: int = 40) -> str:
    """
    Turn arbitrary text into a filesystem-safe slug:
    lowercase, spaces -> underscores, only [a-z0-9_-] kept, trimmed length.
    """
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\s_-]", "", value)
    value = re.sub(r"[\s_-]+", "_", value).strip("_")
    return value[:max_length] or "candidate"


def _build_output_filename(full_name: str | None, role: str | None) -> str:
    """
    Build a unique, readable filename for the generated resume, e.g.:
    maruthi_kumar_senior_flutter_developer_20260818_143205_a1b2c3.pdf

    Uses name + role for readability, plus a UTC timestamp + short UUID
    suffix so concurrent/repeated requests never collide or overwrite
    each other, even for the same candidate/role.
    """
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


@app.post("/workflow-result")
async def workflow_result(request: WorkflowRequest):
    result = await workflow_result_async(
        resume_text=request.resume_text,
        job_description=request.job_description,
    )

    # result may already be a dict, or (in other code paths) a JSON string.
    if isinstance(result, (str, bytes)):
        parsed = json.loads(result)
    else:
        parsed = result

    state = parsed["result"] if "result" in parsed else parsed

    # Merge user-supplied contact fields into state. These never come from
    # the LLM pipeline, so they're added here explicitly rather than trusting
    # the analyzer/rewriter/critic agents to know or invent them.
    state["full_name"] = request.full_name
    state["email"] = request.email
    state["phone"] = request.phone
    state["linkedin_url"] = request.linkedin_url
    state["github_url"] = request.github_url

    latex_code = resume_builder(state=state)

    print(latex_code)

    output_filename = _build_output_filename(
        full_name=request.full_name,
        role=state.get("role"),
    )
    output_path = Path.home() / "Downloads" / output_filename

    pdf_generated = False
    try:
        pdf_path = render_latex_to_pdf(
            latex_source=latex_code,
            output_pdf=output_path,
        )
        pdf_generated = True
        print(f"PDF successfully created at: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")

    # Let the caller know what file was actually produced, since the name
    # is now unique per request instead of a fixed "resume5.pdf".
    if isinstance(result, dict):
        result["pdf_filename"] = output_filename if pdf_generated else None
        result["pdf_path"] = str(output_path) if pdf_generated else None

    return result