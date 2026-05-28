"""
B7 — Email subscription + stats endpoints

POST /api/v1/subscribe  — saves email + industry + region to CSV, sends welcome email via Brevo
GET  /api/v1/stats      — returns total articles, alerts this month, subscriber count
"""

import os
import csv
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
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


def _load_subscribers():
    _ensure_subscribers_csv()
    try:
        df = pd.read_csv(SUBSCRIBERS_CSV)
        return df.to_dict(orient="records")
    except Exception:
        return []


def _email_exists(email):
    subs = _load_subscribers()
    return any(s.get("email", "").lower() == email.lower() for s in subs)


def _save_subscriber(email, industry, region):
    _ensure_subscribers_csv()
    with open(SUBSCRIBERS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SUBSCRIBER_FIELDS)
        writer.writerow({
            "email":         email,
            "industry":      industry,
            "region":        region,
            "subscribed_at": datetime.now(timezone.utc).isoformat(),
        })


def _send_welcome_email_brevo(email, industry, region):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept":       "application/json",
        "content-type": "application/json",
        "api-key":      settings.BREVO_API_KEY,
    }
    payload = {
        "sender": {
            "name":  "NewsShield",
            "email": "janhavi200515@gmail.com",
        },
        "to": [{"email": email}],
        "subject": "Welcome to NewsShield — Your Supply Chain Risk Monitor",
        "htmlContent": f"""
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
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code not in (200, 201):
        raise Exception(f"Brevo API error {response.status_code}: {response.text}")


def _get_stats():
    total_articles = 0
    try:
        df = pd.read_csv(FEATURE_MATRIX)
        total_articles = int(df["article_count"].sum())
    except Exception:
        pass

    alerts_this_month = 0
    try:
        with open(EXTRACTIONS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
        alerts_this_month = len([r for r in data if r.get("status") == "success"])
    except Exception:
        pass

    subscriber_count = len(_load_subscribers())

    regions_monitored = 0
    try:
        df = pd.read_csv(FEATURE_MATRIX)
        regions_monitored = int(df["region"].nunique())
    except Exception:
        pass

    return {
        "total_articles_analysed":     total_articles,
        "alerts_generated_this_month": alerts_this_month,
        "subscriber_count":            subscriber_count,
        "regions_monitored":           regions_monitored,
        "data_sources":                ["GDELT", "GSCPI", "LLM Extraction"],
        "last_updated":                datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


# ── Schemas ───────────────────────────────────────────────────────────────────

class SubscribeRequest(BaseModel):
    email:    EmailStr = Field(..., description="Subscriber email address")
    industry: str      = Field(default="all",    description="Industry of interest")
    region:   str      = Field(default="global", description="Region of interest")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/subscribe", summary="Subscribe to NewsShield alerts")
def subscribe(body: SubscribeRequest):
    if _email_exists(body.email):
        raise HTTPException(status_code=409, detail="Email already subscribed.")

    try:
        _save_subscriber(body.email, body.industry, body.region)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save subscriber: {e}")

    email_sent  = False
    email_error = None

    if settings.BREVO_API_KEY:
        try:
            _send_welcome_email_brevo(body.email, body.industry, body.region)
            email_sent = True
        except Exception as e:
            email_error = str(e)
    else:
        email_error = "BREVO_API_KEY not configured"

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
    return _get_stats()