import os
import re
from pathlib import Path
from typing import Any
import jinja2

import re

def escape_latex_string(text: str) -> str:
    r"""
    Escapes LaTeX special characters in a string, while preserving:
    1. Safe LaTeX commands like \textbf{...}, \textit{...}, etc.
    2. Already escaped characters like \&, \%, \_
    3. Bare URLs (wraps them in \url{})
    """
    if not text:
        return text

    scanner = re.Scanner([
        (r"https?://[^\s<>\"'{}|\\^`]+", lambda s, tok: ("BARE_URL", tok)),
        (r"\\[&%$#_{}]", lambda s, tok: ("ESCAPED_CHAR", tok)),
        (r"\\href\{[^}]*\}\{", lambda s, tok: ("CMD_START", tok)),
        (r"\\(?:textbf|textit|underline|emph|url)\{", lambda s, tok: ("CMD_START", tok)),
        (r"\}", lambda s, tok: ("BRACE_CLOSE", tok)),
        (r"\{", lambda s, tok: ("BRACE_OPEN", tok)),
        (r"\n+", lambda s, tok: ("NEWLINE", tok)),
        (r"\\", lambda s, tok: ("BACKSLASH", tok)),
        (r"[&%$#_~^]", lambda s, tok: ("SPECIAL", tok)),
        (r"[^\\{}&%$#_~^\n]+", lambda s, tok: ("TEXT", tok)),
        (r".", lambda s, tok: ("TEXT", tok)),
    ])
    
    tokens, remainder = scanner.scan(text)
    if remainder:
        tokens.append(("TEXT", remainder))
        
    result = []
    cmd_depth = 0
    in_url_cmd = False
    
    for token_type, tok in tokens:
        if token_type == "BARE_URL":
            if in_url_cmd:
                result.append(tok)
            else:
                result.append(f"\\url{{{tok}}}")
        elif token_type == "ESCAPED_CHAR":
            result.append(tok)
        elif token_type == "CMD_START":
            cmd_depth += 1
            if tok.startswith(r"\url{") or tok.startswith(r"\href{"):
                in_url_cmd = True
            result.append(tok)
        elif token_type == "BRACE_CLOSE":
            if cmd_depth > 0:
                cmd_depth -= 1
                if cmd_depth == 0:
                    in_url_cmd = False
                result.append(tok)
            else:
                result.append(r"\}")
        elif token_type == "BRACE_OPEN":
            result.append(r"\{")
        elif token_type == "NEWLINE":
            result.append(" ") 
        elif token_type == "BACKSLASH":
            result.append(r"\textbackslash{}")
        elif token_type == "SPECIAL":
            if tok == '~':
                result.append(r"\textasciitilde{}")
            elif tok == '^':
                result.append(r"\textasciicircum{}")
            else:
                result.append(f"\\{tok}")
        elif token_type == "TEXT":
            result.append(tok)
            
    return "".join(result)

def escape_latex(text: Any) -> Any:
    """Safely escape LaTeX special characters in user input."""
    if text is None:
        return ""
    if isinstance(text, str):
        return escape_latex_string(text)
    if isinstance(text, list):
        return [escape_latex(i) for i in text]
    if isinstance(text, dict):
        return {k: escape_latex(v) for k, v in text.items()}
    if hasattr(text, 'model_dump'):
        return escape_latex(text.model_dump())
    if hasattr(text, '__dict__'):
        return escape_latex(vars(text))
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
