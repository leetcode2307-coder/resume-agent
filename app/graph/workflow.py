import asyncio
import inspect
from langgraph.graph import StateGraph, START, END
from app.agents.analyzer import analyzer
from app.agents.interview import interviewer
from app.agents.rewriter import rewriter
from app.agents.critic import critic_agent
from app.graph.state import ResumeAgentState


def input_node(state: ResumeAgentState):
    """
    Returns resume_text + job_description
    """
    return {
        'resume_text': state['resume_text'],
        'job_description': state['job_description']
    }


def should_rewrite(state: ResumeAgentState) -> str:
    """
    Decision node to determine if rewriting is needed based on match score
    """
    # If initial match score is low, proceed with rewriting
    if state['initial_match_score'] < 70:  # Example threshold
        return "rewriter_node"
    else:
        # If match score is acceptable, skip to interview preparation
        return "interview_agent"


def should_continue_rewriting(state: ResumeAgentState) -> str:
    """
    Decision node to check if rewriting quality meets threshold
    """
    # Check if we've exceeded max iterations
    if state['rewrite_iteration'] >= state['max_rewrite_iterations']:
        return "interview_agent"
    
    # Check if critic score meets quality threshold
    if state['critic_score'] is not None and state['critic_score'] >= state['quality_threshold']:
        return "interview_agent"
    else:
        # Continue rewriting with feedback
        return "rewriter_node"


async def workflow_result_async(resume_text: str, job_description: str):
    """
    Execute the complete workflow with the initial state (async-aware)
    """
    # Create the state graph
    graph = StateGraph(ResumeAgentState)

    # Add nodes (nodes may be async coroutines)
    graph.add_node('input_node', input_node)
    graph.add_node('analyzer_node', analyzer.analyzer_node)
    graph.add_node('rewriter_node', rewriter.rewriter_node)
    graph.add_node('critic_agent', critic_agent.critic_node)
    graph.add_node('interview_agent', interviewer.interview_agent)

    # Add edges
    graph.add_edge(START, 'input_node')
    graph.add_edge('input_node', 'analyzer_node')

    # Conditional edge from analyzer to either rewriter or interview agent
    graph.add_conditional_edges(
        'analyzer_node',
        should_rewrite,
        {
            "rewriter_node": "rewriter_node",
            "interview_agent": "interview_agent"
        }
    )

    # Edge from rewriter to critic agent
    graph.add_edge('rewriter_node', 'critic_agent')

    # Conditional edge from critic agent to either continue rewriting or proceed to interview
    graph.add_conditional_edges(
        'critic_agent',
        should_continue_rewriting,
        {
            "rewriter_node": "rewriter_node",
            "interview_agent": "interview_agent"
        }
    )

    # Edge from interview agent to END
    graph.add_edge('interview_agent', END)

    # Compile the workflow
    workflow = graph.compile()

    initial_state = {
        'resume_text': resume_text,
        'job_description': job_description
    }

    # Invoke the workflow using the async API so async nodes are supported
    # LangGraph provides `ainvoke` for async invocation
    if hasattr(workflow, "ainvoke"):
        return await workflow.ainvoke(initial_state)

    # Fallback: if async API is not available, call invoke and await if needed
    invocation = workflow.invoke(initial_state)
    if inspect.isawaitable(invocation):
        return await invocation
    return invocation


def workflow_result(resume_text: str, job_description: str):
    """Sync wrapper kept for backwards compatibility; runs the async workflow."""
    return asyncio.run(workflow_result_async(resume_text, job_description))

