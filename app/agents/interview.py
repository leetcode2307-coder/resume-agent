import asyncio
from app.graph.state import ResumeAgentState
from app.llm import llm
from app.schemas.resume import InterviewerOutput
from app.prompts import INTERVIWER_SYSTEM_PROMPT

class InterviewPrepAgent:
    
    
    async def interview_agent(self,state : ResumeAgentState):
        """
        Generates likely interview question for the role
        """
        
        # Invoking the required fields from the llm using with_structured_output
        structured_llm = llm.with_structured_output(InterviewerOutput)
        
        prompt = f"""
        I need you to prepare me for an upcoming interview. Please analyze the following resume and job description to generate a tailored list of questions and study topics.

        **Resume Content:**
        {state['resume_text']}

        **Job Description:**
        {state['job_description']}

        **Role Context:**
        - Company Industry: {state['company']}
        - Position Level (e.g., Junior, Mid, Senior, Lead): {state['seniority']}
        - Tech Stack Specifics (if any): {state['tech_stack']}

        Please generate the interview preparation materials. Make the questions challenging and specific to my background and the role's requirements. Pay special attention to any red flags or skill gaps between my current experience and the job's "Must-Haves."

        Return the output strictly as a valid JSON object matching the InterviewerOutput schema. Do not include any extra commentary outside the JSON structure.
        """
        
        # Run the blocking LLM call in a thread to avoid blocking the event loop
        result = await asyncio.to_thread(
            structured_llm.invoke,
            [
                ("system",INTERVIWER_SYSTEM_PROMPT),
                ("human",prompt)
            ]
        )
        
        return {
            'interview_questions': result.interview_questions,
            'technical_questions': result.technical_questions,
            'gap_questions': result.gap_questions,
            'preparation_tips': result.preparation_tips,
            'key_topics_to_review': result.key_topics_to_review,
            'expected_questions': result.expected_questions 
        }
        
interviewer = InterviewPrepAgent()
        
        
        
        