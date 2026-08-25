import asyncio
import logging

from app.graph.state import ResumeAgentState
from app.llm import llm
from app.schemas.resume import InterviewerOutput
from app.prompts import INTERVIWER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class InterviewPrepAgent:

    async def interview_agent(self, state: ResumeAgentState):
        """
        Generates likely interview questions and prep material for the role.
        """

        resume_text = (state.get('resume_text') or "").strip()
        job_description = (state.get('job_description') or "").strip()

        # Fail fast on unusable input instead of spending an LLM call on it --
        # mirrors the <inputs> handling described in INTERVIWER_SYSTEM_PROMPT,
        # enforced here before hitting the model.
        if not resume_text or not job_description:
            logger.warning(
                "interview_agent called with missing resume_text or job_description"
            )
            return {
                'interview_questions': [],
                'technical_questions': [],
                'gap_questions': [],
                'preparation_tips': [],
                'key_topics_to_review': [],
                'expected_questions': [],
            }

        # Role-context fields come from an upstream node (e.g. the analyzer);
        # default them so a missing/None value doesn't get rendered as the
        # literal string "None" inside the prompt.
        company = state.get('company') or "Not specified"
        seniority = state.get('seniority') or "Not specified"
        tech_stack = state.get('tech_stack') or "Not specified"

        # Invoking the required fields from the llm using with_structured_output
        structured_llm = llm.with_structured_output(InterviewerOutput)

        prompt = f"""
        I need you to prepare me for an upcoming interview. Please analyze the following resume and job description to generate a tailored list of questions and study topics.

        **Resume Content:**
        {resume_text}

        **Job Description:**
        {job_description}

        **Role Context:**
        - Company Industry: {company}
        - Position Level (e.g., Junior, Mid, Senior, Lead): {seniority}
        - Tech Stack Specifics (if any): {tech_stack}

        Please generate the interview preparation materials, strictly following the
        definitions, process, and rules defined in the system prompt. Make the
        questions challenging and specific to my background and the role's
        requirements. Pay special attention to any red flags or skill gaps
        between my current experience and the job's "Must-Haves."

        Return the result according to the required structured schema.
        """

        try:
            result = await structured_llm.ainvoke([
                ("system", INTERVIWER_SYSTEM_PROMPT),
                ("human", prompt),
            ])
        except Exception:
            logger.exception("Interview prep LLM call failed")
            raise

        if result is None:
            raise ValueError("Interview prep LLM returned no structured output.")

        payload = result.model_dump() if hasattr(result, "model_dump") else result
        if not isinstance(payload, dict):
            payload = getattr(result, "__dict__", {})

        return {
            'interview_questions': payload.get('interview_questions', []),
            'behavioral_questions': payload.get('behavioral_questions', []),
            'technical_questions': payload.get('technical_questions', []),
            'gap_questions': payload.get('gap_questions', []),
            'preparation_tips': payload.get('preparation_tips', []),
            'key_topics_to_review': payload.get('key_topics_to_review', []),
            'expected_questions': payload.get('expected_questions', [])
        }


interviewer = InterviewPrepAgent()