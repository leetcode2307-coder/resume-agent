import asyncio
import logging

from langgraph.graph import END, START, StateGraph

from app.agents.analyzer import analyzer
from app.agents.critic import critic_agent
from app.agents.interview import interviewer
from app.agents.rewriter import rewriter
from app.graph.state import ResumeAgentState

logger = logging.getLogger(__name__)


def input_node(state: ResumeAgentState):
    """Return the upstream resume/job inputs for the graph."""
    return {
        "resume_text": state["resume_text"],
        "job_description": state["job_description"],
    }


def should_rewrite(state: ResumeAgentState) -> list[str]:
    """Decide whether the resume should prepare for filtering or rewriting."""
    # Always run interview prep in parallel
    next_nodes = ["interview_agent"]
    # We must always run rewriter_node to generate the structured_resume for the PDF!
    next_nodes.append("rewriter_node")
    return next_nodes


def should_continue_rewriting(state: ResumeAgentState) -> str:
    """Check whether the resume should keep rewriting or move to finalize."""
    if state.get("rewrite_iteration", 0) >= state.get("max_rewrite_iterations", 0):
        return "finalize_node"
    if state.get("critic_score") is not None and state.get("critic_score", 0) >= state.get("quality_threshold", 0):
        return "finalize_node"
    return "rewriter_node"


def finalize_node(state: ResumeAgentState):
    """Restore the best rewriting attempt if the final one was degraded."""
    best_score = state.get("best_critic_score")
    current_score = state.get("critic_score")
    
    if best_score is not None and current_score is not None and best_score > current_score:
        return {
            "critic_score": best_score,
            "rewritten_resume": state.get("best_rewritten_resume"),
            "rewritten_bullet_points": state.get("best_rewritten_bullet_points", []),
            "cover_letter": state.get("best_cover_letter"),
            "structured_resume": state.get("best_structured_resume"),
        }
    return {}


def _build_workflow():
    graph = StateGraph(ResumeAgentState)

    graph.add_node("input_node", input_node)
    graph.add_node("analyzer_node", analyzer.analyzer_node)
    graph.add_node("rewriter_node", rewriter.rewriter_node)
    graph.add_node("critic_agent", critic_agent.critic_node)
    graph.add_node("finalize_node", finalize_node)
    graph.add_node("interview_agent", interviewer.interview_agent)

    graph.add_edge(START, "input_node")
    graph.add_edge("input_node", "analyzer_node")

    graph.add_conditional_edges(
        "analyzer_node",
        should_rewrite,
    )

    graph.add_edge("rewriter_node", "critic_agent")

    graph.add_conditional_edges(
        "critic_agent",
        should_continue_rewriting,
        {"rewriter_node": "rewriter_node", "finalize_node": "finalize_node"},
    )

    graph.add_edge("finalize_node", END)
    graph.add_edge("interview_agent", END)
    return graph.compile()


async def workflow_result_async(
    resume_text: str,
    job_description: str,
    *,
    full_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    linkedin_url: str | None = None,
    github_url: str | None = None,
):
    """Stream agent updates from the graph while preserving the final accumulated state."""
    workflow = _build_workflow()

    initial_state = {
        "resume_text": resume_text,
        "job_description": job_description,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "linkedin_url": linkedin_url,
        "github_url": github_url,
        "rewrite_iteration": 0,
        "max_rewrite_iterations": 3,
        "critic_score": None,
        "quality_threshold": 8,
    }

    final_state = dict(initial_state)

    try:
        yield {
            "event": "workflow_started",
            "agent": "workflow",
            "data": {"status": "started"},
        }

        async for update in workflow.astream(
            initial_state,
            stream_mode="updates",
        ):
            if not isinstance(update, dict):
                continue

            for node_name, node_update in update.items():
                if node_name == "analyzer_node":
                    yield {
                        "event": "agent_completed",
                        "agent": "analyzer",
                        "data": node_update,
                    }
                elif node_name == "rewriter_node":
                    yield {
                        "event": "agent_completed",
                        "agent": "rewriter",
                        "data": node_update,
                    }
                elif node_name == "critic_agent":
                    yield {
                        "event": "agent_completed",
                        "agent": "critic",
                        "data": node_update,
                    }
                elif node_name == "interview_agent":
                    yield {
                        "event": "agent_completed",
                        "agent": "interview_prep",
                        "data": node_update,
                    }

                if isinstance(node_update, dict):
                    final_state.update(node_update)

        yield {
            "event": "workflow_state_ready",
            "agent": "workflow",
            "data": {"state": final_state},
        }

    except asyncio.CancelledError:
        logger.warning("Workflow execution was cancelled by the client.")
        raise
    except Exception as exc:
        logger.exception("LangGraph workflow execution failed")
        yield {
            "event": "workflow_error",
            "agent": "workflow",
            "error": str(exc),
            "error_type": type(exc).__name__,
        }

