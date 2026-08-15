# main.py - Place this in your project root directory
import asyncio
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
import uvicorn

# Import your workflow functions
try:
    from app.graph.workflow import workflow_result_async, workflow_result
except ImportError:
    # Fallback import structure if workflow is in a different location
    try:
        from workflow import workflow_result_async, workflow_result
    except ImportError:
        # Mock workflow functions for testing if imports fail
        print("Warning: Could not import workflow functions. Using mock functions.")
        
        async def workflow_result_async(resume_text: str, job_description: str):
            return {
                "initial_match_score": 75,
                "final_match_score": 85,
                "rewritten_resume": f"Rewritten: {resume_text[:100]}...",
                "critic_score": 80,
                "critic_feedback": "Good improvement needed in skills section",
                "interview_questions": "Tell me about your experience with Python?",
                "rewrite_iteration": 2
            }
        
        def workflow_result(resume_text: str, job_description: str):
            return asyncio.run(workflow_result_async(resume_text, job_description))

# Initialize FastAPI app
app = FastAPI(
    title="Resume Optimization API",
    description="API for optimizing resumes based on job descriptions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request/Response Models with proper Pydantic V2 syntax
class ResumeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resume_text": "Experienced software engineer with 5 years of experience...",
                "job_description": "Looking for a senior software engineer with Python expertise...",
                "max_rewrite_iterations": 3,
                "quality_threshold": 80
            }
        }
    )
    
    resume_text: str
    job_description: str
    max_rewrite_iterations: Optional[int] = 3
    quality_threshold: Optional[int] = 80

class WorkflowResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Workflow completed successfully",
                "data": {
                    "initial_match_score": 65,
                    "rewritten_resume": "Updated resume content...",
                    "critic_score": 85,
                    "interview_questions": ["Question 1", "Question 2"]
                }
            }
        }
    )
    
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Health Check Endpoints
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "message": "Resume Optimization API is running",
        "version": "1.0.0",
        "endpoints": [
            "/docs - API Documentation",
            "/health - Health Check",
            "/optimize-resume - Resume Optimization",
            "/workflow-info - Workflow Information"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "resume-optimizer", "version": "1.0.0"}

# Main Workflow Endpoint
@app.post("/optimize-resume", response_model=WorkflowResponse)
async def optimize_resume(request: ResumeRequest):
    """
    Optimize a resume based on a job description.
    
    The workflow includes:
    1. Analysis of initial match score
    2. Rewriting if needed
    3. Critical review of rewritten content
    4. Interview preparation
    """
    try:
        # Validate input
        if not request.resume_text or not request.job_description:
            raise HTTPException(
                status_code=400,
                detail="Both resume_text and job_description are required"
            )
        
        if len(request.resume_text) < 50:
            raise HTTPException(
                status_code=400,
                detail="Resume text is too short. Please provide a complete resume (minimum 50 characters)."
            )
        
        if len(request.job_description) < 20:
            raise HTTPException(
                status_code=400,
                detail="Job description is too short. Please provide a detailed job description (minimum 20 characters)."
            )

        # Execute the workflow
        print(f"Processing resume for job description...")
        result = await workflow_result_async(
            request.resume_text, 
            request.job_description
        )
        
        # Check if result contains expected data
        if not result:
            raise HTTPException(
                status_code=500,
                detail="Workflow returned no result"
            )

        # Extract relevant data from the result
        response_data = {
            "initial_match_score": result.get('initial_match_score'),
            "final_match_score": result.get('final_match_score'),
            "rewritten_resume": result.get('rewritten_resume'),
            "critic_score": result.get('critic_score'),
            "critic_feedback": result.get('critic_feedback'),
            "interview_questions": result.get('interview_questions'),
            "rewrite_iteration": result.get('rewrite_iteration', 0)
        }

        # Determine if optimization was successful
        critic_score = result.get('critic_score', 0)
        is_successful = critic_score >= 70 if critic_score is not None else False
        
        return WorkflowResponse(
            status="success" if is_successful else "partial",
            message="Resume optimized successfully" if is_successful 
                    else "Resume processed but quality threshold not fully met",
            data=response_data
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in optimize_resume: {str(e)}")
        return WorkflowResponse(
            status="error",
            message="Failed to process resume",
            error=str(e)
        )

# Batch Processing Endpoint
@app.post("/batch-optimize")
async def batch_optimize(requests: list[ResumeRequest]):
    """
    Process multiple resumes in batch
    """
    results = []
    for idx, request in enumerate(requests):
        try:
            result = await workflow_result_async(
                request.resume_text,
                request.job_description
            )
            results.append({
                "index": idx,
                "success": True,
                "data": result
            })
        except Exception as e:
            results.append({
                "index": idx,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total_processed": len(requests),
        "successful": sum(1 for r in results if r["success"]),
        "failed": sum(1 for r in results if not r["success"]),
        "results": results
    }


# Form-based endpoint for multiline resume/job descriptions (works well with Swagger UI 'Try it out')
@app.post("/optimize-resume-form", response_model=WorkflowResponse)
async def optimize_resume_form(
    resume_text: str = Form(...),
    job_description: str = Form(...),
    max_rewrite_iterations: Optional[int] = Form(3),
    quality_threshold: Optional[int] = Form(80),
):
    # Build a ResumeRequest-like object and delegate to the same workflow
    # Lightweight validation similar to the JSON endpoint
    if not resume_text or not job_description:
        raise HTTPException(status_code=400, detail="Both resume_text and job_description are required")

    if len(resume_text) < 50:
        raise HTTPException(status_code=400, detail="Resume text is too short. Please provide a complete resume (minimum 50 characters).")

    if len(job_description) < 20:
        raise HTTPException(status_code=400, detail="Job description is too short. Please provide a detailed job description (minimum 20 characters).")

    try:
        result = await workflow_result_async(resume_text, job_description)
        if not result:
            raise HTTPException(status_code=500, detail="Workflow returned no result")

        response_data = {
            "initial_match_score": result.get('initial_match_score'),
            "final_match_score": result.get('final_match_score'),
            "rewritten_resume": result.get('rewritten_resume'),
            "critic_score": result.get('critic_score'),
            "critic_feedback": result.get('critic_feedback'),
            "interview_questions": result.get('interview_questions'),
            "rewrite_iteration": result.get('rewrite_iteration', 0)
        }

        critic_score = result.get('critic_score', 0)
        is_successful = critic_score >= 70 if critic_score is not None else False

        return WorkflowResponse(
            status="success" if is_successful else "partial",
            message="Resume optimized successfully" if is_successful else "Resume processed but quality threshold not fully met",
            data=response_data
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in optimize_resume_form: {str(e)}")
        return WorkflowResponse(status="error", message="Failed to process resume", error=str(e))

# Workflow Information Endpoint
@app.get("/workflow-info")
async def get_workflow_info():
    """
    Get information about the workflow agents and process
    """
    return {
        "agents": [
            {"name": "analyzer_node", "description": "Analyzes initial resume-job match score"},
            {"name": "rewriter_node", "description": "Rewrites resume based on critic feedback"},
            {"name": "critic_agent", "description": "Reviews rewritten resume quality and provides feedback"},
            {"name": "interview_agent", "description": "Generates interview questions based on resume"}
        ],
        "decision_points": [
            {"node": "analyzer_node", "decision": "Rewrite or proceed to interview based on match score"},
            {"node": "critic_agent", "decision": "Continue rewriting or proceed based on quality threshold"}
        ],
        "workflow_flow": [
            "START → input_node",
            "input_node → analyzer_node",
            "analyzer_node → rewriter_node (if match < 70) OR → interview_agent (if match ≥ 70)",
            "rewriter_node → critic_agent",
            "critic_agent → rewriter_node (if quality < threshold) OR → interview_agent (if quality ≥ threshold)",
            "interview_agent → END"
        ]
    }

# Error Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    payload = WorkflowResponse(
        status="error",
        message=str(exc.detail),
        error=str(exc.detail)
    ).model_dump()
    return JSONResponse(status_code=exc.status_code, content=payload)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"Unhandled exception: {str(exc)}")
    payload = WorkflowResponse(
        status="error",
        message="An unexpected error occurred",
        error=str(exc)
    ).model_dump()
    return JSONResponse(status_code=500, content=payload)


# Handle validation errors (including invalid JSON sent to the model)
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Return a clearer JSON response when the request body is invalid JSON
    print(f"Request validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "message": "Invalid request body. Ensure valid JSON or use the form endpoint for raw text.",
            "error": str(exc)
        },
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    print("=" * 50)
    print("Resume Optimization API Starting...")
    print("=" * 50)
    print(f"API Documentation: http://localhost:8000/docs")
    print(f"Health Check: http://localhost:8000/health")
    print("=" * 50)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("Resume Optimization API shutting down...")

# Main entry point
if __name__ == "__main__":
    # When running from project root with `python -m app.api.routes`
    # point uvicorn at the importable module path `app.api.routes:app`.
    uvicorn.run(
        "app.api.routes:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )