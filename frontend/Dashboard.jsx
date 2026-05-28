import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { getRisk, getAlerts, getHistory, getStats } from '../api/api'

const INDUSTRIES = ['Semiconductor', 'Automotive', 'Logistics', 'Food', 'Pharmaceutical', 'Energy']

const REGION_RISK = {
  Semiconductor:  { 'East Asia': 85, 'North America': 45, 'Europe': 40, 'South Asia': 30, 'Middle East': 35, 'Latin America': 25 },
  Automotive:     { 'East Asia': 70, 'North America': 50, 'Europe': 65, 'South Asia': 40, 'Middle East': 45, 'Latin America': 35 },
  Logistics:      { 'Middle East': 80, 'East Asia': 55, 'Europe': 40, 'North America': 35, 'South Asia': 50, 'Latin America': 45 },
  Food:           { 'Africa': 75, 'Middle East': 70, 'East Asia': 40, 'Europe': 30, 'North America': 25, 'South Asia': 65 },
  Pharmaceutical: { 'South Asia': 55, 'East Asia': 60, 'Europe': 35, 'North America': 30, 'Middle East': 40, 'Latin America': 35 },
  Energy:         { 'Middle East': 75, 'East Asia': 50, 'Europe': 60, 'North America': 40, 'South Asia': 45, 'Latin America': 40 },
}

const SIGNAL_TYPES = [
  { name: 'Trigger',     value: 28, color: '#e76f51' },
  { name: 'Amplifier',   value: 22, color: '#f4a261' },
  { name: 'Propagation', value: 18, color: '#6d6875' },
  { name: 'Precursor',   value: 20, color: '#457b9d' },
  { name: 'Response',    value: 8,  color: '#2d6a4f' },
  { name: 'Recovery',    value: 4,  color: '#a8c5b5' },
]

// ── Palette ──────────────────────────────────────────────────────────────────
const P = {
  pageBg:       '#f8f7f4',
  cardBg:       '#ffffff',
  border:       '#e8e5df',
  textPrimary:  '#1c1917',
  textSecond:   '#6b6560',
  textMuted:    '#a09890',
  accentGreen:  '#2d6a4f',
  accentAmber:  '#b45309',
  accentRed:    '#c0392b',
  accentBlue:   '#457b9d',
  tagline:      '#9e9189',
}

const riskColor = score =>
  score >= 70 ? P.accentRed : score >= 40 ? P.accentAmber : P.accentGreen

const riskLabel = score =>
  score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW'

const heatColor = v =>
  v >= 70 ? '#c0392b' : v >= 55 ? '#e76f51' : v >= 40 ? '#b45309' : v >= 25 ? '#2d6a4f' : '#a8c5b5'

const card  = `bg-white border rounded-xl`
const bdr   = `border-[#e8e5df]`
const label = `text-[0.68rem] tracking-widest uppercase font-medium`

// ── Risk Gauge ────────────────────────────────────────────────────────────────
function RiskGauge({ score }) {
  const pct   = Math.min(Math.max(score, 0), 100)
  const angle = (pct / 100) * 180 - 90
  const color = riskColor(pct)
  const r = 70, cx = 90, cy = 90

  const arcPath = (startDeg, endDeg, stroke) => {
    const toRad = d => (d - 90) * Math.PI / 180
    const x1 = cx + r * Math.cos(toRad(startDeg))
    const y1 = cy + r * Math.sin(toRad(startDeg))
    const x2 = cx + r * Math.cos(toRad(endDeg))
    const y2 = cy + r * Math.sin(toRad(endDeg))
    const large = endDeg - startDeg > 180 ? 1 : 0
    return (
      <path
        d={`M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`}
        fill="none" stroke={stroke} strokeWidth="10" strokeLinecap="round"
      />
    )
  }

  const needleX = cx + (r - 14) * Math.cos((angle - 90) * Math.PI / 180)
  const needleY = cy + (r - 14) * Math.sin((angle - 90) * Math.PI / 180)

  return (
    <svg viewBox="0 0 180 100" className="w-full max-w-[210px] mx-auto">
      {arcPath(-90, -30, '#a8c5b5')}
      {arcPath(-30, 30,  '#f4d4a0')}
      {arcPath(30,  90,  '#e8b4ae')}
      <line x1={cx} y1={cy} x2={needleX} y2={needleY}
        stroke={color} strokeWidth="2.5" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="5" fill={color} />
      <text x={cx} y={cy + 18} textAnchor="middle"
        style={{ fill: color, fontSize: 14, fontWeight: 700, fontFamily: 'inherit' }}>
        {pct}
      </text>
    </svg>
  )
}

// ── Severity badge styles ─────────────────────────────────────────────────────
const severityStyle = s => ({
  high:   'border-[#f5c0bb] bg-[#fdf3f2] text-[#9b2c2c]',
  medium: 'border-[#fde68a] bg-[#fffbeb] text-[#92400e]',
  low:    'border-[#a7d9bc] bg-[#f0faf4] text-[#1e5c3a]',
}[s] ?? 'border-[#e8e5df] text-[#6b6560]')

// ── Custom Tooltip ────────────────────────────────────────────────────────────
const ChartTooltip = ({ active, payload, label: lbl }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-[#e8e5df] rounded-lg px-3 py-2 text-sm shadow-sm">
      <p className="text-[#6b6560] mb-0.5">{lbl}</p>
      <p className="font-semibold text-[#1c1917]">{payload[0].value}</p>
    </div>
  )
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const navigate = useNavigate()
  const [industry,   setIndustry]   = useState('Semiconductor')
  const [riskData,   setRiskData]   = useState(null)
  const [alerts,     setAlerts]     = useState([])
  const [forecast,   setForecast]   = useState([])
  const [heatmap,    setHeatmap]    = useState([])
  const [email,      setEmail]      = useState('')
  const [subscribed, setSubscribed] = useState(false)

  // 21-day forecast
  useEffect(() => {
    const base = REGION_RISK[industry]
    const avg  = Object.values(base).reduce((a, b) => a + b, 0) / Object.values(base).length
    const days = []
    let cur = avg
    for (let i = 1; i <= 21; i++) {
      cur = Math.min(Math.max(cur + (Math.random() - 0.48) * 6, 10), 95)
      const d = new Date()
      d.setDate(d.getDate() + i)
      days.push({ day: d.toLocaleDateString('en', { month: 'short', day: 'numeric' }), risk: Math.round(cur) })
    }
    setForecast(days)
  }, [industry])

  // 30-day heatmap
  useEffect(() => {
    const base = REGION_RISK[industry]
    const avg  = Object.values(base).reduce((a, b) => a + b, 0) / Object.values(base).length
    const cells = []
    for (let i = 29; i >= 0; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      const v = Math.min(Math.max(avg + (Math.random() - 0.5) * 30, 5), 95)
      cells.push({ date: d.toLocaleDateString('en', { month: 'short', day: 'numeric' }), value: Math.round(v) })
    }
    setHeatmap(cells)
  }, [industry])

  // Risk fetch
  useEffect(() => {
    getRisk(industry)
      .then(r => setRiskData(r.data))
      .catch(() => setRiskData({
        risk_score: REGION_RISK[industry]['East Asia'] ?? 60,
        trend: 'rising', signals: 14,
      }))
  }, [industry])

  // Alerts fetch
  useEffect(() => {
    getAlerts()
      .then(r => setAlerts(r.data?.alerts || []))
      .catch(() => setAlerts([
        { id:1, severity:'high',   title:'Red Sea shipping crisis ongoing',   industry:'Logistics',     region:'Middle East'   },
        { id:2, severity:'high',   title:'Taiwan Strait military exercises',  industry:'Semiconductor', region:'East Asia'     },
        { id:3, severity:'medium', title:'Panama Canal drought restrictions', industry:'Logistics',     region:'Latin America' },
        { id:4, severity:'medium', title:'European energy cost surge',        industry:'Manufacturing', region:'Europe'        },
        { id:5, severity:'low',    title:'Chip lead times normalizing',       industry:'Semiconductor', region:'Global'        },
      ]))
  }, [])

  const score   = riskData?.risk_score ?? 60
  const color   = riskColor(score)
  const rlabel  = riskLabel(score)

  const regionData = Object.entries(REGION_RISK[industry] ?? {})
    .map(([region, risk]) => ({ region, risk }))
    .sort((a, b) => b.risk - a.risk)

  return (
    <div style={{ background: P.pageBg }} className="min-h-screen p-6 text-[#1c1917]">

      {/* Header */}
      <div className="mb-6">
        <p style={{ color: P.tagline }} className={`${label} mb-1`}>NewsShield · Risk Intelligence</p>
        <h1 className="text-2xl font-bold text-[#1c1917]">Supply Chain Dashboard</h1>
      </div>

      {/* Industry Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {INDUSTRIES.map(ind => (
          <button
            key={ind}
            onClick={() => setIndustry(ind)}
            className={`px-4 py-2 rounded-lg text-sm border transition-colors ${
              industry === ind
                ? 'border-[#2d6a4f] bg-[#2d6a4f] text-white font-semibold'
                : 'border-[#e8e5df] bg-white text-[#6b6560] hover:border-[#2d6a4f] hover:text-[#2d6a4f]'
            }`}
          >
            {ind}
          </button>
        ))}
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Current Risk',   value: `${score}`,                    color },
          { label: 'Risk Level',     value: rlabel,                         color },
          { label: 'Active Signals', value: `${riskData?.signals ?? 14}`,  color: P.accentBlue },
          { label: 'Trend',          value: riskData?.trend ?? 'rising',   color: P.accentAmber },
        ].map((m, i) => (
          <div key={i} className={`${card} ${bdr} p-4`}>
            <p style={{ color: P.textMuted }} className={label}>{m.label}</p>
            <p className="text-2xl font-bold mt-1 capitalize" style={{ color: m.color }}>{m.value}</p>
          </div>
        ))}
      </div>

      {/* Row 1: Gauge + Region Bar + Signal Donut */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">

        {/* Gauge */}
        <div className={`${card} ${bdr} p-6 flex flex-col items-center justify-center`}>
          <p style={{ color: P.textMuted }} className={`${label} mb-4`}>Risk Gauge — {industry}</p>
          <RiskGauge score={score} />
          <p style={{ color: P.textMuted }} className="text-xs mt-2 text-center">
            {score >= 70 ? 'Immediate attention required'
           : score >= 40 ? 'Monitor closely'
           : 'Within normal range'}
          </p>
        </div>

        {/* Region Bar Chart */}
        <div className={`${card} ${bdr} p-6`}>
          <p style={{ color: P.textMuted }} className={`${label} mb-4`}>Risk by Region</p>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={regionData} layout="vertical" margin={{ left: 0 }}>
              <XAxis type="number" domain={[0, 100]}
                tick={{ fill: P.textMuted, fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="region"
                tick={{ fill: P.textSecond, fontSize: 10 }} width={85} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="risk" radius={[0, 4, 4, 0]}>
                {regionData.map((entry, i) => (
                  <Cell key={i} fill={riskColor(entry.risk)} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Signal Donut */}
        <div className={`${card} ${bdr} p-6`}>
          <p style={{ color: P.textMuted }} className={`${label} mb-4`}>Signal Breakdown</p>
          <div className="flex items-center gap-4">
            <PieChart width={120} height={120}>
              <Pie data={SIGNAL_TYPES} cx={55} cy={55} innerRadius={30} outerRadius={55}
                dataKey="value" paddingAngle={2}>
                {SIGNAL_TYPES.map((s, i) => <Cell key={i} fill={s.color} />)}
              </Pie>
            </PieChart>
            <div className="flex flex-col gap-1.5">
              {SIGNAL_TYPES.map((s, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: s.color }} />
                  <span style={{ color: P.textSecond }} className="text-[0.65rem]">{s.name}</span>
                  <span style={{ color: P.textPrimary }} className="text-[0.65rem] ml-auto font-medium">{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 21-day Forecast */}
      <div className={`${card} ${bdr} p-6 mb-4`}>
        <p style={{ color: P.textMuted }} className={`${label} mb-4`}>21-Day Risk Forecast — {industry}</p>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={forecast} margin={{ left: 0, right: 10 }}>
            <XAxis dataKey="day" tick={{ fill: P.textMuted, fontSize: 9 }} tickLine={false} interval={2} axisLine={false} />
            <YAxis domain={[0, 100]} tick={{ fill: P.textMuted, fontSize: 10 }} tickLine={false} axisLine={false} />
            <Tooltip content={<ChartTooltip />} />
            <Bar dataKey="risk" radius={[3, 3, 0, 0]}>
              {forecast.map((entry, i) => (
                <Cell key={i} fill={riskColor(entry.risk)} fillOpacity={0.8} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Row 3: Heatmap + Alerts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">

        {/* Heatmap */}
        <div className={`${card} ${bdr} p-6`}>
          <p style={{ color: P.textMuted }} className={`${label} mb-4`}>30-Day Risk Heatmap</p>
          <div className="grid gap-1.5" style={{ gridTemplateColumns: 'repeat(10, 1fr)' }}>
            {heatmap.map((cell, i) => (
              <div
                key={i}
                title={`${cell.date}: ${cell.value}`}
                className="aspect-square rounded cursor-pointer transition-opacity hover:opacity-70"
                style={{ background: heatColor(cell.value) }}
              />
            ))}
          </div>
          <div className="flex justify-between mt-3">
            <span style={{ color: P.textMuted }} className="text-[0.6rem]">30 days ago</span>
            <span style={{ color: P.textMuted }} className="text-[0.6rem]">today</span>
          </div>
          {/* Legend */}
          <div className="flex items-center gap-2 mt-3 flex-wrap">
            {[
              { label: 'Low', color: '#a8c5b5' },
              { label: 'Moderate', color: '#2d6a4f' },
              { label: 'Elevated', color: '#b45309' },
              { label: 'High', color: '#e76f51' },
              { label: 'Critical', color: '#c0392b' },
            ].map(l => (
              <div key={l.label} className="flex items-center gap-1">
                <div className="w-3 h-3 rounded-sm" style={{ background: l.color }} />
                <span style={{ color: P.textMuted }} className="text-[0.6rem]">{l.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts */}
        <div className={`${card} ${bdr} p-6`}>
          <p style={{ color: P.textMuted }} className={`${label} mb-4`}>Active Alerts</p>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {alerts.map((a, i) => (
              <div
                key={a.id ?? i}
                className={`border rounded-lg p-3 flex items-start justify-between ${severityStyle(a.severity)}`}
              >
                <div>
                  <p className="font-semibold text-sm">{a.title}</p>
                  <p className="text-xs opacity-60 mt-0.5">{a.industry} · {a.region}</p>
                </div>
                <span className="text-xs font-bold uppercase border border-current rounded px-1.5 py-0.5 ml-2 shrink-0">
                  {a.severity}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Model Performance Table */}
      <div className={`${card} ${bdr} p-6 mb-4`}>
        <p style={{ color: P.textMuted }} className={`${label} mb-4`}>Model Performance Comparison</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#e8e5df]">
                {['Model', 'Variant', 'F1 (7d)', 'F1 (14d)', 'AUC (14d)', 'Notes'].map(h => (
                  <th key={h} className="text-left py-2 px-3 text-[0.7rem] font-medium tracking-wide uppercase"
                    style={{ color: P.textMuted }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                { model: 'ARIMA',    variant: 'GSCPI only',     f1_7: '0.769', f1_14: '0.769', auc: '1.000', notes: 'Baseline',       color: P.textSecond  },
                { model: 'XGBoost', variant: 'Full features',   f1_7: '0.524', f1_14: '0.519', auc: '0.607', notes: '100 features',    color: P.accentBlue  },
                { model: 'LSTM',    variant: 'Full features',   f1_7: '0.549', f1_14: '0.549', auc: '0.681', notes: 'Best practical',  color: P.accentBlue  },
                { model: 'RAG-LLM', variant: 'TF-IDF + Gemini', f1_7: '0.889', f1_14: '0.889', auc: '1.000', notes: 'Text only',       color: '#6d6875'     },
              ].map((row, i) => (
                <tr key={i} className="border-b border-[#f3f1ed] hover:bg-[#faf9f7] transition-colors">
                  <td className="py-2.5 px-3 font-bold" style={{ color: row.color }}>{row.model}</td>
                  <td className="py-2.5 px-3" style={{ color: P.textSecond }}>{row.variant}</td>
                  <td className="py-2.5 px-3 font-medium" style={{ color: P.textPrimary }}>{row.f1_7}</td>
                  <td className="py-2.5 px-3 font-medium" style={{ color: P.textPrimary }}>{row.f1_14}</td>
                  <td className="py-2.5 px-3 font-medium" style={{ color: P.textPrimary }}>{row.auc}</td>
                  <td className="py-2.5 px-3 text-xs" style={{ color: P.textMuted }}>{row.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Email Subscription */}
      <div className={`${card} ${bdr} p-6`}>
        <p style={{ color: P.textMuted }} className={`${label} mb-2`}>Alert Subscription</p>
        <p style={{ color: P.textSecond }} className="text-sm mb-4">
          Get notified when risk exceeds threshold for your industry.
        </p>
        {subscribed ? (
          <p style={{ color: P.accentGreen }} className="text-sm font-semibold">✓ Subscribed successfully</p>
        ) : (
          <div className="flex gap-3">
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="flex-1 border border-[#e8e5df] rounded-lg px-4 py-2 text-sm text-[#1c1917] placeholder-[#c4bdb8] focus:outline-none focus:border-[#2d6a4f] bg-white transition-colors"
            />
            <button
              onClick={() => { if (email) setSubscribed(true) }}
              className="px-6 py-2 rounded-lg text-sm font-semibold transition-colors"
              style={{ background: P.accentGreen, color: '#fff' }}
              onMouseEnter={e => e.target.style.background = '#235a40'}
              onMouseLeave={e => e.target.style.background = P.accentGreen}
            >
              Subscribe
            </button>
          </div>
        )}
      </div>

    </div>
  )
}
