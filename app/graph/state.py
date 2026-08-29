from typing import List, TypedDict


class ResumeAgentState(TypedDict):
    # =========================
    # INPUT DATA
    # =========================
    resume_text: str
    job_description: str

    # Contact info
    full_name: str | None
    email: str | None
    phone: str | None
    linkedin_url: str | None
    github_url: str | None

    # =========================
    # ANALYZER AGENT OUTPUT
    # =========================
    role: str 
    seniority: str | None
    company: str | None
    tech_stack: List[str]
    matching_skills: List[str]
    missing_skills: List[str]
    nice_to_have_skills: List[str]

    strengths: List[str]
    weaknesses: List[str]

    keyword_matches: List[str]
    keyword_gaps: List[str]

    ats_score: float
    initial_match_score: float

    # =========================
    # REWRITER AGENT OUTPUT
    # =========================
    rewritten_resume: str 
    rewritten_bullet_points: List[str]
    cover_letter: str | None
    structured_resume: dict | None  # dict representation of StructuredResume

    # =========================
    # CRITIC / REVIEWER OUTPUT
    # =========================
    critic_score: float
    critic_feedback: List[str]
    detected_errors: List[str]
    weak_phrasing: List[str]

    # =========================
    # WORKFLOW CONTROL
    # =========================
    rewrite_iteration: int
    max_rewrite_iterations: int
    quality_threshold: float

    # =========================
    # FINAL OUTPUT
    # =========================
    interview_questions: List[str]
    technical_questions: List[str]
    behavioral_questions: List[str]
    gap_questions: List[str]
    preparation_tips: List[str]
    key_topics_to_review: List[str]
    expected_questions: List[str]