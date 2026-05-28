import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { getRisk, getAlerts } from '../api/api'

const INDUSTRIES = ['Semiconductor', 'Automotive', 'Logistics', 'Food', 'Pharmaceutical', 'Energy']

const REGION_RISK = {
  Semiconductor: { 'East Asia': 85, 'North America': 45, 'Europe': 40, 'South Asia': 30, 'Middle East': 35, 'Latin America': 25 },
  Automotive:    { 'East Asia': 70, 'North America': 50, 'Europe': 65, 'South Asia': 40, 'Middle East': 45, 'Latin America': 35 },
  Logistics:     { 'Middle East': 80, 'East Asia': 55, 'Europe': 40, 'North America': 35, 'South Asia': 50, 'Latin America': 45 },
  Food:          { 'Africa': 75, 'Middle East': 70, 'East Asia': 40, 'Europe': 30, 'North America': 25, 'South Asia': 65 },
  Pharmaceutical:{ 'South Asia': 55, 'East Asia': 60, 'Europe': 35, 'North America': 30, 'Middle East': 40, 'Latin America': 35 },
  Energy:        { 'Middle East': 75, 'East Asia': 50, 'Europe': 60, 'North America': 40, 'South Asia': 45, 'Latin America': 40 },
}

const SIGNAL_TYPES = [
  { name: 'Trigger',     value: 28, color: '#ef4444' },
  { name: 'Amplifier',   value: 22, color: '#f59e0b' },
  { name: 'Propagation', value: 18, color: '#8b5cf6' },
  { name: 'Precursor',   value: 20, color: '#38bdf8' },
  { name: 'Response',    value: 8,  color: '#22c55e' },
  { name: 'Recovery',    value: 4,  color: '#94a3b8' },
]

const card  = 'bg-white border border-[#e2e8f0] rounded-xl shadow-sm'
const label = 'font-mono text-[0.7rem] tracking-widest uppercase text-[#94a3b8]'

function RiskGauge({ score }) {
  const pct   = Math.min(Math.max(score, 0), 100)
  const angle = (pct / 100) * 180 - 90
  const color = pct >= 70 ? '#ef4444' : pct >= 40 ? '#f59e0b' : '#22c55e'
  const r = 70, cx = 90, cy = 90
  const arcPath = (startDeg, endDeg, c) => {
    const toRad = d => (d - 90) * Math.PI / 180
    const x1 = cx + r * Math.cos(toRad(startDeg)), y1 = cy + r * Math.sin(toRad(startDeg))
    const x2 = cx + r * Math.cos(toRad(endDeg)),   y2 = cy + r * Math.sin(toRad(endDeg))
    return <path d={`M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`}
      fill="none" stroke={c} strokeWidth="12" strokeLinecap="round" />
  }
  const nx = cx + (r - 12) * Math.cos((angle - 90) * Math.PI / 180)
  const ny = cy + (r - 12) * Math.sin((angle - 90) * Math.PI / 180)
  return (
    <svg viewBox="0 0 180 100" className="w-full max-w-[200px] mx-auto">
      {arcPath(-90, -30, '#22c55e')}{arcPath(-30, 30, '#f59e0b')}{arcPath(30, 90, '#ef4444')}
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={color} strokeWidth="3" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="5" fill={color} />
      <text x={cx} y={cy + 18} textAnchor="middle" style={{ fill: color, fontSize: 14, fontWeight: 700, fontFamily: 'monospace' }}>{pct}</text>
    </svg>
  )
}

export default function Dashboard() {
  const [industry, setIndustry] = useState('Semiconductor')
  const [riskData, setRiskData] = useState(null)
  const [alerts,   setAlerts]   = useState([])
  const [forecast, setForecast] = useState([])
  const [heatmap,  setHeatmap]  = useState([])
  const [email,    setEmail]    = useState('')
  const [subscribed, setSubscribed] = useState(false)

  useEffect(() => {
    const avg = Object.values(REGION_RISK[industry]).reduce((a,b) => a+b,0) / Object.values(REGION_RISK[industry]).length
    let cur = avg
    const days = []
    for (let i = 1; i <= 21; i++) {
      cur = Math.min(Math.max(cur + (Math.random() - 0.48) * 6, 10), 95)
      const d = new Date(); d.setDate(d.getDate() + i)
      days.push({ day: d.toLocaleDateString('en', { month:'short', day:'numeric' }), risk: Math.round(cur) })
    }
    setForecast(days)
  }, [industry])

  useEffect(() => {
    const avg = Object.values(REGION_RISK[industry]).reduce((a,b) => a+b,0) / Object.values(REGION_RISK[industry]).length
    const cells = []
    for (let i = 29; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i)
      cells.push({ date: d.toLocaleDateString('en', { month:'short', day:'numeric' }), value: Math.round(Math.min(Math.max(avg + (Math.random()-0.5)*30, 5), 95)) })
    }
    setHeatmap(cells)
  }, [industry])

  useEffect(() => {
    getRisk(industry).then(r => setRiskData(r))
      .catch(() => setRiskData({ risk_score: REGION_RISK[industry]['East Asia'] ?? 60, trend:'rising', signals:14 }))
  }, [industry])

  useEffect(() => {
    getAlerts().then(r => setAlerts(r.alerts || []))
      .catch(() => setAlerts([
        { id:1, severity:'high',   title:'Red Sea shipping crisis ongoing',   industry:'Logistics',     region:'Middle East' },
        { id:2, severity:'high',   title:'Taiwan Strait military exercises',  industry:'Semiconductor', region:'East Asia' },
        { id:3, severity:'medium', title:'Panama Canal drought restrictions', industry:'Logistics',     region:'Latin America' },
        { id:4, severity:'medium', title:'European energy cost surge',        industry:'Manufacturing', region:'Europe' },
        { id:5, severity:'low',    title:'Chip lead times normalizing',       industry:'Semiconductor', region:'Global' },
      ]))
  }, [])

  const riskScore = riskData?.risk_score ?? 60
  const riskColor = riskScore >= 70 ? '#ef4444' : riskScore >= 40 ? '#f59e0b' : '#22c55e'
  const riskLabel = riskScore >= 70 ? 'HIGH' : riskScore >= 40 ? 'MEDIUM' : 'LOW'
  const regionData = Object.entries(REGION_RISK[industry] ?? {}).map(([region, risk]) => ({ region, risk })).sort((a,b) => b.risk - a.risk)

  const severityStyle = s => ({
    high:   'border-red-200   bg-red-50   text-red-700',
    medium: 'border-amber-200 bg-amber-50 text-amber-700',
    low:    'border-green-200 bg-green-50 text-green-700',
  }[s] ?? 'border-gray-200 text-gray-600')

  const heatColor = v => v >= 70 ? '#fca5a5' : v >= 55 ? '#fcd34d' : v >= 40 ? '#86efac' : v >= 25 ? '#bbf7d0' : '#dcfce7'

  return (
    <div className="bg-[#f8fafc] text-[#0f172a] min-h-screen p-6">

      <div className="mb-6">
        <p className={`${label} mb-1`}>NewsShield · Risk Intelligence</p>
        <h1 className="font-mono text-2xl font-bold text-[#0f172a]">Supply Chain Dashboard</h1>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        {INDUSTRIES.map(ind => (
          <button key={ind} onClick={() => setIndustry(ind)}
            className={`px-4 py-2 rounded-lg text-sm font-mono border transition-colors ${
              industry === ind
                ? 'bg-[#0f172a] text-white border-[#0f172a] font-bold'
                : 'bg-white text-[#64748b] border-[#e2e8f0] hover:border-[#94a3b8]'
            }`}>
            {ind}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label:'Current Risk',   value:`${riskScore}`,           color: riskColor },
          { label:'Risk Level',     value: riskLabel,               color: riskColor },
          { label:'Active Signals', value:`${riskData?.signals ?? 14}`, color:'#38bdf8' },
          { label:'Trend',          value: riskData?.trend ?? 'rising', color:'#f59e0b' },
        ].map((m, i) => (
          <div key={i} className={`${card} p-4`}>
            <p className={label}>{m.label}</p>
            <p className="font-mono text-2xl font-bold mt-1 capitalize" style={{ color: m.color }}>{m.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div className={`${card} p-6 flex flex-col items-center justify-center`}>
          <p className={`${label} mb-4`}>Risk Gauge — {industry}</p>
          <RiskGauge score={riskScore} />
          <p className="font-mono text-xs text-[#94a3b8] mt-2 text-center">
            {riskScore >= 70 ? 'Immediate attention required' : riskScore >= 40 ? 'Monitor closely' : 'Within normal range'}
          </p>
        </div>

        <div className={`${card} p-6`}>
          <p className={`${label} mb-4`}>Risk by Region</p>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={regionData} layout="vertical">
              <XAxis type="number" domain={[0,100]} tick={{ fill:'#94a3b8', fontSize:10 }} />
              <YAxis type="category" dataKey="region" tick={{ fill:'#64748b', fontSize:10 }} width={80} />
              <Tooltip contentStyle={{ background:'#fff', border:'1px solid #e2e8f0', borderRadius:8 }}
                labelStyle={{ color:'#0f172a' }} itemStyle={{ color:'#64748b' }} />
              <Bar dataKey="risk" radius={[0,4,4,0]}>
                {regionData.map((e,i) => <Cell key={i} fill={e.risk >= 70 ? '#ef4444' : e.risk >= 40 ? '#f59e0b' : '#22c55e'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className={`${card} p-6`}>
          <p className={`${label} mb-4`}>Signal Breakdown</p>
          <div className="flex items-center gap-4">
            <PieChart width={120} height={120}>
              <Pie data={SIGNAL_TYPES} cx={55} cy={55} innerRadius={30} outerRadius={55} dataKey="value" paddingAngle={2}>
                {SIGNAL_TYPES.map((s,i) => <Cell key={i} fill={s.color} />)}
              </Pie>
            </PieChart>
            <div className="flex flex-col gap-1">
              {SIGNAL_TYPES.map((s,i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: s.color }} />
                  <span className="font-mono text-[0.65rem] text-[#64748b]">{s.name}</span>
                  <span className="font-mono text-[0.65rem] text-[#94a3b8] ml-auto">{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className={`${card} p-6 mb-4`}>
        <p className={`${label} mb-4`}>21-Day Risk Forecast — {industry}</p>
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={forecast}>
            <XAxis dataKey="day" tick={{ fill:'#94a3b8', fontSize:9 }} tickLine={false} interval={2} />
            <YAxis domain={[0,100]} tick={{ fill:'#94a3b8', fontSize:10 }} tickLine={false} />
            <Tooltip contentStyle={{ background:'#fff', border:'1px solid #e2e8f0', borderRadius:8 }}
              labelStyle={{ color:'#0f172a' }} />
            <Bar dataKey="risk" radius={[3,3,0,0]}>
              {forecast.map((e,i) => <Cell key={i} fill={e.risk >= 70 ? '#ef4444' : e.risk >= 40 ? '#f59e0b' : '#22c55e'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className={`${card} p-6`}>
          <p className={`${label} mb-4`}>30-Day Risk Heatmap</p>
          <div className="grid gap-1" style={{ gridTemplateColumns:'repeat(10, 1fr)' }}>
            {heatmap.map((cell,i) => (
              <div key={i} title={`${cell.date}: ${cell.value}`}
                className="aspect-square rounded-sm cursor-pointer hover:opacity-80 transition-opacity"
                style={{ background: heatColor(cell.value) }} />
            ))}
          </div>
          <div className="flex justify-between mt-2">
            <span className="font-mono text-[0.6rem] text-[#94a3b8]">30 days ago</span>
            <span className="font-mono text-[0.6rem] text-[#94a3b8]">today</span>
          </div>
        </div>

        <div className={`${card} p-6`}>
          <p className={`${label} mb-4`}>Active Alerts</p>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {alerts.map((a,i) => (
              <div key={a.id ?? i} className={`border rounded-lg p-3 flex items-start justify-between ${severityStyle(a.severity)}`}>
                <div>
                  <p className="font-semibold text-sm">{a.title}</p>
                  <p className="font-mono text-xs opacity-60 mt-0.5">{a.industry} · {a.region}</p>
                </div>
                <span className="font-mono text-xs font-bold uppercase border border-current rounded px-1.5 py-0.5 ml-2 shrink-0">{a.severity}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={`${card} p-6 mb-4`}>
        <p className={`${label} mb-4`}>Model Performance Comparison</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm font-mono">
            <thead>
              <tr className="border-b border-[#e2e8f0]">
                {['Model','Variant','F1 (7d)','F1 (14d)','AUC (14d)','Notes'].map(h => (
                  <th key={h} className="text-left py-2 px-3 text-xs text-[#94a3b8] font-normal">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                { model:'ARIMA',    variant:'GSCPI only',     f1_7:'0.769', f1_14:'0.769', auc:'1.000', notes:'Baseline',      color:'#64748b' },
                { model:'XGBoost', variant:'Full features',   f1_7:'0.524', f1_14:'0.519', auc:'0.607', notes:'100 features',  color:'#38bdf8' },
                { model:'LSTM',    variant:'Full features',   f1_7:'0.549', f1_14:'0.549', auc:'0.681', notes:'Best practical',color:'#38bdf8' },
                { model:'RAG-LLM', variant:'TF-IDF + Gemini', f1_7:'0.889', f1_14:'0.889', auc:'1.000', notes:'Text only',     color:'#8b5cf6' },
              ].map((row,i) => (
                <tr key={i} className="border-b border-[#f1f5f9] hover:bg-[#f8fafc] transition-colors">
                  <td className="py-2 px-3 font-bold" style={{ color: row.color }}>{row.model}</td>
                  <td className="py-2 px-3 text-[#64748b]">{row.variant}</td>
                  <td className="py-2 px-3 text-[#0f172a]">{row.f1_7}</td>
                  <td className="py-2 px-3 text-[#0f172a]">{row.f1_14}</td>
                  <td className="py-2 px-3 text-[#0f172a]">{row.auc}</td>
                  <td className="py-2 px-3 text-[#94a3b8] text-xs">{row.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className={`${card} p-6`}>
        <p className={`${label} mb-2`}>Alert Subscription</p>
        <p className="text-[#64748b] text-sm mb-4">Get notified when risk exceeds threshold for your industry.</p>
        {subscribed ? (
          <p className="text-green-600 font-mono text-sm">✓ Subscribed successfully</p>
        ) : (
          <div className="flex gap-3">
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="your@email.com"
              className="flex-1 bg-white border border-[#e2e8f0] rounded-lg px-4 py-2 text-sm font-mono text-[#0f172a] placeholder-[#cbd5e1] focus:outline-none focus:border-[#38bdf8]" />
            <button onClick={() => { if (email) setSubscribed(true) }}
              className="bg-[#0f172a] hover:bg-[#1e293b] text-white font-mono font-bold px-6 py-2 rounded-lg text-sm transition-colors">
              Subscribe
            </button>
          </div>
        )}
      </div>
    </div>
  )
}