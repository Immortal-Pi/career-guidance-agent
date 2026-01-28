from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END

from rag.s3_vector import retrieve_utd_context, bedrock_synthesize_answer
from tools.serpapi_jobs import serpapi_google_jobs
from tools.tavily_search import tavily_web_search


class GraphState(TypedDict):
    question: str
    utd_context: NotRequired[str]
    jobs: NotRequired[dict]
    web: NotRequired[dict]
    answer: NotRequired[str]


def node_retrieve(state: GraphState) -> GraphState:
    ctx = retrieve_utd_context(state["question"])
    return {**state, "utd_context": ctx}


def node_fetch_jobs(state: GraphState) -> GraphState:
    jobs_data = serpapi_google_jobs(query=state["question"])
    return {**state, "jobs": jobs_data}


def node_fetch_web(state: GraphState) -> GraphState:
    web_data = tavily_web_search(
        query=f"Ideal student project ideas based on job market demand: {state['question']}"
    )
    return {**state, "web": web_data}


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

    g.add_node("retrieve_catalog", node_retrieve)
    g.add_node("fetch_jobs", node_fetch_jobs)
    g.add_node("fetch_web", node_fetch_web)
    g.add_node("synthesize_answer", node_synthesize)

    g.add_edge(START, "retrieve_catalog")
    g.add_edge("retrieve_catalog", "fetch_jobs")
    g.add_edge("fetch_jobs", "fetch_web")
    g.add_edge("fetch_web", "synthesize_answer")
    g.add_edge("synthesize_answer", END)

    return g.compile()
