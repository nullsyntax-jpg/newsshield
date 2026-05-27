"""
B6 — Ask the AI endpoint (RAG)
POST /api/v1/ask

Pipeline:
  1. Load extracted articles from final_extraction_100.json
  2. Build FAISS index using sentence-transformers embeddings (cached in memory)
  3. Retrieve top-k relevant articles for the question
  4. Feed context + question to Groq LLaMA 3
  5. Stream response word by word using FastAPI StreamingResponse
"""

import os
import json
import asyncio
from functools import lru_cache
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from groq import Groq

from app.core.config import settings

router = APIRouter()

# ── Paths ─────────────────────────────────────────────────────────────────────
JSON_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "gdelt_output", "final_extraction_100.json"
))

# ── Models (loaded once, cached in memory) ────────────────────────────────────
_embedder: SentenceTransformer | None = None
_faiss_index: faiss.IndexFlatL2 | None = None
_articles: list[dict] = []


def _load_articles() -> list[dict]:
    if not os.path.exists(JSON_PATH):
        raise FileNotFoundError(f"Extraction JSON not found at {JSON_PATH}")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [r for r in data if r.get("status") == "success"]


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _build_index() -> tuple[faiss.IndexFlatL2, list[dict]]:
    global _faiss_index, _articles
    if _faiss_index is not None:
        return _faiss_index, _articles

    articles = _load_articles()
    embedder = _get_embedder()

    # Build text to embed: headline + region + industry + category
    texts = [
        f"{a.get('headline', '')} | {a.get('region', '')} | "
        f"{a.get('affected_industry', '')} | {a.get('disruption_category', '')} | "
        f"{a.get('signal_type', '')}"
        for a in articles
    ]

    embeddings = embedder.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    embeddings = embeddings.astype("float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    _faiss_index = index
    _articles = articles
    return index, articles


def _retrieve(question: str, top_k: int = 5) -> list[dict]:
    index, articles = _build_index()
    embedder = _get_embedder()

    q_embedding = embedder.encode([question], convert_to_numpy=True).astype("float32")
    distances, indices = index.search(q_embedding, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < len(articles):
            article = articles[idx].copy()
            article["_relevance_score"] = round(float(1 / (1 + dist)), 4)
            results.append(article)
    return results


def _build_prompt(question: str, sources: list[dict]) -> str:
    context_lines = []
    for i, s in enumerate(sources, 1):
        context_lines.append(
            f"[{i}] Headline: {s.get('headline', 'N/A')}\n"
            f"    Industry: {s.get('affected_industry', 'N/A')} | "
            f"Region: {s.get('region', 'N/A')} | "
            f"Category: {s.get('disruption_category', 'N/A')} | "
            f"Signal: {s.get('signal_type', 'N/A')} | "
            f"Severity: {s.get('severity_score', 'N/A')}/5 | "
            f"Propagation: {s.get('propagation_risk', 'N/A')}"
        )
    context = "\n".join(context_lines)

    return f"""You are NewsShield, an expert supply chain risk analyst AI.
Answer the user's question using ONLY the supply chain disruption signals provided below.
Be concise, factual, and cite signal numbers like [1], [2] where relevant.
If the context doesn't fully answer the question, say so honestly.

SUPPLY CHAIN SIGNALS:
{context}

USER QUESTION: {question}

ANSWER:"""


async def _stream_groq(prompt: str) -> AsyncGenerator[str, None]:
    client = Groq(api_key=settings.GROQ_API_KEY)

    stream = client.chat.completions.create(
       model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        max_tokens=512,
        temperature=0.3,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
            await asyncio.sleep(0)  # yield control to event loop


# ── Request / Response schemas ────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Natural language question about supply chain risks",
        examples=["What are the biggest semiconductor risks right now?"],
    )
    top_k: int = Field(
        default=5, ge=1, le=10,
        description="Number of source articles to retrieve from FAISS",
    )
    stream: bool = Field(
        default=True,
        description="Stream the response word by word (true) or return full response (false)",
    )


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/ask", summary="Ask the AI (RAG) — supply chain risk Q&A")
async def ask_newsshield(body: AskRequest):
    """
    Accepts a natural language question, retrieves relevant supply chain signals
    from FAISS, and streams an LLM-generated answer using Groq LLaMA 3.

    Powers the 'Ask NewsShield' chat box on Page 4.
    """
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY not configured. Add it to your .env file.",
        )

    # ── Retrieve relevant articles ────────────────────────────────────────────
    try:
        sources = _retrieve(body.question, top_k=body.top_k)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not sources:
        raise HTTPException(status_code=404, detail="No relevant signals found.")

    prompt = _build_prompt(body.question, sources)

    # ── Stream response ───────────────────────────────────────────────────────
    if body.stream:
        async def event_stream():
            # First send source metadata as JSON line
            meta = {
                "type": "sources",
                "sources": [
                    {
                        "headline":            s.get("headline", ""),
                        "industry":            s.get("affected_industry", ""),
                        "region":              s.get("region", ""),
                        "disruption_category": s.get("disruption_category", ""),
                        "signal_type":         s.get("signal_type", ""),
                        "severity_score":      s.get("severity_score", 0),
                        "propagation_risk":    s.get("propagation_risk", ""),
                        "relevance_score":     s.get("_relevance_score", 0),
                    }
                    for s in sources
                ],
            }
            yield json.dumps(meta) + "\n"

            # Then stream answer tokens
            async for token in _stream_groq(prompt):
                yield json.dumps({"type": "token", "text": token}) + "\n"

            yield json.dumps({"type": "done"}) + "\n"

        return StreamingResponse(event_stream(), media_type="application/x-ndjson")

    # ── Non-streaming fallback ────────────────────────────────────────────────
    else:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.3,
        )
        answer = response.choices[0].message.content

        return {
            "question": body.question,
            "answer": answer,
            "confidence": round(float(np.mean([s["_relevance_score"] for s in sources])), 4),
            "sources": [
                {
                    "headline":            s.get("headline", ""),
                    "industry":            s.get("affected_industry", ""),
                    "region":              s.get("region", ""),
                    "disruption_category": s.get("disruption_category", ""),
                    "signal_type":         s.get("signal_type", ""),
                    "severity_score":      s.get("severity_score", 0),
                    "propagation_risk":    s.get("propagation_risk", ""),
                    "relevance_score":     s.get("_relevance_score", 0),
                }
                for s in sources
            ],
        }
