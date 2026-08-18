import json
import re
# from langchain_core.tools import tool
from app.llm import llm
from app.prompts import LATEX_TOOL_SYSTEM_PROMPT


def _sanitize_latex(latex_code: str) -> str:
    """
    Guard against a classic LaTeX gotcha: a line break command (\\) 
    immediately followed by an opening square bracket (e.g. from a 
    placeholder like [Location]) gets misparsed as an optional spacing 
    argument, e.g. \\[Location] -> LaTeX tries to read "Location" as a 
    length and fails with "Missing number, treated as zero."

    This inserts an empty group {} right after any \\ that's followed 
    by whitespace/newline and then a '[' — but ONLY when the bracket 
    starts with a letter (i.e. it's a word/placeholder like [Location] 
    or [Company Name]), not a number. This deliberately excludes real 
    LaTeX spacing arguments like \\[4pt] or \\[0.5em], which must be 
    left untouched or they'll be printed as literal text instead of 
    being applied as spacing.
    """
    return re.sub(r'(\\\\)(\s*)\[(?=[A-Za-z])', r'\1{}\2[', latex_code)


def resume_builder(state: dict) -> str:
    """
    Tool is used to convert the output JSON into professional resume LaTeX code.

    Args:
        state: Dictionary containing ResumeAgentState with all analysis data

    Returns:
        str: Complete LaTeX code for a professional resume
    """

    # Extract the relevant data from state
    resume_text = state.get('resume_text', '')
    job_description = state.get('job_description', '')
    rewritten_resume = state.get('rewritten_resume', '')
    rewritten_bullet_points = state.get('rewritten_bullet_points', [])

    if not resume_text.strip():
        raise ValueError(
            "resume_text is empty. Check that you're passing the correct nested "
            "dictionary into resume_builder() (e.g. data['result'], not the raw "
            "top-level JSON)."
        )

    # Extract analyzer data
    role = state.get('role', 'Software Developer')
    seniority = state.get('seniority', '')
    company = state.get('company', '')
    tech_stack = state.get('tech_stack', [])
    matching_skills = state.get('matching_skills', [])
    missing_skills = state.get('missing_skills', [])
    nice_to_have_skills = state.get('nice_to_have_skills', [])
    strengths = state.get('strengths', [])
    weaknesses = state.get('weaknesses', [])
    keyword_matches = state.get('keyword_matches', [])
    keyword_gaps = state.get('keyword_gaps', [])

    # Extract scores & critic data
    ats_score = state.get('ats_score', 0)
    initial_match_score = state.get('initial_match_score', 0)
    critic_score = state.get('critic_score', 0)
    critic_feedback = state.get('critic_feedback', [])
    detected_errors = state.get('detected_errors', [])
    weak_phrasing = state.get('weak_phrasing', [])

    # --- Contact info: use real values if supplied, otherwise instruct the
    # LLM to fall back to a clean generic placeholder. Never let the LLM
    # guess/fabricate a specific-looking name, email, phone, or URL. ---
    full_name = state.get('full_name') or None
    email = state.get('email') or None
    phone = state.get('phone') or None
    linkedin_url = state.get('linkedin_url') or None
    github_url = state.get('github_url') or None

    def _contact_line(label: str, value, placeholder: str) -> str:
        if value:
            return f"{label}: {value} (use this EXACT value, verbatim)"
        return f"{label}: NOT PROVIDED -> use placeholder \"{placeholder}\", do NOT invent a value"

    contact_block = "\n".join([
        _contact_line("Full Name", full_name, "[Full Name]"),
        _contact_line("Email", email, "[Email Address]"),
        _contact_line("Phone", phone, "[Phone Number]"),
        _contact_line("LinkedIn URL", linkedin_url, "[LinkedIn URL]"),
        _contact_line("GitHub URL", github_url, "[GitHub URL]"),
    ])

    # Build the prompt with all available data
    prompt = f"""
You are an expert LaTeX resume generator and career-document specialist.

CRITICAL RULES (non-negotiable):
1. Base every factual claim (years of experience, tools used, education, seniority) strictly on what is written in "Original resume text" below. Do not import facts from any other candidate profile or example.
2. Highlight only the genuine matching skills, drawn from this exact list (do not add to it): {matching_skills}
3. Do NOT claim any of the following missing or nice-to-have skills as the candidate's own experience: {missing_skills + nice_to_have_skills}
4. Produce a clean, ATS-friendly, one-page professional LaTeX resume.
5. Use modern but conservative formatting (geometry, titlesec, enumitem, hyperref, fontawesome5, etc.).
6. Output ONLY the complete, compilable LaTeX source code — no explanations, no markdown fences, no commentary.

CONTACT INFORMATION (strict):
{contact_block}
- For any field marked NOT PROVIDED, you MUST use the exact bracketed placeholder given above.
- NEVER invent, guess, or construct a realistic-looking name, email address, phone number, or URL (e.g. never write something like "maruthi@example.com" or "github.com/maruthi") for a field marked NOT PROVIDED.
- Never derive a GitHub/LinkedIn handle from the candidate's name — only use a URL if it was given to you verbatim above.

STRUCTURED DATA
---------------
Role target: {role} ({seniority})
Company: {company or "Not specified"}

Original resume text:
\"\"\"{resume_text}\"\"\"

Job description:
\"\"\"{job_description}\"\"\"

Matching skills: {matching_skills}
Missing skills (do NOT claim these): {missing_skills}
Nice-to-have skills (do NOT claim these): {nice_to_have_skills}
Strengths to emphasize: {strengths}
Weaknesses to avoid inventing around: {weaknesses}
Keyword matches: {keyword_matches}
Keyword gaps (do NOT invent): {keyword_gaps}

ATS / Match context (for your awareness only — do not reference scores in the resume):
- ats_score: {ats_score}
- initial_match_score: {initial_match_score}
- critic_score: {critic_score}
- critic_feedback: {critic_feedback}
- detected_errors: {detected_errors}

TASK
----
Using ONLY the structured data provided above, generate a complete, professional, ATS-friendly one-page LaTeX resume.

Requirements:
- Base every claim strictly on the original resume_text and the listed strengths / matching_skills / keyword_matches.
- Never invent experience, metrics, tools, achievements, or contact details that are not explicitly provided above.
- Target the role and seniority indicated in the data ({role} / {seniority}).
- Emphasize the candidate's genuine strengths and matching skills while remaining honest about limited experience.
- Output ONLY the complete, compilable LaTeX source code — no explanations, no markdown fences, no commentary.
"""

    # Call the LLM
    messages = [
        {"role": "system", "content": LATEX_TOOL_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]

    response = llm.invoke(messages)

    # Return clean LaTeX (strip any accidental markdown fences)
    latex_code = response.content.strip()
    if latex_code.startswith("```"):
        lines = latex_code.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        latex_code = "\n".join(lines).strip()

    latex_code = _sanitize_latex(latex_code)

    return latex_code