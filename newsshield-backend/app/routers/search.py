from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import json
import os
from datetime import datetime, timedelta

router = APIRouter()

JSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "gdelt_output", "final_extraction_100.json"
)

VALID_SIGNAL_TYPES = {"trigger", "precursor", "amplifier", "propagation", "response"}
VALID_INDUSTRIES   = {"semiconductor", "automotive", "logistics", "energy", "pharmaceutical", "agriculture"}


def _load_articles() -> list[dict]:
    path = os.path.abspath(JSON_PATH)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Extraction JSON not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    successful = [r for r in data if r.get("status") == "success"]

    # Assign simulated dates spread over last 90 days
    base = datetime.utcnow()
    total = len(successful)
    for i, rec in enumerate(successful):
        offset = int((i / max(total - 1, 1)) * 89)
        rec["article_date"] = (base - timedelta(days=offset)).strftime("%Y-%m-%d")
        rec["risk_score"] = round((float(rec.get("severity_score", 3)) - 1) / 4, 4)
        rec["warning_level"] = (
            "critical" if rec["risk_score"] >= 0.75 else
            "high"     if rec["risk_score"] >= 0.50 else
            "medium"   if rec["risk_score"] >= 0.25 else
            "low"
        )

    return successful


@router.get("/search", summary="Search extracted news articles")
def search_articles(
    query: Optional[str] = Query(
        None,
        description="Keyword search over headline, region, industry (case-insensitive)",
    ),
    signal_type: Optional[str] = Query(
        None,
        description=f"Filter by signal type: {', '.join(sorted(VALID_SIGNAL_TYPES))}",
    ),
    industry: Optional[str] = Query(
        None,
        description=f"Filter by industry: {', '.join(sorted(VALID_INDUSTRIES))}",
    ),
    region: Optional[str] = Query(
        None,
        description="Filter by region e.g. Taiwan, China, Europe",
    ),
    disruption_category: Optional[str] = Query(
        None,
        description="Filter by disruption category e.g. geopolitical, labor, port",
    ),
    min_severity: float = Query(
        default=0.0, ge=0.0, le=1.0,
        description="Minimum normalised severity score (0–1)",
    ),
    propagation_risk: Optional[str] = Query(
        None,
        description="Filter by propagation risk: local, regional, global",
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=50, description="Results per page (max 50)"),
):
    """
    Keyword + multi-filter search over the extracted article dataset.
    Powers the News Explorer search bar and filter chips on Page 4.

    Filters applied in order:
      1. query      — matches headline, region, affected_industry (OR logic)
      2. signal_type
      3. industry
      4. region
      5. disruption_category
      6. min_severity
      7. propagation_risk

    Returns paginated article cards with all extracted fields.
    """
    try:
        articles = _load_articles()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    results = articles

    # ── 1. Keyword search (headline + region + industry) ──────────────────────
    if query:
        q = query.strip().lower()
        results = [
            r for r in results
            if q in r.get("headline", "").lower()
            or q in r.get("region", "").lower()
            or q in r.get("affected_industry", "").lower()
            or q in r.get("disruption_category", "").lower()
        ]

    # ── 2. Signal type filter ─────────────────────────────────────────────────
    if signal_type:
        st = signal_type.strip().lower()
        results = [
            r for r in results
            if st in r.get("signal_type", "").lower()
        ]

    # ── 3. Industry filter ────────────────────────────────────────────────────
    if industry:
        ind = industry.strip().lower()
        results = [
            r for r in results
            if ind in r.get("affected_industry", "").lower()
        ]

    # ── 4. Region filter ──────────────────────────────────────────────────────
    if region:
        reg = region.strip().lower()
        results = [
            r for r in results
            if reg in r.get("region", "").lower()
        ]

    # ── 5. Disruption category filter ────────────────────────────────────────
    if disruption_category:
        dc = disruption_category.strip().lower()
        results = [
            r for r in results
            if dc in r.get("disruption_category", "").lower()
        ]

    # ── 6. Min severity filter ────────────────────────────────────────────────
    if min_severity > 0:
        results = [r for r in results if r["risk_score"] >= min_severity]

    # ── 7. Propagation risk filter ────────────────────────────────────────────
    if propagation_risk:
        pr = propagation_risk.strip().lower()
        results = [
            r for r in results
            if pr in r.get("propagation_risk", "").lower()
        ]

    # ── Sort by severity descending ───────────────────────────────────────────
    results = sorted(results, key=lambda r: r.get("severity_score", 0), reverse=True)

    # ── Pagination ────────────────────────────────────────────────────────────
    total   = len(results)
    start   = (page - 1) * page_size
    end     = start + page_size
    page_results = results[start:end]

    if not page_results and total == 0:
        raise HTTPException(status_code=404, detail="No articles match the given filters.")

    # ── Build response cards ──────────────────────────────────────────────────
    cards = [
        {
            "headline":            r.get("headline", ""),
            "affected_industry":   r.get("affected_industry", "unknown"),
            "region":              r.get("region", "unknown"),
            "disruption_category": r.get("disruption_category", "unknown"),
            "signal_type":         r.get("signal_type", "unknown"),
            "severity_score":      r.get("severity_score", 0),
            "risk_score":          r["risk_score"],
            "warning_level":       r["warning_level"],
            "propagation_risk":    r.get("propagation_risk", "unknown"),
            "article_date":        r["article_date"],
        }
        for r in page_results
    ]

    return {
        "meta": {
            "total_results": total,
            "page":          page,
            "page_size":     page_size,
            "total_pages":   max(1, -(-total // page_size)),  # ceiling division
            "filters_applied": {
                "query":                query,
                "signal_type":          signal_type,
                "industry":             industry,
                "region":               region,
                "disruption_category":  disruption_category,
                "min_severity":         min_severity,
                "propagation_risk":     propagation_risk,
            },
        },
        "results": cards,
    }