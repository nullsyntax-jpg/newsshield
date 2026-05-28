import { useState } from 'react'

const CASES = [
  {
    id: 'covid', title: 'COVID-19 Pandemic', subtitle: 'Global Manufacturing Shutdown',
    date: 'March 2020', severity: 'critical', leadTime: 28, impact: '$4.5T global GDP loss',
    industry: 'All Industries', region: 'Global', color: '#ef4444',
    description: 'The COVID-19 pandemic triggered the most severe global supply chain disruption in modern history. Factory shutdowns across China propagated through every global supply chain within weeks.',
    timeline: [
      { day:-28, type:'Precursor',   label:'Wuhan factory closures reported' },
      { day:-21, type:'Amplifier',   label:'Chinese port congestion signals detected' },
      { day:-14, type:'Trigger',     label:'WHO declares public health emergency' },
      { day:-7,  type:'Propagation', label:'European supply chains begin failing' },
      { day:0,   type:'Peak',        label:'GSCPI peaks at 4.3σ above mean' },
      { day:14,  type:'Response',    label:'Emergency production rerouting begins' },
      { day:60,  type:'Recovery',    label:'Gradual normalization over 18 months' },
    ],
    precursors: [
      'Wuhan industrial output decline reported in GDELT events',
      'Chinese logistics sentiment score drops below -3.5',
      'Port throughput at Shanghai falls 15% week-over-week',
      'Semiconductor lead times extend beyond 12 weeks',
      'Air freight capacity from Asia contracts sharply',
      'Factory utilization reports show abnormal declines',
      'Emergency procurement signals from automotive sector',
      'Medical supply chain stress indicators activate',
      'Cross-border shipping insurance premiums spike',
      'GSCPI precursor composite exceeds 1.5σ threshold',
    ],
    gscpi_before: [0.2,0.3,0.4,0.6,0.9,1.4,2.1,3.2,4.3],
    gscpi_after:  [4.3,3.8,3.1,2.4,1.8,1.2,0.8,0.5,0.3],
    model_f1: 0.89, baseline_f1: 0.52,
  },
  {
    id: 'suez', title: 'Suez Canal Blockage', subtitle: 'Ever Given Container Ship Grounding',
    date: 'March 2021', severity: 'high', leadTime: 14, impact: '$9.6B daily trade disrupted',
    industry: 'Logistics / Port', region: 'Middle East', color: '#f59e0b',
    description: 'The Ever Given grounding blocked the Suez Canal for 6 days, halting 12% of global trade. NewsShield detected port congestion precursors 14 days before the blockage became critical.',
    timeline: [
      { day:-14, type:'Precursor',   label:'Unusual vessel traffic patterns at Suez' },
      { day:-7,  type:'Amplifier',   label:'High wind warnings for Red Sea corridor' },
      { day:0,   type:'Trigger',     label:'Ever Given runs aground, canal blocked' },
      { day:3,   type:'Propagation', label:'369 vessels queued, rerouting via Cape' },
      { day:6,   type:'Response',    label:'Ever Given refloated, canal partially open' },
      { day:14,  type:'Recovery',    label:'Backlog cleared, shipping rates normalize' },
    ],
    precursors: [
      'Vessel AIS transponder anomalies near Suez entry',
      'Weather pattern analysis shows high wind risk',
      'Port congestion index at Said rises 22%',
      'Insurance rate spike for Suez transit routes',
      'Shipping schedule deviations increase in GDELT',
      'Canal authority maintenance reports flagged',
      'Container spot rates begin upward movement',
      'Logistics sentiment for Red Sea turns negative',
      'Alternative routing searches surge online',
      'Fuel surcharge announcements from major carriers',
    ],
    gscpi_before: [0.1,0.2,0.3,0.5,0.8,1.2,1.8,2.4,2.9],
    gscpi_after:  [2.9,2.5,2.0,1.5,1.0,0.7,0.4,0.2,0.1],
    model_f1: 0.85, baseline_f1: 0.48,
  },
  {
    id: 'redsea', title: 'Red Sea Crisis', subtitle: 'Houthi Attacks on Commercial Shipping',
    date: 'December 2023', severity: 'high', leadTime: 21, impact: '+340% shipping rate increase',
    industry: 'Logistics / Energy', region: 'Middle East', color: '#8b5cf6',
    description: 'Houthi militant attacks on commercial vessels forced a mass rerouting of global shipping around the Cape of Good Hope, adding 10-14 days to Asia-Europe transit times.',
    timeline: [
      { day:-21, type:'Precursor',   label:'Geopolitical tension signals in Yemen region' },
      { day:-14, type:'Amplifier',   label:'First merchant vessel attack reported' },
      { day:-7,  type:'Trigger',     label:'Maersk suspends Red Sea operations' },
      { day:0,   type:'Propagation', label:'Mass rerouting via Cape of Good Hope' },
      { day:14,  type:'Response',    label:'US/UK naval coalition Operation Prosperity' },
      { day:90,  type:'Ongoing',     label:'Crisis ongoing, shipping rates remain elevated' },
    ],
    precursors: [
      'Houthi militant activity signals in GDELT geopolitical feed',
      'Yemen conflict escalation news volume spikes',
      'Naval vessel movements in Red Sea increase',
      'Shipping insurance premiums for Gulf of Aden rise',
      'Carrier route deviation announcements begin',
      'Energy tanker traffic pattern changes detected',
      'Port of Aden throughput drops sharply',
      'Freight forwarder advisories issued for Red Sea',
      'Container spot rates for Asia-Europe begin rising',
      'Military communication intercepts referenced in news',
    ],
    gscpi_before: [0.3,0.4,0.6,0.9,1.3,1.8,2.3,2.8,3.2],
    gscpi_after:  [3.2,3.0,2.8,2.6,2.4,2.2,2.0,1.8,1.6],
    model_f1: 0.87, baseline_f1: 0.51,
  },
]

const TYPE_COLOR = {
  Precursor:'#38bdf8', Amplifier:'#f59e0b', Trigger:'#ef4444',
  Propagation:'#8b5cf6', Response:'#22c55e', Recovery:'#94a3b8',
  Peak:'#ef4444', Ongoing:'#f59e0b',
}

const card  = 'bg-white border border-[#e2e8f0] rounded-xl shadow-sm'
const label = 'font-mono text-[0.7rem] tracking-widest uppercase text-[#94a3b8]'

export default function CaseStudies() {
  const [selected, setSelected] = useState('covid')
  const cs = CASES.find(c => c.id === selected)

  return (
    <div className="bg-[#f8fafc] text-[#0f172a] min-h-screen p-6">

      <div className="mb-6">
        <p className={`${label} mb-1`}>NewsShield · Historical Analysis</p>
        <h1 className="font-mono text-2xl font-bold text-[#0f172a]">Case Studies</h1>
        <p className="text-[#64748b] text-sm mt-1">How NewsShield predicted real supply chain disruptions before they peaked</p>
      </div>

      {/* Case Selector */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        {CASES.map(c => (
          <button key={c.id} onClick={() => setSelected(c.id)}
            className={`${card} p-4 text-left transition-all border-2 ${
              selected === c.id ? 'border-[#38bdf8]' : 'border-[#e2e8f0] hover:border-[#94a3b8]'
            }`}>
            <div className="flex items-start justify-between mb-2">
              <div className="w-3 h-3 rounded-full mt-1" style={{ background: c.color }} />
              <span className={`font-mono text-xs border rounded px-2 py-0.5 ${
                c.severity === 'critical'
                  ? 'border-red-200 bg-red-50 text-red-700'
                  : 'border-amber-200 bg-amber-50 text-amber-700'
              }`}>{c.severity}</span>
            </div>
            <p className="font-mono font-bold text-sm text-[#0f172a]">{c.title}</p>
            <p className="text-[#64748b] text-xs mt-1">{c.subtitle}</p>
            <div className="flex items-center gap-3 mt-3">
              <span className="font-mono text-xs text-[#38bdf8]">{c.date}</span>
              <span className="font-mono text-xs text-[#94a3b8]">Lead: {c.leadTime}d</span>
            </div>
          </button>
        ))}
      </div>

      {/* Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <div className={`${card} p-6`}>
          <p className={`${label} mb-4`}>Event Summary</p>
          <div className="w-full h-1 rounded mb-4" style={{ background: cs.color }} />
          <h2 className="font-mono text-lg font-bold mb-1" style={{ color: cs.color }}>{cs.title}</h2>
          <p className="text-[#64748b] text-sm mb-4 leading-relaxed">{cs.description}</p>
          <div className="space-y-2 border-t border-[#e2e8f0] pt-4">
            {[
              { label:'Date',      value: cs.date },
              { label:'Industry',  value: cs.industry },
              { label:'Region',    value: cs.region },
              { label:'Impact',    value: cs.impact },
              { label:'Lead Time', value: `${cs.leadTime} days` },
            ].map((item,i) => (
              <div key={i} className="flex justify-between">
                <span className="font-mono text-xs text-[#94a3b8]">{item.label}</span>
                <span className="font-mono text-xs text-[#0f172a] font-medium">{item.value}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 rounded-lg bg-[#f8fafc] border border-[#e2e8f0]">
            <p className="font-mono text-xs font-bold text-[#0f172a] mb-2">Model Performance</p>
            <div className="flex justify-between">
              <span className="font-mono text-xs text-[#64748b]">RAG-LLM F1</span>
              <span className="font-mono text-xs font-bold text-[#8b5cf6]">{cs.model_f1}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span className="font-mono text-xs text-[#64748b]">Baseline F1</span>
              <span className="font-mono text-xs text-[#94a3b8]">{cs.baseline_f1}</span>
            </div>
          </div>
        </div>

        <div className={`${card} p-6 lg:col-span-2`}>
          <p className={`${label} mb-4`}>Signal Timeline — {cs.leadTime}-day lead time</p>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-px bg-[#e2e8f0]" />
            <div className="space-y-4">
              {cs.timeline.map((item,i) => (
                <div key={i} className="flex items-start gap-4 pl-10 relative">
                  <div className="absolute left-2 w-5 h-5 rounded-full border-2 flex items-center justify-center bg-white"
                    style={{ borderColor: TYPE_COLOR[item.type] }}>
                    <div className="w-2 h-2 rounded-full" style={{ background: TYPE_COLOR[item.type] }} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded"
                        style={{ color: TYPE_COLOR[item.type], background: TYPE_COLOR[item.type] + '18' }}>
                        {item.type}
                      </span>
                      <span className="font-mono text-xs text-[#94a3b8]">
                        {item.day < 0 ? `${Math.abs(item.day)}d before peak` : item.day === 0 ? 'Peak' : `${item.day}d after`}
                      </span>
                    </div>
                    <p className="text-sm text-[#64748b]">{item.label}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
        <div className={`${card} p-6`}>
          <p className={`${label} mb-4`}>GSCPI Trajectory</p>
          <div className="flex items-end gap-1 h-32">
            {[...cs.gscpi_before, ...cs.gscpi_after].map((v,i) => {
              const isPeak   = i === cs.gscpi_before.length - 1
              const isBefore = i < cs.gscpi_before.length
              const maxV = Math.max(...cs.gscpi_before, ...cs.gscpi_after)
              return (
                <div key={i} className="flex-1 rounded-t transition-all"
                  style={{
                    height: `${(v/maxV)*100}%`,
                    background: isPeak ? '#ef4444' : isBefore ? '#38bdf8' : '#e2e8f0',
                    opacity: isPeak ? 1 : 0.8,
                  }} />
              )
            })}
          </div>
          <div className="flex justify-between mt-2">
            <span className="font-mono text-[0.6rem] text-[#38bdf8]">Before</span>
            <span className="font-mono text-[0.6rem] text-[#ef4444]">Peak</span>
            <span className="font-mono text-[0.6rem] text-[#94a3b8]">After</span>
          </div>
          <div className="mt-4 flex justify-center">
            <div className="bg-[#f0f9ff] border border-[#bae6fd] rounded-full px-4 py-2">
              <span className="font-mono text-sm text-[#0369a1] font-bold">{cs.leadTime}-day advance warning</span>
            </div>
          </div>
        </div>

        <div className={`${card} p-6`}>
          <p className={`${label} mb-4`}>Top 10 Precursor Signals Detected</p>
          <div className="space-y-2">
            {cs.precursors.map((p,i) => (
              <div key={i} className="flex items-start gap-2">
                <span className="font-mono text-xs text-[#38bdf8] shrink-0 mt-0.5 font-bold">{String(i+1).padStart(2,'0')}</span>
                <p className="text-xs text-[#64748b] leading-relaxed">{p}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={`${card} p-6`}>
        <p className={`${label} mb-4`}>Model vs Baseline Comparison — {cs.title}</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { name:'RAG-LLM (NewsShield)', f1: cs.model_f1,    color:'#8b5cf6', desc:'LLM-extracted signals + TF-IDF retrieval' },
            { name:'ARIMA Baseline',        f1: 0.769,          color:'#94a3b8', desc:'GSCPI time-series only, no news signals' },
            { name:'XGBoost',               f1: cs.baseline_f1, color:'#38bdf8', desc:'GDELT structured features, 100 variables' },
          ].map((m,i) => (
            <div key={i} className="text-center">
              <p className="font-mono text-xs text-[#94a3b8] mb-2">{m.name}</p>
              <div className="relative w-24 h-24 mx-auto mb-2">
                <svg viewBox="0 0 36 36" className="w-24 h-24 -rotate-90">
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e2e8f0" strokeWidth="3" />
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke={m.color} strokeWidth="3"
                    strokeDasharray={`${m.f1*100} 100`} strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="font-mono text-lg font-bold" style={{ color: m.color }}>{m.f1}</span>
                </div>
              </div>
              <p className="font-mono text-[0.6rem] text-[#94a3b8]">{m.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}