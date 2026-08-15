from typing import TypedDict, List, Dict, Optional


class ResumeAgentState(TypedDict):

    # =========================
    # INPUT DATA
    # =========================

    resume_text: str
    job_description: str


    # =========================
    # ANALYZER AGENT OUTPUT
    # =========================
    role : str
    seniority : str
    company: str
    tech_stack : List[str]
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

    rewritten_resume: Optional[str]
    rewritten_bullet_points: List[str]

    cover_letter: Optional[str]



    # =========================
    # CRITIC / REVIEWER OUTPUT
    # =========================

    critic_score: Optional[float]
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
    gap_questions: List[str]
    preparation_tips: List[str]
    key_topics_to_review: List[str]
    expected_questions: List[str]
    
