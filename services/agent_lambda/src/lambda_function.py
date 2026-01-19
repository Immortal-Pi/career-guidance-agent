import json
import base64

def lambda_handler(event, context):
    question = ""

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

    # ---- Your agent logic goes here ----
    reply = f"I received your question: {question}"

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
        },
        "body": json.dumps({
            "answer": reply
        })
    }
