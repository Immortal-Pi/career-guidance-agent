import json
import base64
from graph import build_graph

graph = None

def lambda_handler(event, context):
    question = ""
    global graph
    if graph is None:
        graph=build_graph()
    # ---- Case 1: API Gateway invocation ----
    body = event.get("body")
    if body is not None:
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")

        try:
            payload = json.loads(body) if isinstance(body, str) else body
        except Exception:
            payload = {}

        question = payload.get("question", "")

    # ---- Case 2: Lambda console test ----
    if not question:
        question = (event or {}).get("question", "")

    if not question:
        return _resp(400, {"answer": "No question provided"})

    # Run LangGraph workflow
    result = graph.invoke({"question": question})

    return _resp(200, {"answer": result.get("answer", "")})


def _resp(status, obj):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(obj),
    }
