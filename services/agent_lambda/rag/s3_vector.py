import os
import json
import boto3

bedrock_runtime = boto3.client("bedrock-runtime")
s3vectors = boto3.client("s3vectors")
s3 = boto3.client("s3")

S3V_INDEX_ARN = os.environ["S3V_INDEX_ARN"]

EMBED_MODEL_ID = os.environ.get("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
CHAT_MODEL_ID = os.environ.get("CHAT_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")

TOP_K = int(os.environ.get("TOP_K", "6"))


def _embed_query(text: str) -> list[float]:
    resp = bedrock_runtime.invoke_model(
        modelId=EMBED_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputText": text}),
    )
    return json.loads(resp["body"].read())["embedding"]


def retrieve_utd_context(question: str) -> str:
    qvec = _embed_query(question)

    resp = s3vectors.query_vectors(
        indexArn=S3V_INDEX_ARN,
        topK=TOP_K,
        queryVector={"float32": qvec},
        returnMetadata=True,
        returnDistance=True,
    )

    vectors = resp.get("vectors", [])
    chunks = []

    for v in vectors:
        md = v.get("metadata") or v.get("Metadata") or {}

        # text stored directly
        txt = md.get("text")
        if isinstance(txt, str) and txt.strip():
            chunks.append(txt.strip())
            continue

        # pointer stored
        b = md.get("bucket") or md.get("source_bucket")
        k = md.get("key") or md.get("source_key")
        if b and k:
            obj = s3.get_object(Bucket=b, Key=k)
            raw = obj["Body"].read().decode("utf-8", errors="ignore")
            chunks.append(raw)

    return "\n\n---\n\n".join(chunks[:TOP_K])



def bedrock_synthesize_answer(question: str, utd_context: str, jobs: dict, web: dict) -> str:
    # Keep prompt short + structured (helps reduce hallucinations)
    prompt = f"""
You are a UTD Career Guiding Assistant.
You have 3 data sources:
(1) UTD course catalog context (trusted)
(2) Job listings snapshot (jobs)
(3) Web search summary (web)

Task:
- Answer the user's question.
- Recommend 2-4 ideal project ideas for a student based on job market signals.
- Tie projects to relevant UTD coursework from the catalog context.
- If data is missing, be explicit.

UTD Catalog Context:
{utd_context}

Job Listings (JSON):
{json.dumps(jobs)[:6000]}

Web Search (JSON):
{json.dumps(web)[:6000]}

User Question:
{question}

Return:
- A concise answer
- "Project Ideas" (bullets)
- "Suggested UTD Courses" (bullets)
"""

    resp = bedrock_runtime.invoke_model(
        modelId=CHAT_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 700,
            "temperature": 0.2,
            "messages": [{"role": "user", "content": prompt}],
        }),
    )

    out = json.loads(resp["body"].read())
    return out["content"][0]["text"]
