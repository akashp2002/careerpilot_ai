import os
from dotenv import load_dotenv
load_dotenv()
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.agents.state import GraphState
from app.agents.supervisor import supervisor_node
from app.agents.job_search import job_search_node
from app.agents.hitl import hitl_node
from app.agents.routing import route_after_hitl
from app.agents.matching import matching_ranking_node
from app.agents.jd_analysis import jd_analysis_node
from app.agents.explanation import explanation_node



DATABASE_URL = os.getenv("DATABASE_URL").replace("+asyncpg", "")  # psycopg format for checkpointer

builder = StateGraph(GraphState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("job_search", job_search_node)
builder.add_node("jd_analysis",jd_analysis_node)
builder.add_node("matching_ranking", matching_ranking_node)
builder.add_node("explanation", explanation_node)
builder.add_node("hitl", hitl_node)

builder.set_entry_point("supervisor")
builder.add_edge("supervisor", "job_search")
builder.add_edge("job_search", "jd_analysis")
builder.add_edge("jd_analysis", "matching_ranking")
builder.add_edge("matching_ranking", "explanation")
builder.add_edge("explanation", "hitl")

builder.add_conditional_edges(
    "hitl",
    route_after_hitl,
    {
        "end": END,
        "supervisor": "supervisor",
        "matching_ranking": "matching_ranking",
    },
)

def build_graph(checkpointer):
    """Compiles the graph against an already-open checkpointer connection."""
    return builder.compile(checkpointer=checkpointer)