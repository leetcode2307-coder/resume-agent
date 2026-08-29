import logging
from app.services.latex_utils import render_resume_latex

logger = logging.getLogger(__name__)

def resume_builder(state: dict) -> str:
    """
    Renders the structured resume into a hardcoded LaTeX template.
    """
    structured_resume = state.get('structured_resume')
    
    if not structured_resume:
        # Fallback if somehow missing
        logger.warning("structured_resume missing from state. Attempting to build empty resume.")
        structured_resume = {}
        
    if isinstance(structured_resume, dict):
        pass # Expected
    elif hasattr(structured_resume, 'model_dump'):
        structured_resume = structured_resume.model_dump()
    elif hasattr(structured_resume, '__dict__'):
        structured_resume = vars(structured_resume)
    else:
        raise ValueError(f"Invalid structured_resume format: {type(structured_resume)}")

    contact_info = {
        "full_name": state.get('full_name', 'Candidate Name'),
        "email": state.get('email'),
        "phone": state.get('phone'),
        "linkedin_url": state.get('linkedin_url'),
        "github_url": state.get('github_url'),
    }
    
    if not contact_info["full_name"]:
        raise ValueError("full_name is missing from state")

    return render_resume_latex(structured_resume, contact_info)


def validate_latex(latex_code: str) -> None:
    """
    Perform lightweight structural validation of the LaTeX code before compilation.
    Raises ValueError if structural issues are detected.
    """
    # Remove escaped braces and backslashes to check for balance
    import re
    clean_code = re.sub(r'\\.', '', latex_code)
    if clean_code.count('{') != clean_code.count('}'):
        raise ValueError("Mismatched braces detected in LaTeX source.")
        
    # Check for unmatched environments
    if latex_code.count(r'\begin{itemize}') != latex_code.count(r'\end{itemize}'):
        raise ValueError("Mismatched itemize environments detected.")


def fix_latex(latex_code: str, error_message: str) -> str:
    """
    Attempt safe, deterministic repairs based on compiler errors.
    """
    import re
    fixed_code = latex_code
    
    if "Misplaced alignment tab character" in error_message or "unescaped special characters" in error_message:
        # A fallback if escaping somehow failed: find bare ampersands not following a backslash
        # Note: In a real scenario, escape_latex should have handled this, but this is a defense-in-depth repair.
        # Use negative lookbehind for \
        fixed_code = re.sub(r'(?<!\\)&', r'\&', fixed_code)
        
    if "Missing $ inserted" in error_message or "Missing { inserted" in error_message:
        # Escaping bare underscores
        fixed_code = re.sub(r'(?<!\\)_', r'\_', fixed_code)
        
    return fixed_code