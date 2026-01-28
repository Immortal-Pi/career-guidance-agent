from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END

from rag.s3_vectors import retrieve_utd_context
from tools.serpapi_jobs import serpapi_google_jobs
from tools.tavily_search import tavily_web_search
from rag.s3_vectors import bedrock_synthesize_answer


class GraphState(TypedDict):
    question: str
    utd_context: NotRequired[str]
    jobs: NotRequired[dict]
    web: NotRequired[dict]
    answer: NotRequired[str]


def node_retrieve(state: GraphState) -> GraphState:
    ctx = retrieve_utd_context(state["question"])
    return {**state, "utd_context": ctx}


def node_jobs(state: GraphState) -> GraphState:
    jobs = serpapi_google_jobs(query=state["question"])
    return {**state, "jobs": jobs}


def node_web(state: GraphState) -> GraphState:
    # Useful for “project ideas” + “skills in demand” style queries
    web = tavily_web_search(
        query=f"Ideal student project ideas based on job market demand: {state['question']}"
    )
    return {**state, "web": web}


def node_synthesize(state: GraphState) -> GraphState:
    answer = bedrock_synthesize_answer(
        question=state["question"],
        utd_context=state.get("utd_context", ""),
        jobs=state.get("jobs", {}),
        web=state.get("web", {}),
    )
    return {**state, "answer": answer}


def build_graph():
    g = StateGraph(GraphState)
    g.add_node("retrieve", node_retrieve)
    g.add_node("jobs", node_jobs)
    g.add_node("web", node_web)
    g.add_node("synthesize", node_synthesize)

    g.add_edge(START, "retrieve")
    g.add_edge("retrieve", "jobs")
    g.add_edge("jobs", "web")
    g.add_edge("web", "synthesize")
    g.add_edge("synthesize", END)

    return g.compile()
