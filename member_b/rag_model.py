import os
import json
import time
import numpy as np
import faiss
from dotenv import load_dotenv
from google import genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

# ── Load API key ──────────────────────────────────────────────────────────────
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ── 1. Load extracted signals from T3 ────────────────────────────────────────
print("Loading extracted signals...")
with open('test_extraction.json', 'r') as f:
    raw_signals = json.load(f)

signals = [s for s in raw_signals if s.get('status') == 'success']
print(f"Loaded {len(signals)} signals\n")

# ── 2. Convert each signal to a text chunk ───────────────────────────────────
def signal_to_text(signal: dict) -> str:
    return (
        f"Headline: {signal.get('headline', 'N/A')}. "
        f"Disruption type: {signal.get('disruption_category', 'N/A')}. "
        f"Affected industry: {signal.get('affected_industry', 'N/A')}. "
        f"Region: {signal.get('region', 'N/A')}. "
        f"Severity: {signal.get('severity_score', 0)}/5. "
        f"Propagation risk: {signal.get('propagation_risk', 'N/A')}. "
        f"Signal type: {signal.get('signal_type', 'N/A')}."
    )

signal_texts = [signal_to_text(s) for s in signals]

print("Signal texts prepared:")
for i, text in enumerate(signal_texts):
    print(f"  [{i+1}] {text[:80]}...")
print()

# ── 3. Create TF-IDF embeddings ───────────────────────────────────────────────
print("Creating TF-IDF embeddings (no PyTorch needed)...")
vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=512)
embeddings = vectorizer.fit_transform(signal_texts).toarray().astype(np.float32)
embeddings = normalize(embeddings)
print(f"Embeddings matrix shape: {embeddings.shape}\n")

# ── 4. Build FAISS index ──────────────────────────────────────────────────────
print("Building FAISS index...")
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)
print(f"FAISS index built with {index.ntotal} vectors (dimension={dimension})\n")

# ── 5. RAG query function ─────────────────────────────────────────────────────
def rag_query(question: str, top_k: int = 3) -> dict:
    question_vec = vectorizer.transform([question]).toarray().astype(np.float32)
    question_vec = normalize(question_vec)

    scores, indices = index.search(question_vec, top_k)

    retrieved_signals = []
    for idx, score in zip(indices[0], scores[0]):
        if idx < len(signal_texts):
            retrieved_signals.append({
                'text': signal_texts[idx],
                'signal': signals[idx],
                'score': float(score)
            })

    context = "\n\n".join([
        f"Signal {i+1} (relevance: {r['score']:.3f}): {r['text']}"
        for i, r in enumerate(retrieved_signals)
    ])

    prompt = f"""You are a supply chain risk analyst. Based on the following recent news signals,
answer the question with a disruption probability and explanation.

Recent supply chain signals:
{context}

Question: {question}

Respond in this exact JSON format with no markdown:
{{
  "disruption_probability": <float between 0.0 and 1.0>,
  "risk_level": "<low|medium|high|critical>",
  "affected_industries": [<list of industries at risk>],
  "affected_regions": [<list of regions at risk>],
  "reasoning": "<2-3 sentence explanation>",
  "recommended_action": "<1 sentence recommendation>"
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    result['retrieved_signals'] = [r['text'] for r in retrieved_signals]
    return result

# ── 6. Run test queries ───────────────────────────────────────────────────────
print("=" * 60)
print("RAG MODEL TEST QUERIES")
print("=" * 60)

test_questions = [
    "Will there be a semiconductor supply chain disruption in the next 14 days?",
    "Is there a risk of port congestion affecting automotive production?",
    "What is the likelihood of a global logistics disruption in the next 3 weeks?"
]

for question in test_questions:
    print(f"\nQuestion: {question}")
    print("-" * 50)
    try:
        result = rag_query(question)
        print(f"Disruption Probability : {result['disruption_probability']:.0%}")
        print(f"Risk Level             : {result['risk_level'].upper()}")
        print(f"Affected Industries    : {', '.join(result['affected_industries'])}")
        print(f"Affected Regions       : {', '.join(result['affected_regions'])}")
        print(f"Reasoning              : {result['reasoning']}")
        print(f"Recommended Action     : {result['recommended_action']}")
        print(f"\nTop signals retrieved:")
        for i, sig in enumerate(result['retrieved_signals']):
            print(f"  [{i+1}] {sig[:90]}...")
    except Exception as e:
        print(f"Error: {e}")
    time.sleep(13)

print("\n" + "=" * 60)
print("T5 RAG model complete!")
print("=" * 60)
