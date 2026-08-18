import json
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

    try:
        pdf_path = render_latex_to_pdf(
            latex_source=latex_code,
            output_pdf=Path.home() / "Downloads" / "resume5.pdf",
        )
        print(f"PDF successfully created at: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")

    return result