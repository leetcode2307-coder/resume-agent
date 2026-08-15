from typing import TypedDict, List, Optional


class ResumeAgentState(TypedDict, total=False):
    # =========================
    # INPUT DATA
    # =========================
    resume_text: str
    job_description: str

    # =========================
    # ANALYZER AGENT OUTPUT
    # =========================
    role: str
    seniority: str
    company: str
    tech_stack: Optional[List[str]]
    matching_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    nice_to_have_skills: Optional[List[str]]

    strengths: Optional[List[str]]
    weaknesses: Optional[List[str]]

    keyword_matches: Optional[List[str]]
    keyword_gaps: Optional[List[str]]

    ats_score: Optional[float]
    initial_match_score: Optional[float]

    # =========================
    # REWRITER AGENT OUTPUT
    # =========================
    rewritten_resume: Optional[str]
    rewritten_bullet_points: Optional[List[str]]
    cover_letter: Optional[str]

    # =========================
    # CRITIC / REVIEWER OUTPUT
    # =========================
    critic_score: Optional[float]
    critic_feedback: Optional[List[str]]
    detected_errors: Optional[List[str]]
    weak_phrasing: Optional[List[str]]

    # =========================
    # WORKFLOW CONTROL
    # =========================
    rewrite_iteration: Optional[int]
    max_rewrite_iterations: Optional[int]

    quality_threshold: Optional[float]

    # =========================
    # FINAL OUTPUT
    # =========================
    interview_questions: Optional[List[str]]
    technical_questions: Optional[List[str]]
    gap_questions: Optional[List[str]]
    preparation_tips: Optional[List[str]]
    key_topics_to_review: Optional[List[str]]
    expected_questions: Optional[List[str]]

