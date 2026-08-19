import asyncio
from app.llm import llm
from app.prompts import CRITIC_AGENT_PROMPT
from app.graph.state import ResumeAgentState
from app.schemas.resume import CriticOutput  # You'll need to create this

class CriticAgent:
    
    async def critic_node(self, state: ResumeAgentState):
        """
        Evaluate rewritten content then score quality between range 0 to 10,
        flag errors and weak parsing
        """
        
        # Invoking the required fields from the llm using with_structured_output
        structured_llm = llm.with_structured_output(CriticOutput)
        
        prompt = f"""
        Evaluate the rewritten resume content and provide a quality assessment.

        ========================
        ORIGINAL RESUME
        ========================

        {state['resume_text']}


        ========================
        JOB DESCRIPTION
        ========================

        {state['job_description']}


        ========================
        REWRITTEN CONTENT
        ========================

        Rewritten Resume: {state.get('rewritten_resume', 'Not available')}
        
        Tailored Bullet Points: {state.get('rewritten_bullet_points', [])}
        
        Cover Letter: {state.get('cover_letter', 'Not available')}


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
        TASK
        ========================

        Based on the above information, please evaluate the rewritten content and:

        1. Score the quality of the rewritten resume on a scale of 0-10
           - 0-3: Poor, needs significant improvement
           - 4-6: Average, some improvements needed
           - 7-8: Good, minor improvements needed
           - 9-10: Excellent, ready for submission

        2. Provide detailed feedback on the quality of the rewrite
           - What was done well
           - What needs improvement
           - Specific suggestions for enhancement

        3. Flag any errors detected in the rewritten content
           - Grammar/spelling mistakes
           - Formatting issues
           - Factual inconsistencies
           - Missing critical information

        4. Identify weak phrasing in the rewritten content
           - Passive voice
           - Generic statements
           - Overused buzzwords
           - Vague accomplishments
           - Lacking impact or quantifiable results

        Return the result according to the required structured schema.
        """
        
        # Run the blocking LLM call in a thread to avoid blocking the event loop
        result = await asyncio.to_thread(
            structured_llm.invoke,
            [
                ("system", CRITIC_AGENT_PROMPT),
                ("human", prompt)
            ]
        )
        
        # Return using dot notation (result is a CriticOutput object)
        return {
            'critic_score': result.critic_score,
            'critic_feedback': result.critic_feedback,
            'detected_errors': result.detected_errors,
            'weak_phrasing': result.weak_phrasing,
            # Preserve cover letter so downstream nodes and final result keep it
            'cover_letter': state.get('cover_letter'),
            # Increment iteration counter
            'rewrite_iteration': state.get('rewrite_iteration', 0) + 1
        }

critic_agent = CriticAgent()