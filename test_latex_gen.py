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
    "resume_text": """
Experienced in C++, C#, Python_Developer roles.
Worked in R&D, increased revenue by 50% ($100K).
Used Node.js.
""",
    "job_description": "We need a Python_Developer with 50% more skills in C++ & Node.js.",
    "matching_skills": ["C++", "C#", "Node.js", "Python_Developer"],
    "missing_skills": [],
    "nice_to_have_skills": [],
    "strengths": ["C++", "R&D"],
    "weaknesses": [],
    "keyword_matches": ["Node.js", "C#"],
    "keyword_gaps": [],
    "full_name": "Test User",
    "email": "user@example.com",
    "phone": "555-1234",
    "linkedin_url": "linkedin.com/in/test_user",
    "github_url": "github.com/example_user"
}

async def run_test():
    latex_code = await asyncio.to_thread(resume_builder, state)
    print("=== INITIAL LATEX ===")
    print(latex_code[:300] + "...\n")
    
    max_retries = 3
    output_path = Path("test_output.pdf")
    
    for attempt in range(max_retries):
        try:
            validate_latex(latex_code)
            print("Validation passed.")
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
            print("=== FIXED LATEX ===")
            print(latex_code[:300] + "...\n")

if __name__ == "__main__":
    asyncio.run(run_test())
