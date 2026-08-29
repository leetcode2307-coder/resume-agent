import os
import re
from pathlib import Path
from typing import Any
import jinja2

# Characters that need escaping in LaTeX
_LATEX_SUBS = (
    (re.compile(r'\\'), r'\\textbackslash '),
    (re.compile(r'([{}])'), r'\\\1'),
    (re.compile(r'\\textbackslash '), r'\\textbackslash{}'),
    (re.compile(r'~'), r'\\textasciitilde{}'),
    (re.compile(r'\^'), r'\\textasciicircum{}'),
    (re.compile(r'([&%$#_])'), r'\\\1'),
)

def escape_latex(text: Any) -> Any:
    """Safely escape LaTeX special characters in user input."""
    if text is None:
        return ""
    if isinstance(text, str):
        # Apply all substitutions
        for pattern, replacement in _LATEX_SUBS:
            text = pattern.sub(replacement, text)
        return text
    if isinstance(text, list):
        return [escape_latex(i) for i in text]
    if isinstance(text, dict):
        return {k: escape_latex(v) for k, v in text.items()}
    return text

def get_jinja_env() -> jinja2.Environment:
    """Setup Jinja environment with LaTeX delimiters."""
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    
    env = jinja2.Environment(
        block_start_string=r'\BLOCK{',
        block_end_string='}',
        variable_start_string=r'\VAR{',
        variable_end_string='}',
        comment_start_string=r'\#{',
        comment_end_string='}#',
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(str(template_dir))
    )
    # Register filter for LaTeX escaping
    env.filters['escape_latex'] = escape_latex
    return env

def render_resume_latex(structured_resume: dict, contact_info: dict) -> str:
    """Render the structured resume data into the hardcoded LaTeX template."""
    env = get_jinja_env()
    template = env.get_template("resume_template.tex")
    
    # Escape data
    safe_resume = escape_latex(structured_resume)
    safe_contact = escape_latex(contact_info)
    
    # Build contact line
    contacts = []
    if safe_contact.get("email"):
        contacts.append(safe_contact["email"])
    if safe_contact.get("phone"):
        contacts.append(safe_contact["phone"])
    if safe_contact.get("linkedin_url"):
        contacts.append(safe_contact["linkedin_url"])
    if safe_contact.get("github_url"):
        contacts.append(safe_contact["github_url"])
    contact_line = " | ".join(contacts)
    
    # Combine data
    template_data = {
        "full_name": safe_contact.get("full_name") or "Candidate",
        "contact_line": contact_line,
        "summary": safe_resume.get("summary"),
        "experience": safe_resume.get("experience", []),
        "education": safe_resume.get("education", []),
        "projects": safe_resume.get("projects", []),
        "skills": safe_resume.get("skills", {}),
        "certifications": safe_resume.get("certifications", []),
        "achievements": safe_resume.get("achievements", []),
    }
    
    return template.render(**template_data)
