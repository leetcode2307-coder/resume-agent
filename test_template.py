import asyncio
from pathlib import Path
from app.resume_builder_tool import resume_builder
from app.latex_executer import render_latex_to_pdf
import logging

logging.basicConfig(level=logging.INFO)

state = {
    "role": "Software Developer",
    "seniority": "Junior",
    "company": "AT&T",
    "full_name": "Test User",
    "email": "user@example.com",
    "phone": "+91 99999 99999",
    "linkedin_url": "linkedin.com/in/test",
    "github_url": "github.com/test",
    "structured_resume": {
        "summary": "Junior Software Developer with C++ & Python skills.",
        "experience": [
            {
                "company": "AT&T",
                "role": "Python Developer",
                "location": "Remote",
                "start_date": "2020",
                "end_date": "Present",
                "bullets": [
                    "Increased performance by 50% using C++",
                    "Saved $100K in R&D",
                    "Used Node.js & React"
                ]
            }
        ],
        "education": [
            {
                "institution": "University of Tech",
                "degree": "B.S. Computer Science",
                "location": "City, ST",
                "start_date": "2016",
                "end_date": "2020",
                "details": ["GPA: 3.8/4.0"]
            }
        ],
        "projects": [
            {
                "name": "FastAPI_v2",
                "technologies": ["Python", "FastAPI"],
                "description": "A REST API project.",
                "bullets": ["Handled 10k req/sec"]
            }
        ],
        "skills": {
            "Languages": ["C++", "Python", "SQL"],
            "Frameworks": ["FastAPI", "Node.js"]
        },
        "certifications": ["AWS Certified Developer"],
        "achievements": []
    }
}

async def run_test():
    try:
        latex_code = resume_builder(state)
        print("=== GENERATED LATEX ===")
        print(latex_code[:500] + "...\n")
        
        output_path = Path("test_template_output.pdf")
        pdf_path = render_latex_to_pdf(
            latex_source=latex_code,
            output_pdf=output_path,
        )
        print(f"Success! PDF created at: {pdf_path}")
    except Exception as exc:
        print(f"Failed: {exc}")
        raise

if __name__ == "__main__":
    asyncio.run(run_test())
