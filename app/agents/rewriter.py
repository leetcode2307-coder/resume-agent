import asyncio
from app.llm import llm
from app.graph.state import ResumeAgentState
from app.schemas.resume import RewriterOutput
from app.prompts import REWRITER_SYSTEM_PROMPT  # You'll need to create this

class Rewriter:
    
    async def rewriter_node(self, state: ResumeAgentState):
        """
        Rewrite the resume bullet points, tailor to JD keywords, draft cover letter
        """
        
        # Invoking the required fields from the llm using with_structured_output
        structured_llm = llm.with_structured_output(RewriterOutput)
        
        prompt = f"""
        Rewrite and improve the resume based on the job description and analysis.

        ========================
        RESUME
        ========================

        {state['resume_text']}


        ========================
        JOB DESCRIPTION
        ========================

        {state['job_description']}


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

        Based on the above information, please:
        1. Rewrite the resume bullet points to be more impactful and ATS-friendly
        2. Tailor the resume to incorporate key JD keywords and skills
        3. Highlight matching skills and address missing skills where possible
        4. Draft a compelling cover letter tailored to this specific role and company
        5. Suggest improvements to the resume structure and content

        Return the result according to the required structured schema.
        """
        
        # Run the blocking LLM call in a thread to avoid blocking the event loop
        result = await asyncio.to_thread(
            structured_llm.invoke,
            [
                ("system", REWRITER_SYSTEM_PROMPT),
                ("human", prompt)
            ]
        )
        
        # Return using dot notation (result is a RewriterOutput object)
        # Ensure keys match the state schema used across the workflow
        return {
            'rewritten_resume': result.rewritten_resume,
            'rewritten_bullet_points': result.rewritten_bullet_points,
            'cover_letter': result.cover_letter,
        }

rewriter = Rewriter()