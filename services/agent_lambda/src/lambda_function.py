import json
import base64
import os
import boto3

# ---------- AWS clients ----------
bedrock_runtime = boto3.client("bedrock-runtime")
s3vectors = boto3.client("s3vectors")
s3 = boto3.client("s3")

# ---------- ENV ----------
EMBED_MODEL_ID = os.environ.get(
    "EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0"
)
CHAT_MODEL_ID = os.environ.get(
    "CHAT_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0"
)
S3V_INDEX_ARN = os.environ["S3V_INDEX_ARN"]

TOP_K = int(os.environ.get("TOP_K", "5"))


# ---------- helpers ----------
def embed_query(text: str) -> list[float]:
    resp = bedrock_runtime.invoke_model(
        modelId=EMBED_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text}),
    )
    return json.loads(resp["body"].read())["embedding"]


def query_s3_vectors(query_vec: list[float]) -> list[str]:
    resp = s3vectors.query_vectors(
        IndexArn=S3V_INDEX_ARN,
        QueryVector=query_vec,
        TopK=TOP_K,
    )

    chunks = []

    for v in resp.get("Vectors", []):
        md = v.get("Metadata", {})

        # Case 1: text stored directly in metadata
        if "text" in md:
            chunks.append(md["text"])
            continue

        # Case 2: pointer to S3 object
        if "bucket" in md and "key" in md:
            obj = s3.get_object(Bucket=md["bucket"], Key=md["key"])
            chunks.append(obj["Body"].read().decode("utf-8"))

    return chunks


def call_llm(question: str, context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    prompt = f"""
You are a helpful UTD Career Guiding Assistant.
Answer ONLY using the context below.
If the answer is not present, say you do not know.

Context:
{context}

Question:
{question}

Answer (concise):
"""

    resp = bedrock_runtime.invoke_model(
        modelId=CHAT_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 400,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }),
    )

    return json.loads(resp["body"].read())["content"][0]["text"]


# ---------- Lambda handler ----------
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

    if not question:
        return {
            "statusCode": 400,
            "headers": cors_headers(),
            "body": json.dumps({"answer": "No question provided"})
        }

    # ---- RAG inference ----
    query_vec = embed_query(question)
    chunks = query_s3_vectors(query_vec)
    answer = call_llm(question, chunks)

    return {
        "statusCode": 200,
        "headers": cors_headers(),
        "body": json.dumps({
            "answer": answer
        })
    }


def cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
    }
