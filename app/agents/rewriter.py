import asyncio
import logging

from app.llm import primary_llm as llm
from app.graph.state import ResumeAgentState
from app.schemas.resume import RewriterOutput
from app.prompts import REWRITER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class Rewriter:

    async def rewriter_node(self, state: ResumeAgentState):
        """
        Rewrite the resume bullet points, tailor to JD keywords, draft cover letter
        """

        resume_text = (state.get('resume_text') or "").strip()
        job_description = (state.get('job_description') or "").strip()

        # Fail fast on unusable input instead of spending an LLM call on it --
        # mirrors the <inputs> handling described in REWRITER_SYSTEM_PROMPT,
        # enforced here before hitting the model.
        if not resume_text or not job_description:
            logger.warning(
                "rewriter_node called with missing resume_text or job_description"
            )
            return {
                'rewritten_resume': None,
                'rewritten_bullet_points': [],
                'cover_letter': None,
            }

        # Invoking the required fields from the llm using with_structured_output
        structured_llm = llm.with_structured_output(RewriterOutput)

        best_attempt_context = ""
        best_score = state.get("best_critic_score")
        if best_score is not None:
            best_attempt_context = f"""
        ========================
        PREVIOUS BEST ATTEMPT (Score: {best_score}/10)
        ========================
        Your previous best rewrite scored {best_score}/10. 
        Improve upon this version by addressing the feedback. DO NOT degrade the quality or lose good additions!
        
        Previous Best Resume:
        {state.get('best_rewritten_resume', 'N/A')}
        """

        prompt = f"""
        Rewrite and improve the resume based on the job description and analysis.

        ========================
        RESUME
        ========================

        {resume_text}


        ========================
        JOB DESCRIPTION
        ========================

        {job_description}


        ========================
        ANALYSIS RESULTS
        ========================

        Role: {state.get('role', 'Not specified')}
        Company: {state.get('company', 'Not specified')}
        Seniority: {state.get('seniority', 'Not specified')}
        Tech Stack: {state.get('tech_stack', 'Not specified')}
        
        Matching Skills: {state.get('matching_skills', [])}
        Missing Skills: {state.get('missing_skills', [])}
        Nice to Have Skills: {state.get('nice_to_have_skills', [])}
        
        Strengths: {state.get('strengths', [])}
        Weaknesses: {state.get('weaknesses', [])}
        
        Keyword Matches: {state.get('keyword_matches', [])}
        Keyword Gaps: {state.get('keyword_gaps', [])}
        
        ATS Score: {state.get('ats_score', 'N/A')}
        Initial Match Score: {state.get('initial_match_score', 'N/A')}
        
        ========================
        PREVIOUS CRITIQUE FEEDBACK (Address these issues carefully!)
        ========================
        Iteration: {state.get('rewrite_iteration', 0)}
        Critic Feedback: {state.get('critic_feedback', [])}
        Detected Errors: {state.get('detected_errors', [])}
        Weak Phrasing: {state.get('weak_phrasing', [])}
{best_attempt_context}

        ========================
        TASK
        ========================

        Based on the above information, please:
        1. Rewrite the resume bullet points to be more impactful and ATS-friendly
        2. Tailor the resume to incorporate key JD keywords and skills
        3. Highlight matching skills and address missing skills where possible
        4. Draft a compelling cover letter tailored to this specific role and company
        5. Suggest improvements to the resume structure and content

        Follow the integrity rules, process, and quality bar defined in the
        system prompt strictly -- do not invent metrics, skills, employers, or
        experience that are not supported by the resume above.

        IMPORTANT: Ensure that your structured output is strictly valid JSON.
        For multi-line strings like the cover letter, use properly escaped newline characters (\\n) and avoid raw newlines.

        Return the result according to the required structured schema.
        """

        try:
            result = await structured_llm.ainvoke([
                ("system", REWRITER_SYSTEM_PROMPT),
                ("human", prompt),
            ])
        except Exception:
            logger.exception("Rewriter LLM call failed")
            raise

        if result is None:
            raise ValueError("Rewriter LLM returned no structured output.")

        payload = result.model_dump() if hasattr(result, "model_dump") else result
        if not isinstance(payload, dict):
            payload = getattr(result, "__dict__", {})

        return {
            'rewritten_resume': payload.get('rewritten_resume'),
            'rewritten_bullet_points': payload.get('rewritten_bullet_points', []),
            'cover_letter': payload.get('cover_letter'),
            'structured_resume': payload.get('structured_resume')
        }


rewriter = Rewriter()