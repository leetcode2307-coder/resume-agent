import json
# from langchain_core.tools import tool
from app.llm import llm
from app.prompts import LATEX_TOOL_SYSTEM_PROMPT
import re

def _sanitize_latex(latex_code: str) -> str:
    """
    Guard against a classic LaTeX gotcha: a line break command (\\) 
    immediately followed by an opening square bracket (e.g. from a 
    placeholder like [Location]) gets misparsed as an optional spacing 
    argument, e.g. \\[Location] -> LaTeX tries to read "Location" as a 
    length and fails with "Missing number, treated as zero."

    This inserts an empty group {} right after any \\ that's followed 
    by whitespace/newline and then a '[', which blocks LaTeX from 
    treating the bracket as an argument.
    """
    return re.sub(r'(\\\\)(\s*)\[', r'\1{}\2[', latex_code)

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

    # --- Safety check: fail loudly instead of silently generating a hallucinated resume ---
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

    # Build the prompt with all available data
    # NOTE: Rules 2 and 3 below used to hardcode a specific Python/FastAPI/LangGraph
    # candidate profile. That meant EVERY resume, regardless of input state, was
    # constrained to describe that one fictional candidate. They are now fully
    # dynamic and derived only from the state passed in.
    prompt = f"""
You are an expert LaTeX resume generator and career-document specialist.

CRITICAL RULES (non-negotiable):
1. NEVER invent or exaggerate experience, metrics, tools, or achievements that are not explicitly present in the original resume_text below.
2. Base every factual claim (years of experience, tools used, education, seniority) strictly on what is written in "Original resume text". Do not import facts from any other candidate profile or example.
3. Highlight only the genuine matching skills, drawn from this exact list (do not add to it): {matching_skills}
4. Do NOT claim any of the following missing or nice-to-have skills as the candidate's own experience: {missing_skills + nice_to_have_skills}
5. Produce a clean, ATS-friendly, one-page professional LaTeX resume.
6. Use modern but conservative formatting (geometry, titlesec, enumitem, hyperref, fontawesome5, etc.).
7. Output ONLY the complete, compilable LaTeX source code — no explanations, no markdown fences, no commentary.
8. Never place a line break command (\\\\) immediately before a square bracket 
   (e.g. avoid "\\\\ \\n[Location]"). If a line break is followed by bracketed 
   text, either put it on the same line with a space, or write "\\\\{{}}" instead 
   of a bare "\\\\" to prevent LaTeX from misreading the bracket as a spacing argument.
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
- Never invent experience, metrics, tools, or achievements that appear in missing_skills, keyword_gaps, weaknesses, or critic_feedback.
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
        
    latex_code = _sanitize_latex(latex_code)  # <-- add this

    return latex_code


# # ---------------------------------------------------------------------------
# # Parse the raw JSON string into a dictionary
# # ---------------------------------------------------------------------------
# raw_json_string = r"""
# {
#   "result": {
#     "resume_text": "..."
#   }
# }
# """

# # Parse the JSON, then UNWRAP the "result" key before passing it in.
# # This was the other bug: state_dict used to be {"result": {...}}, and
# # resume_builder() was called on that outer dict, so state.get('resume_text')
# # always returned '' because the real data was one level deeper.
# parsed = json.loads(raw_json_string)
# state_dict = parsed["result"]  # <-- unwrap here

# result = resume_builder(state_dict)

# print(result)