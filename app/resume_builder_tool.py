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


# ── FontAwesome5 sanitisers ───────────────────────────────────────────────────
#
# FontAwesome5 has TWO calling conventions, both case-sensitive:
#
#   1. Direct commands  \faEnvelope  \faGithub  \faLinkedin   (PascalCase)
#   2. Generic command  \faIcon{envelope}  \faIcon{github}    (ALL lowercase)
#
# LLMs routinely mix these up:
#   \faLinkedIn   → \faLinkedin
#   \faIcon{Envelope} → \faIcon{envelope}
#
# We fix both styles unconditionally so that any LaTeX the LLM emits will
# compile without "Package fontawesome5 Error: The requested icon X was not found."

# Table of wrong → correct direct-command spellings.
_FA5_DIRECT_FIXES: list[tuple[str, str]] = [
    # LinkedIn
    (r'\faLinkedIn', r'\faLinkedin'),
    (r'\faLinkedinIn', r'\faLinkedin'),
    (r'\faLinkedInSquare', r'\faLinkedin'),
    # GitHub
    (r'\faGitHub', r'\faGithub'),
    (r'\faGithubAlt', r'\faGithub'),
    (r'\faGithubSquare', r'\faGithubSquare'),   # this one IS correct
    # Envelope / mail
    (r'\faEnvelop\b', r'\faEnvelope'),           # missing trailing e
    (r'\faMail', r'\faEnvelope'),
    # Phone
    (r'\faPhone-square', r'\faPhoneSquare'),
    # Twitter / X
    (r'\faTwitterX', r'\faTwitter'),
    # Facebook
    (r'\faFaceBook', r'\faFacebook'),
    # Map marker
    (r'\faMappin', r'\faMapMarker'),
]


def _fix_fontawesome5_icons(latex_code: str) -> str:
    """
    Two-pass FontAwesome5 correction:

    Pass 1 — fix wrong direct-command names (e.g. \\faLinkedIn → \\faLinkedin, \\faLinkinelinkedin → \\faLinkedin).
    Pass 2 — lowercase every icon name inside \\faIcon{...} because fontawesome5
              requires ALL-lowercase strings in that form.
              \\faIcon{Envelope}  →  \\faIcon{envelope}
              \\faIcon{GitHub}    →  \\faIcon{github}
    """
    # Pre-pass: Fix mangled / hallucinated fontawesome5 commands (e.g. \faLinkinelinkedin)
    latex_code = re.sub(r'\\faLinkin[A-Za-z]*', r'\\faLinkedin ', latex_code)
    latex_code = re.sub(r'\\faLinkedIn[A-Za-z]*', r'\\faLinkedin ', latex_code)
    latex_code = re.sub(r'\\faGit[A-Za-z]*', r'\\faGithub ', latex_code)
    latex_code = re.sub(r'\\faEnv[A-Za-z]*|\\faMail[A-Za-z]*', r'\\faEnvelope ', latex_code)
    latex_code = re.sub(r'\\faPhon[A-Za-z]*|\\faMobil[A-Za-z]*', r'\\faPhone ', latex_code)
    latex_code = re.sub(r'\\faMap[A-Za-z]*|\\faLoc[A-Za-z]*', r'\\faMapMarker ', latex_code)
    latex_code = re.sub(r'\\faGlob[A-Za-z]*|\\faWeb[A-Za-z]*', r'\\faGlobe ', latex_code)

    # Pass 1: string replacements for direct commands
    for wrong, correct in _FA5_DIRECT_FIXES:
        if '\\b' in wrong:
            # word-boundary replacement needs regex
            latex_code = re.sub(re.escape(wrong.replace('\\b', '')) + r'\b', correct, latex_code)
        else:
            latex_code = latex_code.replace(wrong, correct)

    # Pass 2: lowercase the argument of every \faIcon{...}
    latex_code = re.sub(
        r'\\faIcon\{([^}]+)\}',
        lambda m: r'\faIcon{' + m.group(1).lower() + '}',
        latex_code,
    )

    return latex_code


# ── enumitem option sanitiser ──────────────────────────────────────────────────
#
# The enumitem package does NOT support a 'columns' option (or 'twocol' /
# 'multicol').  LLMs invent these options because they look plausible, but they
# cause "Package enumitem Error: columns undefined" and abort compilation.
#
# Correct way to get multi-column lists: wrap in \begin{multicols}{N}...
# We simply strip the bad options so the list still renders (single-column).

# Keys that are NOT valid in enumitem \begin{...}[OPTIONS]
_INVALID_ENUMITEM_KEYS = frozenset({
    'columns', 'twocol', 'multicol', 'multicolumn',
})


def _fix_enumitem_compat(latex_code: str) -> str:
    """
    Strip unsupported keys from enumitem list-environment option lists.

    Handles \\begin{itemize}[...], \\begin{enumerate}[...],
    \\begin{description}[...] — removes any key=value pair (or bare key)
    whose key is in _INVALID_ENUMITEM_KEYS.
    """
    def clean_options(m: re.Match) -> str:
        env_open = m.group(1)   # e.g. r'\begin{itemize}'
        raw_opts = m.group(2)   # everything inside [...]

        # Split on commas, strip each token, remove invalid key=value pairs
        tokens = [t.strip() for t in raw_opts.split(',')]
        kept = []
        for tok in tokens:
            key = tok.split('=')[0].strip().lower()
            if key and key not in _INVALID_ENUMITEM_KEYS:
                kept.append(tok)

        if kept:
            return env_open + '[' + ', '.join(kept) + ']'
        else:
            return env_open   # drop the [] entirely when nothing is left

    return re.sub(
        r'(\\begin\{(?:itemize|enumerate|description)\})\[([^\]]*)\]',
        clean_options,
        latex_code,
    )

# ── titlesec compatibility fix ─────────────────────────────────────────────────
#
# titlesec < 2.14 is INCOMPATIBLE with TeX Live 2022/Debian (LaTeX 2022-11-01+).
# Symptom: "Missing { inserted" at every \section{...} call.
#
# Root cause: the 2022 kernel refactored \section internals; old titlesec
# patches commands that no longer exist in the same form, leaving LaTeX's
# brace-matching state corrupt exactly before the argument of \section.
#
# Fix: strip titlesec (and any \titleformat / \titlespacing calls it enables)
# and replace with a portable \renewcommand that works on ALL LaTeX versions.

_TITLESEC_SAFE_SECTION = r"""% Section formatting — titlesec-free, TeX Live 2022 compatible
\makeatletter
\renewcommand{\section}{\@startsection{section}{1}{\z@}
  {-1.5ex \@plus -0.5ex \@minus -0.2ex}
  {0.8ex \@plus 0.2ex}
  {\normalfont\large\bfseries}}
\makeatother"""


def _fix_titlesec_compat(latex_code: str) -> str:
    """
    Replace \\usepackage{titlesec} with a TeX Live 2022–safe section format.

    Also removes any \\titleformat / \\titlespacing / \\titlespacing* calls
    that only work with titlesec — leaving them in would produce
    "Undefined control sequence" errors after the package is removed.
    """
    if r'\usepackage{titlesec}' not in latex_code:
        return latex_code  # nothing to do

    # 1. Remove \titleformat{...}{...}{...}{...}{...}[...] (possibly multi-line)
    #    These commands use up to 6 arguments; strip the whole call.
    latex_code = re.sub(
        r'\\titleformat\s*\{[^}]*\}(?:\s*\{[^}]*\}){2,5}(?:\s*\[[^\]]*\])?\n?',
        '',
        latex_code,
    )
    # 2. Remove \titlespacing*?{...}{...}{...}{...}[...]
    latex_code = re.sub(
        r'\\titlespacing\*?\s*\{[^}]*\}(?:\s*\{[^}]*\}){2,3}(?:\s*\[[^\]]*\])?\n?',
        '',
        latex_code,
    )
    # 3. Replace the \usepackage{titlesec} line with the safe alternative
    latex_code = latex_code.replace(
        r'\usepackage{titlesec}',
        _TITLESEC_SAFE_SECTION,
    )

    return latex_code


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
5. Use modern but conservative formatting (geometry, enumitem, hyperref, fontawesome5, xcolor, parskip).
   DO NOT use titlesec — it is broken on TeX Live 2022. Use \@startsection for section headings.

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
    latex_code = _fix_titlesec_compat(latex_code)
    latex_code = _fix_fontawesome5_icons(latex_code)
    latex_code = _fix_enumitem_compat(latex_code)

    return latex_code