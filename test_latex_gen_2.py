import asyncio
from pathlib import Path
from app.resume_builder_tool import resume_builder, validate_latex, fix_latex
from app.latex_executer import render_latex_to_pdf
import logging

logging.basicConfig(level=logging.INFO)

state = {
    "role": "Software Developer",
    "seniority": "Junior",
    "company": "AT&T",
    "resume_text": "C++ Python Node.js",
    "job_description": "We need a Python_Developer.",
    "matching_skills": [],
    "missing_skills": [],
    "nice_to_have_skills": [],
    "strengths": [],
    "weaknesses": [],
    "keyword_matches": [],
    "keyword_gaps": [],
    "full_name": "Test User",
}

async def run_test():
    latex_code = await asyncio.to_thread(resume_builder, state)
    
    # Introduce intentional error
    latex_code = latex_code + r"\someInvalidCommandThatFails{}"
    
    max_retries = 3
    output_path = Path("test_output2.pdf")
    
    for attempt in range(max_retries):
        try:
            validate_latex(latex_code)
            print(f"Validation passed on attempt {attempt+1}.")
            pdf_path = await asyncio.to_thread(
                render_latex_to_pdf,
                latex_source=latex_code,
                output_pdf=output_path,
            )
            print(f"Success! PDF created at: {pdf_path}")
            break
        except Exception as exc:
            if attempt == max_retries - 1:
                print(f"Failed after {max_retries} attempts: {exc}")
                raise
            print(f"Attempt {attempt+1} failed: {exc}")
            print("Fixing latex...")
            latex_code = await asyncio.to_thread(fix_latex, latex_code, str(exc))

if __name__ == "__main__":
    asyncio.run(run_test())
