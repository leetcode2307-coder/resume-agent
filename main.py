"""
Resume Agent — Streamlit UI
============================
A single-file, production-ready Streamlit front end for the FastAPI
`/workflow-result` backend (resume_text + job_description -> tailored
resume PDF + analysis + interview prep).

Run:
    streamlit run streamlit_app.py

Configure the backend URL via the sidebar, an environment variable
(RESUME_AGENT_API_URL), or Streamlit secrets (api_url).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
import streamlit as st

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

DEFAULT_API_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = 900  # LLM workflow + LaTeX render can be slow

st.set_page_config(
    page_title="Resume Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# Minimal, clean styling
# --------------------------------------------------------------------------

st.markdown(
    """
    <style>
        .block-container { padding-top: 2.5rem; max-width: 1100px; }
        h1 { font-weight: 700; letter-spacing: -0.02em; }
        h3 { margin-top: 1.5rem; }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            padding: 0.6rem 1.2rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(127,127,127,0.06);
            border-radius: 10px;
            padding: 0.75rem 1rem;
        }
        .stAlert { border-radius: 8px; }
        .prep-item {
            background: rgba(127,127,127,0.06);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.6rem;
        }
        .prep-item b { display: block; margin-bottom: 0.25rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Helpers — API
# --------------------------------------------------------------------------

def get_api_url() -> str:
    """Resolve backend URL: sidebar override > secrets > env var > default."""
    if "api_url" in st.session_state and st.session_state.api_url:
        return st.session_state.api_url.rstrip("/")
    try:
        secret_url = st.secrets.get("api_url")  # type: ignore[attr-defined]
        if secret_url:
            return str(secret_url).rstrip("/")
    except Exception:
        pass
    return os.environ.get("RESUME_AGENT_API_URL", DEFAULT_API_URL).rstrip("/")


def call_workflow(api_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST to /workflow-result and raise a readable error on failure."""
    response = requests.post(
        f"{api_url}/workflow-result",
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def check_health(api_url: str) -> bool:
    try:
        r = requests.get(f"{api_url}/health", timeout=5)
        return r.ok
    except requests.RequestException:
        return False


def read_local_pdf(pdf_path: Optional[str]) -> Optional[bytes]:
    """
    Best-effort read of the generated PDF from disk. This only works when
    the Streamlit app runs on the same machine/filesystem as the FastAPI
    server (e.g. local dev, or a shared volume in the same container).
    """
    if not pdf_path:
        return None
    path = Path(pdf_path)
    if path.exists():
        return path.read_bytes()
    return None


# --------------------------------------------------------------------------
# Helpers — rendering
# --------------------------------------------------------------------------

# Common field-name aliases used to pull a "title" and a "body" out of a
# loosely-structured dict item (question objects, topic objects, etc.).
_TITLE_KEYS = ("question", "topic", "title", "tip", "name", "skill")
_BODY_KEYS = ("answer", "why", "description", "detail", "details", "reason", "explanation", "note")


def _split_title_body(item: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    title = next((str(item[k]) for k in _TITLE_KEYS if item.get(k)), None)
    body = next((str(item[k]) for k in _BODY_KEYS if item.get(k)), None)
    if title is None:
        # Fall back to the first value in the dict as the title.
        remaining = {k: v for k, v in item.items() if v not in (None, "")}
        if remaining:
            first_key, first_val = next(iter(remaining.items()))
            title = str(first_val)
    return title, body


def render_items(items: List[Any]) -> None:
    """Render a list that may contain plain strings or small dicts."""
    if not items:
        st.caption("Nothing to show here.")
        return
    for item in items:
        if isinstance(item, dict):
            title, body = _split_title_body(item)
            html = f'<div class="prep-item">'
            if title:
                html += f"<b>{title}</b>"
            if body:
                html += body
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.markdown(f"- {item}")


def render_cover_letter(state: Dict[str, Any]) -> Set[str]:
    """Render the generated cover letter, if present."""
    if not state.get("cover_letter"):
        return set()

    st.markdown("### ✉️ Cover Letter")
    st.text_area(
        "Generated cover letter",
        value=str(state["cover_letter"]),
        height=500,
        disabled=True,
    )

    return {"cover_letter"}


def render_interview_prep(state: Dict[str, Any]) -> Set[str]:
    """
    Render the interview-prep fields (interview_questions, technical_questions,
    gap_questions, preparation_tips, key_topics_to_review, expected_questions)
    as tabs, if any are present. Returns the set of keys consumed so the
    generic fallback section doesn't repeat them.
    """
    fields = {
        "interview_questions": "🎤 Interview Qs",
        "technical_questions": "🛠️ Technical Qs",
        "gap_questions": "🕳️ Gap Qs",
        "preparation_tips": "✅ Prep Tips",
        "key_topics_to_review": "📚 Key Topics",
        "expected_questions": "❓ Expected Qs",
    }
    present = {k: v for k, v in fields.items() if state.get(k)}
    if not present:
        return set()

    st.markdown("### 🧠 Interview Preparation")
    tabs = st.tabs(list(present.values()))
    for tab, key in zip(tabs, present.keys()):
        with tab:
            render_items(state[key])

    return set(present.keys())


# Known analyzer field groups, in the order they should render. Any of
# these that the backend didn't send are simply skipped.
_ANALYZER_META_FIELDS = [("role", "Role"), ("seniority", "Seniority"), ("company", "Company")]
_ANALYZER_SCORE_FIELDS = [
    ("ats_score", "ATS Score"),
    ("initial_match_score", "Initial Match"),
    ("critic_score", "Critic Score"),
]
_ANALYZER_BADGE_FIELDS = [
    ("tech_stack", "🧰 Tech Stack"),
    ("matching_skills", "✅ Matching Skills"),
    ("missing_skills", "❗ Missing Skills"),
    ("nice_to_have_skills", "✨ Nice to Have"),
    ("keyword_matches", "🔑 Keyword Matches"),
    ("keyword_gaps", "🔍 Keyword Gaps"),
]
_ANALYZER_NARRATIVE_FIELDS = [("strengths", "💪 Strengths", "✅"), ("weaknesses", "⚠️ Weaknesses", "⚠️")]
_ANALYZER_ALL_KEYS = (
    {k for k, _ in _ANALYZER_META_FIELDS}
    | {k for k, _ in _ANALYZER_SCORE_FIELDS}
    | {k for k, _ in _ANALYZER_BADGE_FIELDS}
    | {k for k, _, _ in _ANALYZER_NARRATIVE_FIELDS}
)


def _badge_row(items: list[Any]) -> None:
    """Render a wrapping row of small pill-style badges."""
    if not items:
        st.caption("None listed.")
        return
    st.markdown(
        " ".join(
            f'<span style="display:inline-block;background:rgba(127,127,127,0.12);'
            f'border-radius:999px;padding:0.25rem 0.7rem;margin:0.15rem 0.15rem 0.15rem 0;'
            f'font-size:0.85rem;">{item}</span>'
            for item in items
        ),
        unsafe_allow_html=True,
    )


def render_analyzer_output(state: Dict[str, Any]) -> Set[str]:
    """
    Render the resume/job-description analysis: role/seniority/company,
    match scores, skill/keyword badges, and strengths/weaknesses. Returns
    the set of top-level keys consumed so the raw-JSON fallback doesn't
    repeat them.
    """
    if not any(k in state for k in _ANALYZER_ALL_KEYS):
        return set()

    st.markdown("### 🔍 Resume Analysis")

    meta_present = [(k, l) for k, l in _ANALYZER_META_FIELDS if state.get(k) not in (None, "")]
    if meta_present:
        cols = st.columns(len(meta_present))
        for col, (key, label) in zip(cols, meta_present):
            col.markdown(f"**{label}**  \n{state[key]}")

    score_present = [(k, l) for k, l in _ANALYZER_SCORE_FIELDS if state.get(k) not in (None, "")]
    if score_present:
        cols = st.columns(len(score_present))
        for col, (key, label) in zip(cols, score_present):
            col.metric(label, state[key])

    badge_present = [(k, l) for k, l in _ANALYZER_BADGE_FIELDS if state.get(k)]
    if badge_present:
        tabs = st.tabs([label for _, label in badge_present])
        for tab, (key, _) in zip(tabs, badge_present):
            with tab:
                _badge_row([str(v) for v in state[key]])

    narrative_present = [(k, l, i) for k, l, i in _ANALYZER_NARRATIVE_FIELDS if state.get(k)]
    if narrative_present:
        cols = st.columns(len(narrative_present))
        for col, (key, label, icon) in zip(cols, narrative_present):
            with col:
                st.markdown(f"**{label}**")
                for v in state[key]:
                    st.markdown(f"{icon} {v}")

    return {k for k in _ANALYZER_ALL_KEYS if k in state}


def render_remaining(state: Dict[str, Any], already_consumed: Set[str]) -> None:
    """Dump anything left over so nothing the backend returns is hidden."""
    excluded = {
        "full_name", "email", "phone", "linkedin_url", "github_url",
        "pdf_filename", "pdf_path", "resume_text", "job_description",
        *already_consumed,
    }
    remaining = {
        k: v for k, v in state.items()
        if k not in excluded and v not in (None, "", [])
    }
    if remaining:
        with st.expander("Full response (raw)", expanded=False):
            st.json(remaining)


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

with st.sidebar:
    st.subheader("⚙️ Settings")
    st.session_state.api_url = st.text_input(
        "Backend API URL",
        value=st.session_state.get("api_url", get_api_url()),
        help="Base URL of the FastAPI service (no trailing slash).",
    )
    api_url = get_api_url()

    healthy = check_health(api_url)
    if healthy:
        st.success("Backend reachable", icon="✅")
    else:
        st.error("Backend unreachable", icon="⚠️")

    st.divider()
    st.caption(
        "PDF download works automatically only if this app can read the "
        "server's filesystem (e.g. local dev). Otherwise the file path is "
        "shown for reference."
    )

# --------------------------------------------------------------------------
# Main — input form
# --------------------------------------------------------------------------

st.title("📄 Resume Agent")
st.caption("Tailor your resume to a job description and generate a polished PDF.")

with st.form("workflow_form", clear_on_submit=False):
    st.markdown("#### Resume & Job Description")
    col1, col2 = st.columns(2)
    with col1:
        resume_text = st.text_area(
            "Your current resume (plain text)",
            height=280,
            placeholder="Paste your resume text here…",
        )
    with col2:
        job_description = st.text_area(
            "Target job description",
            height=280,
            placeholder="Paste the job description here…",
        )

    st.markdown("#### Contact details")
    st.caption("Used verbatim on the generated resume — nothing here is inferred.")
    c1, c2, c3 = st.columns(3)
    with c1:
        full_name = st.text_input("Full name")
        email = st.text_input("Email")
    with c2:
        phone = st.text_input("Phone")
        linkedin_url = st.text_input("LinkedIn URL")
    with c3:
        github_url = st.text_input("GitHub URL")

    submitted = st.form_submit_button("Generate tailored resume", use_container_width=True)

if submitted:
    if not resume_text.strip() or not job_description.strip():
        st.warning("Please provide both your resume text and the job description.")
    else:
        payload = {
            "resume_text": resume_text,
            "job_description": job_description,
            "full_name": full_name or None,
            "email": email or None,
            "phone": phone or None,
            "linkedin_url": linkedin_url or None,
            "github_url": github_url or None,
        }
        try:
            with st.spinner("Running the workflow — analyzing, rewriting, and rendering the PDF…"):
                result = call_workflow(api_url, payload)
            st.session_state.last_result = result
        except requests.exceptions.Timeout:
            st.error("The request timed out. The workflow may still be running on the server.")
        except requests.exceptions.ConnectionError:
            st.error(f"Could not connect to the backend at {api_url}.")
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = e.response.json().get("detail", "")
            except Exception:
                pass
            st.error(f"Backend returned an error ({e.response.status_code}). {detail}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# --------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------

if "last_result" in st.session_state:
    raw_result = st.session_state.last_result
    # Backend sometimes nests the payload under "result" (see FastAPI route);
    # unwrap it so the rendering functions always see a flat state dict.
    result = raw_result["result"] if isinstance(raw_result.get("result"), dict) else raw_result
    st.divider()
    st.markdown("### 📎 Generated Resume")

    pdf_filename = result.get("pdf_filename")
    pdf_path = result.get("pdf_path")

    if pdf_filename:
        st.success(f"PDF generated: **{pdf_filename}**", icon="🎉")
        pdf_bytes = read_local_pdf(pdf_path)
        if pdf_bytes:
            st.download_button(
                "⬇️ Download resume PDF",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.info(f"PDF saved on the server at: `{pdf_path}`")
    else:
        st.warning("The workflow completed, but PDF generation failed. See details below.")

    consumed_keys: set[str] = {"pdf_filename", "pdf_path"}
    consumed_keys |= render_analyzer_output(result)
    consumed_keys |= render_interview_prep(result)
    consumed_keys |= render_cover_letter(result)
    render_remaining(result, consumed_keys)