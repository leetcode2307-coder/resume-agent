import asyncio
from pathlib import Path
from app.resume_builder_tool import resume_builder
from app.latex_executer import render_latex_to_pdf
from app.schemas.resume import StructuredResume, ResumeExperience, ResumeProject, ResumeEducation

async def run_integration_test():
    # 1. Create a realistic resume containing problematic characters
    structured_resume = StructuredResume(
        summary="Experienced Python_Developer with 100% accuracy in building solutions. Proficient in C# / C++.",
        experience=[
            ResumeExperience(
                company="Tech Corp",
                role="R&D Engineer",
                start_date="2020",
                end_date="2023",
                bullets=[
                    r"Built an RAG system using PostgreSQL & Redis.",
                    r"Managed a budget of ₹1,00,000 or $1000.",
                    r"Collaborated with M\u00fcnchen team.", # München
                    r"VLSI & Digital Design",
                ]
            )
        ],
        projects=[
            ResumeProject(
                name="my_project",
                technologies=["C#", "C++", "Python"],
                description="https://github.com/user/my_project?a=1&b=2",
                bullets=[
                    "Advanced {Python} & Machine^Learning",
                    "A ~ B"
                ]
            )
        ],
        education=[
            ResumeEducation(
                institution="University of \u00c9cole",
                degree="BSc Computer Science",
                details=["Graduated with 100%"]
            )
        ]
    )

    state = {
        "full_name": "Jos\u00e9 Fran\u00e7ois",
        "email": "jose_f@example.com",
        "phone": "+1-555-1234",
        "linkedin_url": "https://linkedin.com/in/jose&francois",
        "structured_resume": structured_resume
    }

    print("Generating LaTeX...")
    # 2. Generates the LaTeX.
    latex_code = await asyncio.to_thread(resume_builder, state)
    
    print("LaTeX successfully generated. Running XeLaTeX...")
    
    # 3. Runs XeLaTeX.
    output_path = Path("integration_test_output.pdf")
    
    try:
        pdf_path = await asyncio.to_thread(
            render_latex_to_pdf,
            latex_source=latex_code,
            output_pdf=output_path,
        )
    except Exception as exc:
        print(f"Compilation failed!\n{exc}")
        return False
        
    # 4. Confirms compilation succeeds.
    print(f"XeLaTeX compilation succeeded!")
    
    # 5. Confirms the PDF exists.
    if not pdf_path.exists():
        print("PDF does not exist!")
        return False
        
    # 6. Confirms the PDF is non-empty.
    if pdf_path.stat().st_size == 0:
        print("PDF is empty!")
        return False
        
    print(f"Integration test passed! PDF size: {pdf_path.stat().st_size} bytes")
    return True

if __name__ == "__main__":
    success = asyncio.run(run_integration_test())
    if not success:
        exit(1)
