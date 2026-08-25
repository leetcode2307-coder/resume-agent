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
            result = await structured_llm.ainvoke([
                ("system", ANALYZER_SYSTEM_PROMPT),
                ("human", prompt),
            ])
        except Exception:
            logger.exception("Analyzer LLM call failed")
            raise

        if result is None:
            raise ValueError("Analyzer LLM returned no structured output.")

        payload = result.model_dump() if hasattr(result, "model_dump") else result
        if not isinstance(payload, dict):
            payload = getattr(result, "__dict__", {})

        return {
            'role': payload.get('role'),
            'seniority': payload.get('seniority'),
            'tech_stack': payload.get('tech_stack', []),
            'company': payload.get('company'),
            'matching_skills': payload.get('matching_skills', []),
            'missing_skills': payload.get('missing_skills', []),
            'nice_to_have_skills': payload.get('nice_to_have_skills', []),
            'strengths': payload.get('strengths', []),
            'weaknesses': payload.get('weaknesses', []),
            'keyword_matches': payload.get('keyword_matches', []),
            'keyword_gaps': payload.get('keyword_gaps', []),
            'ats_score': payload.get('ats_score', 0),
            'initial_match_score': payload.get('initial_match_score', 0),
        }


analyzer = AnalyzerAgent()