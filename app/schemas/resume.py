from typing import List, Annotated, Optional
from pydantic import BaseModel, Field


class AnalyzerOutput(BaseModel):
    """Output model for the resume analyzer agent."""

    role: Annotated[
        str,
        Field(
            description="Role in the job description."
        )
    ]

    seniority: Annotated[
        str|None,
        Field(
            description="Seniority present in the job description, such as Junior, Mid, Senior, or Lead."
        )
    ]

    company: Annotated[
        str|None,
        Field(
            description="Name of the company present in the job description."
        )
    ]

    tech_stack: Annotated[
        List[str],
        Field(
            description="Technologies, programming languages, frameworks, libraries, and tools required by the job."
        )
    ]

    matching_skills: Annotated[
        List[str],
        Field(
            description="Skills present in both the resume and job description."
        )
    ]

    missing_skills: Annotated[
        List[str],
        Field(
            description="Important job requirements missing or not sufficiently demonstrated in the resume."
        )
    ]

    nice_to_have_skills: Annotated[
        List[str],
        Field(
            description="Optional or preferred skills mentioned in the job description."
        )
    ]

    strengths: Annotated[
        List[str],
        Field(
            description="Candidate strengths relevant to the target job."
        )
    ]

    weaknesses: Annotated[
        List[str],
        Field(
            description="Candidate weaknesses or gaps relative to the target job."
        )
    ]

    keyword_matches: Annotated[
        List[str],
        Field(
            description="Important keywords from the job description that are clearly represented in the resume."
        )
    ]

    keyword_gaps: Annotated[
        List[str],
        Field(
            description="Important job-description keywords missing or weakly represented in the resume."
        )
    ]

    ats_score: Annotated[
        float,
        Field(
            ge=0,
            le=100,
            description="Estimated ATS compatibility score from 0 to 100."
        )
    ]

    initial_match_score: Annotated[
        float,
        Field(
            ge=0,
            le=100,
            description="Overall match score between the resume and job description from 0 to 100."
        )
    ]


class InterviewerOutput(BaseModel):
    """Output model for the interview preparation agent."""

    interview_questions: Annotated[
        List[str],
        Field(
            description="Comprehensive list of interview questions covering technical, behavioral, and situational aspects."
        )
    ]

    technical_questions: Annotated[
        List[str],
        Field(
            description="Technical questions based on required skills, frameworks, and tools mentioned in the job description."
        )
    ]

    behavioral_questions: Annotated[
        List[str],
        Field(
            description="Behavioral questions to assess soft skills, past experiences, and problem-solving approach."
        )
    ]

    gap_questions: Annotated[
        List[str],
        Field(
            description="Questions addressing specific gaps and weaknesses identified in the resume."
        )
    ]

    preparation_tips: Annotated[
        List[str],
        Field(
            description="Recommended preparation strategies and key topics to focus on before the interview."
        )
    ]

    key_topics_to_review: Annotated[
        List[str],
        Field(
            description="Important concepts, technologies, or skills to review before the interview."
        )
    ]

    expected_questions: Annotated[
        List[str],
        
        Field(
            description="High-priority questions most likely to be asked based on the job description and common interview patterns."
        )
    ]


class RewriterOutput(BaseModel):
    """Output model for the rewriter agent."""

    rewritten_resume: Annotated[
        str,
        Field(description="Complete rewritten resume optimized for the target job while preserving factual information from the original resume.")
    ]

    rewritten_bullet_points: Annotated[
        List[str],
        Field(
            description="Rewritten resume bullet points optimized for clarity, impact, and ATS compatibility."
        )
    ]

    cover_letter: Annotated[
        str|None,
        Field(
            description="Generated cover letter tailored to the target job."
        )
    ]


class CriticOutput(BaseModel):
    """Structured output for the critic agent evaluation."""

    critic_score: Annotated[
        float,
        Field(
            ge=0.0,
            le=10.0,
            description="Quality score of the rewritten resume from 0 to 10."
        )
    ]

    critic_feedback: Annotated[
        List[str],
        Field(
            description="List of feedback points about the rewritten content."
        )
    ]

    detected_errors: Annotated[
        List[str],
        Field(
            description="List of errors found in the rewritten content."
        )
    ]

    weak_phrasing: Annotated[
        List[str],
        Field(
            description="List of weak phrases or sentences that need improvement."
        )
    ]