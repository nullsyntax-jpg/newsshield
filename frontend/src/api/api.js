// NewsShield API client
// Base URL: set VITE_API_URL in Vercel environment variables
// to https://newsshield.onrender.com

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API  = `${BASE}/api/v1`

// ── B1: Risk Heatmap ─────────────────────────────────────────────────────────
// GET /api/v1/risk/heatmap
// Returns risk scores by region
export async function getRiskHeatmap() {
  const res = await fetch(`${API}/risk/heatmap`)
  return res.json()
}

// GET /api/v1/risk?region=Middle_East&horizon=21
// Returns XGBoost risk prediction for a region
export async function getRisk(industry = 'Semiconductor', region = null, horizon = 21) {
  const industryRegionMap = {
    'Semiconductor': 'East_Asia',
    'Automotive':    'Europe',
    'Logistics':     'Middle_East',
    'Food':          'Africa',
    'Pharmaceutical':'South_Asia',
    'Energy':        'Middle_East',
  }
  const r = region || industryRegionMap[industry] || 'Middle_East'
  const res = await fetch(`${API}/risk?region=${r}&horizon=${horizon}`)
  const data = await res.json()
  return {
    risk_score:    Math.round((data.risk_score || 0) * 100),
    trend:         data.warning_level === 'critical' ? 'rising' : 'stable',
    signals:       data.features_used || 14,
    warning_level: data.warning_level,
    region:        data.region,
  }
}

// ── B1: Forecast ──────────────────────────────────────────────────────────────
// GET /api/v1/forecast
// Returns 21-day forecast
export async function getForecast(region = 'Middle_East', horizon = 21) {
  const res = await fetch(`${API}/forecast?region=${region}&horizon=${horizon}`)
  return res.json()
}

// ── B3: Alerts ────────────────────────────────────────────────────────────────
// GET /api/v1/alerts?days=7&region=...&risk_type=...
// Returns top 5 risk alerts
export async function getAlerts(days = 7, region = null, riskType = null) {
  let url = `${API}/alerts?days=${days}`
  if (region)   url += `&region=${region}`
  if (riskType) url += `&risk_type=${riskType}`
  const res  = await fetch(url)
  const data = await res.json()
  // Normalize alert fields
  return {
    alerts: (data.alerts || []).map(a => ({
      id:       a.rank,
      severity: a.risk_score,
      title:    a.headline,
      industry: a.industry,
      region:   a.region,
      risk_type: a.risk_type,
      detected_date: a.detected_date,
      lead_days: a.lead_days,
    }))
  }
}

// ── B4: History ───────────────────────────────────────────────────────────────
// GET /api/v1/history?region=...&industry=...&days=90
// Returns weekly risk scores + GSCPI for charts
export async function getHistory(event = 'COVID', region = null, industry = null, days = 365) {
  // Map case study event names to regions
  const eventRegionMap = {
    'COVID':   { region: 'Asia',       industry: 'all'           },
    'Suez':    { region: 'Africa',     industry: 'logistics'     },
    'RedSea':  { region: 'Middle_East', industry: 'logistics'    },
  }
  const mapped = eventRegionMap[event] || {}
  const r = region   || mapped.region   || 'all'
  const i = industry || mapped.industry || 'all'

  let url = `${API}/history?days=${days}`
  if (r !== 'all') url += `&region=${r}`
  if (i !== 'all') url += `&industry=${i}`

  const res = await fetch(url)
  return res.json()
}

// ── B5: Search ────────────────────────────────────────────────────────────────
// GET /api/v1/search?query=...&signal_type=...&industry=...
// Returns paginated article cards
export async function searchNews(q = '', type = null, industry = null, page = 1) {
  let url = `${API}/search?page=${page}&page_size=10`
  if (q)        url += `&query=${encodeURIComponent(q)}`
  if (type)     url += `&signal_type=${type}`
  if (industry) url += `&industry=${industry}`

  const res  = await fetch(url)
  const data = await res.json()

  return {
    articles: (data.results || []).map(a => ({
      title:      a.headline,
      severity:   a.risk_score,
      date:       a.article_date,
      industry:   a.affected_industry,
      region:     a.region,
      signal:     a.signal_type,
      sparkline:  [a.risk_score, a.risk_score * 0.9, a.risk_score * 1.1,
                   a.risk_score * 0.95, a.risk_score],
    })),
    total:      data.meta?.total_results || 0,
    totalPages: data.meta?.total_pages   || 1,
  }
}

// ── B6: Ask AI (SSE streaming) ────────────────────────────────────────────────
// POST /api/v1/ask
// Streams NDJSON response — each line is a JSON object
// { type: "sources", sources: [...] }
// { type: "token",   text: "..." }
// { type: "done" }
export async function askAI(question, onToken, onSources, onDone) {
  const res = await fetch(`${API}/ask`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ question, stream: true, top_k: 5 }),
  })

  const reader  = res.body.getReader()
  const decoder = new TextDecoder()
  let   buffer  = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() // keep incomplete line

    for (const line of lines) {
      if (!line.trim()) continue
      try {
        const obj = JSON.parse(line)
        if (obj.type === 'sources' && onSources) onSources(obj.sources)
        if (obj.type === 'token'   && onToken)   onToken(obj.text)
        if (obj.type === 'done'    && onDone)    onDone()
      } catch (e) {
        // skip malformed lines
      }
    }
  }
}

// ── B7: Stats ─────────────────────────────────────────────────────────────────
// GET /api/v1/stats
export async function getStats() {
  const res  = await fetch(`${API}/stats`)
  const data = await res.json()
  return {
    visitors:    data.subscriber_count      || 0,
    requests:    data.total_articles_analysed || 0,
    uptime:      '99.9%',
    alerts:      data.alerts_generated_this_month || 0,
    regions:     data.regions_monitored     || 0,
    dataSources: data.data_sources          || [],
  }
}

// ── B7: Subscribe ─────────────────────────────────────────────────────────────
// POST /api/v1/subscribe
export async function subscribe(email, industry = 'all', region = 'global') {
  const res = await fetch(`${API}/subscribe`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ email, industry, region }),
  })
  return res.json()
}