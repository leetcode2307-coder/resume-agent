from app.llm import llm
from app.schemas.resume import AnalyzerOutput
from app.prompts import ANALYZER_SYSTEM_PROMPT
from app.graph.state import ResumeAgentState

class AnalyzerAgent:
    
        
    def analyzer_node(self,state:ResumeAgentState):
        """
        Analyzes the resume_text + job_description and determines the matching_skills,missing_skills,
        nice_to_have_skills,strengths,weaknesses,keyword_matches,keyword_gaps,ats_score,initial_match_score
        and then stores all in state
        """
        
        # Invoking the required fields from the llm using with_structured_output
        structured_llm = llm.with_structured_output(AnalyzerOutput)
        
        prompt = f"""
        Analyze the following resume against the job description.

        ========================
        RESUME
        ========================

        {state['resume_text']}


        ========================
        JOB DESCRIPTION
        ========================

        {state['job_description']}


        Perform a detailed comparison.

        Return the result according to the required structured schema.
        """
        
        result = structured_llm.invoke(
            [
                ("system",ANALYZER_SYSTEM_PROMPT),
                ("human",prompt)
            ]
        )
        
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
