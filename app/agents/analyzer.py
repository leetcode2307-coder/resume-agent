#analzer.py
import asyncio
import logging

from app.llm import llm
from app.schemas.resume import AnalyzerOutput
from app.prompts import ANALYZER_SYSTEM_PROMPT
from app.graph.state import ResumeAgentState

logger = logging.getLogger(__name__)


class AnalyzerAgent:

    async def analyzer_node(self, state: ResumeAgentState):
        """
        Analyzes the resume_text + job_description and determines the matching_skills,missing_skills,
        nice_to_have_skills,strengths,weaknesses,keyword_matches,keyword_gaps,ats_score,initial_match_score
        and then stores all in state
        """

        resume_text = (state.get('resume_text') or "").strip()
        job_description = (state.get('job_description') or "").strip()

        # Fail fast on obviously unusable input instead of spending an LLM
        # call on it -- mirrors the <inputs> handling described in
        # ANALYZER_SYSTEM_PROMPT, but caught here before hitting the model.
        if not resume_text or not job_description:
            logger.warning(
                "analyzer_node called with missing resume_text or job_description"
            )
            return {
                'role': None,
                'seniority': None,
                'tech_stack': [],
                'company': None,
                'matching_skills': [],
                'missing_skills': [],
                'nice_to_have_skills': [],
                'strengths': [],
                'weaknesses': [],
                'keyword_matches': [],
                'keyword_gaps': [],
                'ats_score': 0,
                'initial_match_score': 0,
            }

        # Invoking the required fields from the llm using with_structured_output
        structured_llm = llm.with_structured_output(AnalyzerOutput)

        prompt = f"""
        Analyze the following resume against the job description.

        ========================
        RESUME
        ========================

        {resume_text}


        ========================
        JOB DESCRIPTION
        ========================

        {job_description}


        Perform a detailed comparison, strictly following the definitions,
        process, and rules defined in the system prompt. Be conservative
        when evidence is weak or absent.

        Return the result according to the required structured schema.
        """

        try:
            # Run the blocking LLM call in a thread to avoid blocking the event loop
            result = await asyncio.to_thread(
                structured_llm.invoke,
                [
                    ("system", ANALYZER_SYSTEM_PROMPT),
                    ("human", prompt)
                ]
            )
        except Exception:
            logger.exception("Analyzer LLM call failed")
            raise

        return {
            'role': result.role,
            'seniority': result.seniority,
            'tech_stack': result.tech_stack,
            'company': result.company,
            'matching_skills': result.matching_skills,
            'missing_skills': result.missing_skills,
            'nice_to_have_skills': result.nice_to_have_skills,
            'strengths': result.strengths,
            'weaknesses': result.weaknesses,
            'keyword_matches': result.keyword_matches,
            'keyword_gaps': result.keyword_gaps,
            'ats_score': result.ats_score,
            'initial_match_score': result.initial_match_score,
        }


analyzer = AnalyzerAgent()