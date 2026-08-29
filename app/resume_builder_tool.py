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