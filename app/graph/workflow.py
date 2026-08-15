from langgraph.graph import StateGraph,START,END
from app.agents.analyzer import analyzer
from app.agents.interview import interviewer
from app.graph.state import ResumeAgentState



def input_node(state:ResumeAgentState):
    """
    Returns resume_text + job_description
    """
    
    return{
        'resume_text': state['resume_text'],
        'job_description': state['job_description']
    }
    

graph = StateGraph(ResumeAgentState)


#add nodes
graph.add_node('input_node',input_node)
graph.add_node('analyzer_node',analyzer.analyzer_node)
graph.add_node('interview_agent',interviewer.interview_agent)

#add edges
graph.add_edge(START,'input_node')
graph.add_edge('input_node','analyzer_node')
graph.add_edge('analyzer_node','interview_agent')
graph.add_edge('interview_agent',END)

workflow = graph.compile()

intitial_state = {
    "resume_text" : """
        Python Developer
    
        Skills:
        Python
        FastAPI
        LangChain
        LangGraph
        Git
    
        Built a RAG chatbot using LangChain.
        """
        ,
        "job_description" : """
        We are hiring an AI Engineer.
    
        Requirements:
        Python
        FastAPI
        LangChain
        LangGraph
        RAG
        Docker
        AWS
    
        Good to have:
        Kubernetes
        Terraform
        """
}



def workflow_result():
    return workflow.invoke(intitial_state)



# from langgraph.graph import StateGraph, START, END
# from app.agents.analyzer import analyzer
# from app.agents.interview import interviewer
# from app.agents.rewriter import rewriter
# from app.agents.critic import critic_agent
# from app.graph.state import ResumeAgentState


# def input_node(state: ResumeAgentState):
#     """
#     Returns resume_text + job_description
#     """
#     return {
#         'resume_text': state['resume_text'],
#         'job_description': state['job_description']
#     }


# def should_rewrite(state: ResumeAgentState) -> str:
#     """
#     Decision node to determine if rewriting is needed based on match score
#     """
#     # If initial match score is low, proceed with rewriting
#     if state['initial_match_score'] < 70:  # Example threshold
#         return "rewriter_node"
#     else:
#         # If match score is acceptable, skip to interview preparation
#         return "interview_agent"


# def should_continue_rewriting(state: ResumeAgentState) -> str:
#     """
#     Decision node to check if rewriting quality meets threshold
#     """
#     # Check if we've exceeded max iterations
#     if state['rewrite_iteration'] >= state['max_rewrite_iterations']:
#         return "interview_agent"
    
#     # Check if critic score meets quality threshold
#     if state['critic_score'] is not None and state['critic_score'] >= state['quality_threshold']:
#         return "interview_agent"
#     else:
#         # Continue rewriting with feedback
#         return "rewriter_node"


# def workflow_result():
#     """
#     Execute the complete workflow with the initial state
#     """
#     # Create the state graph
#     graph = StateGraph(ResumeAgentState)
    
#     # Add nodes
#     graph.add_node('input_node', input_node)
#     graph.add_node('analyzer_node', analyzer.analyzer_node)
#     graph.add_node('rewriter_node', rewriter.rewriter_node)
#     graph.add_node('critic_agent', critic_agent.critic_node)
#     graph.add_node('interview_agent', interviewer.interview_agent)
    
#     # Add edges
#     graph.add_edge(START, 'input_node')
#     graph.add_edge('input_node', 'analyzer_node')
    
#     # Conditional edge from analyzer to either rewriter or interview agent
#     graph.add_conditional_edges(
#         'analyzer_node',
#         should_rewrite,
#         {
#             "rewriter_node": "rewriter_node",
#             "interview_agent": "interview_agent"
#         }
#     )
    
#     # Edge from rewriter to critic agent
#     graph.add_edge('rewriter_node', 'critic_agent')
    
#     # Conditional edge from critic agent to either continue rewriting or proceed to interview
#     graph.add_conditional_edges(
#         'critic_agent',
#         should_continue_rewriting,
#         {
#             "rewriter_node": "rewriter_node",
#             "interview_agent": "interview_agent"
#         }
#     )
    
#     # Edge from interview agent to END
#     graph.add_edge('interview_agent', END)
    
#     # Compile the workflow
#     workflow = graph.compile()
    
#     # Initial state
#     initial_state = {
#         "resume_text": """
#             Python Developer
        
#             Skills:
#             Python
#             FastAPI
#             LangChain
#             LangGraph
#             Git
        
#             Built a RAG chatbot using LangChain.
#             """,
#         "job_description": """
#             We are hiring an AI Engineer.
        
#             Requirements:
#             Python
#             FastAPI
#             LangChain
#             LangGraph
#             RAG
#             Docker
#             AWS
        
#             Good to have:
#             Kubernetes
#             Terraform
#             """,
#         # Initialize workflow control variables
#         "rewrite_iteration": 0,
#         "max_rewrite_iterations": 3,
#         "quality_threshold": 8.0,  # Example: score out of 10
        
#     }
    
#     # Invoke the workflow
#     return workflow.invoke(initial_state)


# # Helper function to run the workflow with custom state
# def run_workflow_with_state(state: ResumeAgentState):
#     """
#     Run the workflow with a custom state
#     """
#     graph = StateGraph(ResumeAgentState)
    
#     # Add nodes
#     graph.add_node('input_node', input_node)
#     graph.add_node('analyzer_node', analyzer.analyzer_node)
#     graph.add_node('rewriter_node', rewriter.rewriter_node)
#     graph.add_node('critic_agent', critic_agent.critic_node)
#     graph.add_node('interview_agent', interviewer.interview_agent)
    
#     # Add edges with conditional logic
#     graph.add_edge(START, 'input_node')
#     graph.add_edge('input_node', 'analyzer_node')
    
#     graph.add_conditional_edges(
#         'analyzer_node',
#         should_rewrite,
#         {
#             "rewriter_node": "rewriter_node",
#             "interview_agent": "interview_agent"
#         }
#     )
    
#     graph.add_edge('rewriter_node', 'critic_agent')
    
#     graph.add_conditional_edges(
#         'critic_agent',
#         should_continue_rewriting,
#         {
#             "rewriter_node": "rewriter_node",
#             "interview_agent": "interview_agent"
#         }
#     )
    
#     graph.add_edge('interview_agent', END)
    
#     workflow = graph.compile()
#     return workflow.invoke(state)