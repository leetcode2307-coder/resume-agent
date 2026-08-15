from typing import List, Annotated
from pydantic import BaseModel, Field


class AnalyzerOutput(BaseModel):
    """Output model for the resume analyzer agent."""
    
    role: Annotated[
        str,
        Field(
            default="",
            description="Role in the job description"
        )
    ]
    
    seniority: Annotated[
        str,
        Field(
            default="",
            description="Seniority present in the job description like Junior, Mid, Senior, Lead"
        )
    ]
    
    company: Annotated[
        str,
        Field(
            default="",
            description="Name of the company present in the job description"
        )
    ]
    
    tech_stack: Annotated[
        List[str] | None,
        Field(
            default=None,
            description="Tech stack "
        )
    ]
    
    matching_skills: Annotated[
        List[str],
        Field(
            default=[],
            description="Skills present in both the resume and job description."
        )
    ]
    
    missing_skills: Annotated[
        List[str],
        Field(
            default=[],
            description="Important job requirements missing or not sufficiently demonstrated in the resume."
        )
    ]
    
    nice_to_have_skills: Annotated[
        List[str],
        Field(
            default=[],
            description="Optional or preferred skills mentioned in the job description."
        )
    ]
    
    strengths: Annotated[
        List[str],
        Field(
            default=[],
            description="Candidate strengths relevant to the target job."
        )
    ]
    
    weaknesses: Annotated[
        List[str],
        Field(
            default=[],
            description="Candidate weaknesses or gaps relative to the target job."
        )
    ]
    
    keyword_matches: Annotated[
        List[str],
        Field(
            default=[],
            description="Important keywords from the job description that are clearly represented in the resume."
        )
    ]
    
    keyword_gaps: Annotated[
        List[str],
        Field(
            default=[],
            description="Important job-description keywords missing or weakly represented in the resume."
        )
    ]
    
    ats_score: Annotated[
        float,
        Field(
            default=0.0,
            ge=0,
            le=100,
            description="Estimated ATS compatibility score from 0 to 100."
        )
    ]
    
    initial_match_score: Annotated[
        float,
        Field(
            default=0.0,
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
            default=[],
            description="Comprehensive list of interview questions covering technical, behavioral, and situational aspects."
        )
    ]
    
    technical_questions: Annotated[
        List[str],
        Field(
            default=[],
            description="Technical questions based on required skills, frameworks, and tools mentioned in the job description."
        )
    ]
    
    behavioral_questions: Annotated[
        List[str],
        Field(
            default=[],
            description="Behavioral questions to assess soft skills, past experiences, and problem-solving approach."
        )
    ]
    
    gap_questions: Annotated[
        List[str],
        Field(
            default=[],
            description="Questions addressing specific gaps and weaknesses identified in the resume."
        )
    ]
    
    preparation_tips: Annotated[
        List[str],
        Field(
            default=[],
            description="Recommended preparation strategies and key topics to focus on before the interview."
        )
    ]
    
    key_topics_to_review: Annotated[
        List[str],
        Field(
            default=[],
            description="Important concepts, technologies, or skills to brush up on before the interview."
        )
    ]
    
    expected_questions: Annotated[
        List[str],
        Field(
            default=[],
            description="High-priority questions that are most likely to be asked based on the job description and common interview patterns."
        )
    ]
    
class RewriterOutput(BaseModel):
    """Output model for the rewriter agent."""
    
    rewritten_resume: Annotated[
            List[str]|None,
            Field(
                default=None,
                description="Rewritten resume"
            )
    ]
    
    rewritten_bullet_points: Annotated[
                List[str]|None,
                Field(
                    default=None,
                    description="rewritten bullet points"
                )
    ]
    
    cover_letter: Annotated[
                List[str]|None,
                Field(
                    default=None,
                    description="cover letter"
                )
    ]
    
    

class CriticOutput(BaseModel):
    """Structured output for the critic agent evaluation"""
    
    critic_score: float
    """Quality score from 0-10"""
    
    critic_feedback: List[str]
    """List of feedback points about the rewrite"""
    
    detected_errors: List[str]
    """List of errors found in the rewritten content"""
    
    weak_phrasing: List[str]
    """List of weak phrases or sentences that need improvement"""