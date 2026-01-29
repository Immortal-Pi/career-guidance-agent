from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END

from rag.s3_vector import retrieve_utd_context, bedrock_synthesize_answer
from tools.serpapi_jobs import serpapi_google_jobs
from tools.tavily_search import tavily_web_search

import os
import json
import re
import boto3

bedrock_runtime = boto3.client("bedrock-runtime")
CHAT_MODEL_ID = os.environ.get("CHAT_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")


class GraphState(TypedDict):
    question: str
    utd_context: NotRequired[str]
    jobs_plan: NotRequired[dict]     # <-- NEW
    jobs: NotRequired[dict]
    web: NotRequired[dict]
    answer: NotRequired[str]


def _extract_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return {}
    return json.loads(m.group(0))


def node_retrieve(state: GraphState) -> GraphState:
    ctx = retrieve_utd_context(state["question"])
    return {**state, "utd_context": ctx}


def node_plan_jobs(state: GraphState) -> GraphState:
    """
    Convert the user question into a SHORT Google Jobs query + filters.
    """
    prompt = f"""
You are a job-search query planner for Google Jobs.

Return ONLY valid JSON:
{{
  "location": "Dallas, TX",
  "query": "SHORT query string",
  "num_results": 8,
  "fallback_queries": ["...", "...", "..."]
}}

Rules:
- The query must be job titles + a few skills, NOT the user's full sentence.
- Use OR for synonyms.
- If user is a student / internship, include "intern" or "internship".
- Keep query <= 120 chars.

User question:
{state["question"]}
"""

    resp = bedrock_runtime.invoke_model(
        modelId=CHAT_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 250,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}],
        }),
    )
    out = json.loads(resp["body"].read())
    txt = out["content"][0]["text"]

    plan = _extract_json(txt) or {}
    plan.setdefault("location", "Dallas, TX")
    plan.setdefault("num_results", 8)
    plan.setdefault("fallback_queries", [
        "AI Engineer OR Machine Learning Engineer",
        "MLOps Engineer OR Machine Learning Platform",
        "LLM Engineer OR NLP Engineer",
    ])
    if not plan.get("query"):
        plan["query"] = "AI Engineer OR Machine Learning Engineer internship"

    print("jobs_plan:", plan)
    return {**state, "jobs_plan": plan}


def node_fetch_jobs(state: GraphState) -> GraphState:
    plan = state.get("jobs_plan") or {}
    q = plan.get("query", "AI Engineer OR Machine Learning Engineer")
    location = plan.get("location", "Dallas, TX")
    num_results = int(plan.get("num_results", 8))

    jobs_data = serpapi_google_jobs(query=q, location=location, num_results=num_results)

    # fallback if empty
    if not (jobs_data.get("jobs") or []):
        for fq in plan.get("fallback_queries", []):
            jobs_data = serpapi_google_jobs(query=fq, location=location, num_results=num_results)
            if jobs_data.get("jobs"):
                break

    print("Job Query Used:", jobs_data.get("query"), "| Jobs found:", len(jobs_data.get("jobs") or []))
    return {**state, "jobs": jobs_data}


def node_fetch_web(state: GraphState) -> GraphState:
    web_data = tavily_web_search(
        query=f"Ideal student project ideas based on job market demand: {state['question']}"
    )
    return {**state, "web": web_data}


def node_synthesize(state: GraphState) -> GraphState:
    jobs_payload = state.get("jobs", {}) or {}
    jobs_list = jobs_payload.get("jobs") or []

    print("jobs in state:", type(jobs_payload), "jobs_count:", len(jobs_list))

    answer = bedrock_synthesize_answer(
        question=state["question"],
        utd_context=state.get("utd_context", ""),
        jobs=jobs_payload,
        web=state.get("web", {}),
    )
    return {**state, "answer": answer}


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("retrieve_catalog", node_retrieve)
    g.add_node("plan_jobs", node_plan_jobs)         # <-- NEW
    g.add_node("fetch_jobs", node_fetch_jobs)
    g.add_node("fetch_web", node_fetch_web)
    g.add_node("synthesize_answer", node_synthesize)

    g.add_edge(START, "retrieve_catalog")
    g.add_edge("retrieve_catalog", "plan_jobs")     # <-- NEW
    g.add_edge("plan_jobs", "fetch_jobs")           # <-- NEW
    g.add_edge("fetch_jobs", "fetch_web")
    g.add_edge("fetch_web", "synthesize_answer")
    g.add_edge("synthesize_answer", END)

    return g.compile()

# from typing_extensions import TypedDict, NotRequired
# from langgraph.graph import StateGraph, START, END

# from rag.s3_vector import retrieve_utd_context, bedrock_synthesize_answer
# from tools.serpapi_jobs import serpapi_google_jobs
# from tools.tavily_search import tavily_web_search


# class GraphState(TypedDict):
#     question: str
#     utd_context: NotRequired[str]
#     jobs: NotRequired[dict]
#     web: NotRequired[dict]
#     answer: NotRequired[str]


# def node_retrieve(state: GraphState) -> GraphState:
#     ctx = retrieve_utd_context(state["question"])
#     return {**state, "utd_context": ctx}


# def node_fetch_jobs(state: GraphState) -> GraphState:
#     jobs_data = serpapi_google_jobs(query=state["question"])
#     print(f'Job Data: {jobs_data}')
#     return {**state, "jobs": jobs_data}


# def node_fetch_web(state: GraphState) -> GraphState:
#     web_data = tavily_web_search(
#         query=f"Ideal student project ideas based on job market demand: {state['question']}"
#     )
#     return {**state, "web": web_data}


# def node_synthesize(state: GraphState) -> GraphState:
#     print("jobs in state:", type(state.get("jobs")), "len:", len(state.get("jobs") or []))
#     answer = bedrock_synthesize_answer(
#         question=state["question"],
#         utd_context=state.get("utd_context", ""),
#         jobs=state.get("jobs", {}),
#         web=state.get("web", {}),
#     )
#     return {**state, "answer": answer}


# def build_graph():
#     g = StateGraph(GraphState)

#     g.add_node("retrieve_catalog", node_retrieve)
#     g.add_node("fetch_jobs", node_fetch_jobs)
#     g.add_node("fetch_web", node_fetch_web)
#     g.add_node("synthesize_answer", node_synthesize)

#     g.add_edge(START, "retrieve_catalog")
#     g.add_edge("retrieve_catalog", "fetch_jobs")
#     g.add_edge("fetch_jobs", "fetch_web")
#     g.add_edge("fetch_web", "synthesize_answer")
#     g.add_edge("synthesize_answer", END)

#     return g.compile()
