"""
B7 — Email subscription + stats endpoints

POST /api/v1/subscribe  — saves email + industry + region to CSV, sends welcome email
GET  /api/v1/stats      — returns total articles, alerts this month, subscriber count
"""

import os
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import resend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, EmailStr

from app.core.config import settings

router = APIRouter()

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parents[3]
SUBSCRIBERS_CSV  = BASE / "gdelt_output" / "subscribers.csv"
FEATURE_MATRIX   = BASE / "gdelt_output" / "feature_matrix.csv"
EXTRACTIONS_JSON = BASE / "gdelt_output" / "final_extraction_100.json"

SUBSCRIBER_FIELDS = ["email", "industry", "region", "subscribed_at"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ensure_subscribers_csv():
    if not SUBSCRIBERS_CSV.exists():
        with open(SUBSCRIBERS_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SUBSCRIBER_FIELDS)
            writer.writeheader()


def _load_subscribers() -> list[dict]:
    _ensure_subscribers_csv()
    try:
        df = pd.read_csv(SUBSCRIBERS_CSV)
        return df.to_dict(orient="records")
    except Exception:
        return []


def _email_exists(email: str) -> bool:
    subs = _load_subscribers()
    return any(s.get("email", "").lower() == email.lower() for s in subs)


def _save_subscriber(email: str, industry: str, region: str):
    _ensure_subscribers_csv()
    with open(SUBSCRIBERS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUBSCRIBER_FIELDS)
        writer.writerow({
            "email":         email,
            "industry":      industry,
            "region":        region,
            "subscribed_at": datetime.now(timezone.utc).isoformat(),
        })


def _send_welcome_email(email: str, industry: str, region: str):
    resend.api_key = settings.RESEND_API_KEY
    resend.Emails.send({
        "from":    "NewsShield <onboarding@resend.dev>",
        "to":      [email],
        "subject": "Welcome to NewsShield — Your Supply Chain Risk Monitor",
        "html":    f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: auto;">
          <h2 style="color: #1a1a2e;">Welcome to NewsShield 🛡️</h2>
          <p>Hi there,</p>
          <p>You're now subscribed to <strong>NewsShield</strong> — real-time supply chain
          disruption intelligence powered by GDELT news data and AI.</p>
          <p><strong>Your preferences:</strong><br/>
          Industry: <strong>{industry or 'All'}</strong><br/>
          Region: <strong>{region or 'Global'}</strong></p>
          <p>You'll receive alerts when supply chain risks matching your profile are detected.</p>
          <hr/>
          <p style="color: #666; font-size: 12px;">
            NewsShield · Powered by GDELT + AI<br/>
            <a href="https://newsshield.onrender.com">newsshield.onrender.com</a>
          </p>
        </div>
        """,
    })


def _get_stats() -> dict:
    # ── Total articles analysed ───────────────────────────────────────────────
    total_articles = 0
    try:
        df = pd.read_csv(FEATURE_MATRIX)
        total_articles = int(df["article_count"].sum())
    except Exception:
        pass

    # ── Alerts generated this month ───────────────────────────────────────────
    alerts_this_month = 0
    try:
        with open(EXTRACTIONS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        alerts_this_month = len([r for r in data if r.get("status") == "success"])
    except Exception:
        pass

    # ── Subscriber count ──────────────────────────────────────────────────────
    subscriber_count = len(_load_subscribers())

    # ── Regions monitored ─────────────────────────────────────────────────────
    regions_monitored = 0
    try:
        df = pd.read_csv(FEATURE_MATRIX)
        regions_monitored = int(df["region"].nunique())
    except Exception:
        pass

    return {
        "total_articles_analysed": total_articles,
        "alerts_generated_this_month": alerts_this_month,
        "subscriber_count": subscriber_count,
        "regions_monitored": regions_monitored,
        "data_sources": ["GDELT", "GSCPI", "LLM Extraction"],
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


# ── Schemas ───────────────────────────────────────────────────────────────────

class SubscribeRequest(BaseModel):
    email: EmailStr = Field(..., description="Subscriber email address")
    industry: str = Field(
        default="all",
        description="Industry of interest e.g. semiconductor, logistics, automotive",
    )
    region: str = Field(
        default="global",
        description="Region of interest e.g. Asia, Europe, Middle_East",
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/subscribe", summary="Subscribe to NewsShield alerts")
def subscribe(body: SubscribeRequest):
    """
    Saves email + preferences to subscribers CSV and sends a welcome email
    via Resend. Powers the subscription form on the dashboard.
    """
    if _email_exists(body.email):
        raise HTTPException(status_code=409, detail="Email already subscribed.")

    try:
        _save_subscriber(body.email, body.industry, body.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save subscriber: {e}")

    email_sent = True
    email_error = None
    if settings.RESEND_API_KEY:
        try:
            _send_welcome_email(body.email, body.industry, body.region)
        except Exception as e:
            email_sent = False
            email_error = str(e)
    else:
        email_sent = False
        email_error = "RESEND_API_KEY not configured"

    return {
        "success":     True,
        "message":     f"Successfully subscribed {body.email}",
        "email_sent":  email_sent,
        "email_error": email_error,
        "preferences": {
            "industry": body.industry,
            "region":   body.region,
        },
    }


@router.get("/stats", summary="Platform engagement stats")
def get_stats():
    """
    Returns total articles analysed, alerts generated this month,
    subscriber count, and regions monitored.
    Powers the engagement stats on Page 5.
    """
    return _get_stats()