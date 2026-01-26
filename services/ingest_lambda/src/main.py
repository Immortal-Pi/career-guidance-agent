import os
import json
import hashlib
from array import array
from typing import List, Dict, Any
import json, urllib.parse, traceback
import boto3

# --------- Clients ----------
s3 = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime")
s3vectors = boto3.client("s3vectors")

# --------- Env ----------
SOURCE_BUCKET = os.environ.get("SOURCE_BUCKET", "")
VECTOR_BUCKET_NAME = os.environ["VECTOR_BUCKET_NAME"]
VECTOR_INDEX_NAME = os.environ["VECTOR_INDEX_NAME"]

MANIFEST_BUCKET = os.environ.get("MANIFEST_BUCKET", SOURCE_BUCKET)
MANIFEST_PREFIX = os.environ.get("MANIFEST_PREFIX", "manifests/")

BEDROCK_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "amazon.titan-embed-text-v2:0")

CHUNK_MAX_CHARS = int(os.environ.get("CHUNK_MAX_CHARS", "3500"))
CHUNK_OVERLAP_CHARS = int(os.environ.get("CHUNK_OVERLAP_CHARS", "300"))
UPSERT_BATCH_SIZE = int(os.environ.get("UPSERT_BATCH_SIZE", "50"))


def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _manifest_key(doc_id: str) -> str:
    return f"{MANIFEST_PREFIX}{doc_id}.json"


def _read_text_from_s3(bucket: str, key: str) -> str:
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8", errors="ignore")


def _chunk_text(text: str, max_chars: int, overlap_chars: int) -> List[str]:
    """
    Simple char-based chunking that works well for markdown.
    Keeps overlap to preserve context across chunks.
    """
    text = text.replace("\r\n", "\n")
    chunks = []
    n = len(text)
    start = 0

    while start < n:
        end = min(n, start + max_chars)

        # Try not to cut mid-paragraph: backtrack to nearest newline if possible
        if end < n:
            back = text.rfind("\n", start, end)
            if back != -1 and back > start + int(max_chars * 0.6):
                end = back

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break

        start = max(0, end - overlap_chars)

    return chunks


def _embed_titan(text: str) -> List[float]:
    """
    Titan Text Embeddings v2 returns 1024-d vector.
    """
    payload = {"inputText": text}
    resp = bedrock.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json",
    )
    body = json.loads(resp["body"].read())
    emb = body["embedding"]  # per Titan embeddings response format
    # Force float32 (S3 Vectors expects float32 values)
    return array("f", emb).tolist()


def _load_manifest(doc_id: str) -> List[str]:
    """
    Manifest contains the vector keys previously written for this document.
    """
    key = _manifest_key(doc_id)
    try:
        obj = s3.get_object(Bucket=MANIFEST_BUCKET, Key=key)
        return json.loads(obj["Body"].read().decode("utf-8"))
    except s3.exceptions.NoSuchKey:
        return []
    except Exception:
        # If manifest is corrupted, treat as none (won't delete old vectors)
        return []


def _save_manifest(doc_id: str, vector_keys: List[str]) -> None:
    key = _manifest_key(doc_id)
    s3.put_object(
        Bucket=MANIFEST_BUCKET,
        Key=key,
        Body=json.dumps(vector_keys).encode("utf-8"),
        ContentType="application/json",
    )


def _delete_old_vectors(old_keys: List[str]) -> None:
    if not old_keys:
        return

    # Delete in batches (API accepts list of keys)
    BATCH = 500  # conservative
    for i in range(0, len(old_keys), BATCH):
        batch = old_keys[i : i + BATCH]
        s3vectors.delete_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            keys=batch,
        )


def _put_vectors(vectors: List[Dict[str, Any]]) -> None:
    """
    Put vectors in batches. put_vectors overwrites if key already exists.
    """
    for i in range(0, len(vectors), UPSERT_BATCH_SIZE):
        batch = vectors[i : i + UPSERT_BATCH_SIZE]
        s3vectors.put_vectors(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            vectors=batch,
        )

def _extract_bucket_key(event: dict):
    # S3 Event Notification (most likely your case)
    recs = event.get("Records") or []
    if recs:
        s3rec = recs[0].get("s3") or {}
        bucket = (s3rec.get("bucket") or {}).get("name")
        key = (s3rec.get("object") or {}).get("key")
        if key:
            key = urllib.parse.unquote_plus(key)
        return bucket, key

    # EventBridge S3 (fallback)
    d = event.get("detail") or {}
    bucket = (d.get("bucket") or {}).get("name")
    key = (d.get("object") or {}).get("key")
    if bucket and key:
        return bucket, key

    return None, None


def handler(event, context):
    try:
        print("EVENT:", json.dumps(event)[:4000])

        bucket, key = _extract_bucket_key(event)
        print("PARSED bucket/key:", bucket, key)

        if not bucket or not key:
            raise RuntimeError("Could not parse bucket/key from event")

        if not key.lower().endswith(".md"):
            print("SKIP: not md", key)
            return {"ok": True, "skipped": True, "reason": "not md"}

        # Add a single checkpoint so you know it reached here
        print("OK: will ingest", bucket, key)
        # EventBridge S3 event: bucket + object key live under event["detail"]
        detail = event.get("detail", {})
        bucket = detail.get("bucket", {}).get("name")
        key = detail.get("object", {}).get("key")

        if not bucket or not key:
            return {"ok": False, "reason": "Missing bucket/key in event", "event": event}

        # Optional: only process markdown files
        if not key.lower().endswith(".md"):
            return {"ok": True, "skipped": True, "reason": "Not .md", "key": key}

        # Read document
        text = _read_text_from_s3(bucket, key)
        if not text.strip():
            return {"ok": True, "skipped": True, "reason": "Empty file", "key": key}

        doc_id = _sha1(key)

        # Load old manifest & delete old vectors for this doc
        old_vector_keys = _load_manifest(doc_id)
        _delete_old_vectors(old_vector_keys)

        # Chunk
        chunks = _chunk_text(text, CHUNK_MAX_CHARS, CHUNK_OVERLAP_CHARS)

        # Embed + build vectors
        vectors = []
        new_vector_keys = []

        for idx, chunk in enumerate(chunks):
            emb = _embed_titan(chunk)
            vkey = f"{doc_id}:{idx}"
            new_vector_keys.append(vkey)

            vectors.append(
                {
                    "key": vkey,
                    "data": {"float32": emb},
                    "metadata": {
                        "s3_bucket": bucket,
                        "s3_key": key,
                        "doc_id": doc_id,
                        "chunk_index": idx,
                        "text": chunk[:1000],  # keep metadata small; store preview only
                    },
                }
            )

        # Write vectors
        _put_vectors(vectors)

        # Save manifest
        _save_manifest(doc_id, new_vector_keys)

        return {
            "ok": True,
            "bucket": bucket,
            "key": key,
            "doc_id": doc_id,
            "chunks": len(chunks),
            "vectors_written": len(vectors),
        }
    except Exception as e:
        print("ERROR:", str(e))
        print(traceback.format_exc())
        raise
