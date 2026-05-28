import { useState } from 'react'

const PIPELINE_STAGES = [
  { id:'ingest',  step:'01', title:'News Ingestion',  color:'#38bdf8',
    desc:'Global news sources scraped and preprocessed. GDELT 2.0 provides 182,888 structured events across 2019–2024.',
    details:'GDELT 2.0 event database • 21 monthly CSV files • CAMEO event code mapping • Region × week aggregation • 25 base features' },
  { id:'extract', step:'02', title:'LLM Extraction',  color:'#8b5cf6',
    desc:'Gemini-2.5-flash extracts structured signals from raw news headlines with severity, signal type, and propagation risk.',
    details:'100 signals extracted • 13-category schema • severity_score 1-5 • propagation_risk: global/regional/local • 6-type taxonomy' },
  { id:'retrieve',step:'03', title:'RAG Retrieval',   color:'#f59e0b',
    desc:'TF-IDF vectorization builds a searchable index. FAISS enables fast similarity search for relevant historical signals.',
    details:'TF-IDF ngram(1,2) • max_features=5000 • FAISS flat index • top-5 retrieval • horizon-aware queries (7d/14d/21d)' },
  { id:'predict', step:'04', title:'Risk Prediction', color:'#22c55e',
    desc:'Retrieved signals are scored using T2 taxonomy weights and aggregated into a GSCPI spike probability.',
    details:'Taxonomy-weighted scoring • GSCPI threshold: mean + 0.8σ • Horizons: 7d, 14d, 21d • F1=0.889 at 7d' },
]

const TECH_STACK = [
  { name:'Python 3.11',      category:'Backend',   color:'#38bdf8' },
  { name:'Gemini 2.5 Flash', category:'LLM',       color:'#8b5cf6' },
  { name:'FAISS',            category:'Retrieval', color:'#f59e0b' },
  { name:'TF-IDF',           category:'NLP',       color:'#22c55e' },
  { name:'GDELT 2.0',        category:'Data',      color:'#38bdf8' },
  { name:'NY Fed GSCPI',     category:'Data',      color:'#38bdf8' },
  { name:'XGBoost',          category:'ML',        color:'#ef4444' },
  { name:'PyTorch LSTM',     category:'ML',        color:'#ef4444' },
  { name:'ARIMA',            category:'ML',        color:'#ef4444' },
  { name:'React 18',         category:'Frontend',  color:'#64748b' },
  { name:'Tailwind CSS',     category:'Frontend',  color:'#64748b' },
  { name:'Recharts',         category:'Frontend',  color:'#64748b' },
  { name:'FastAPI',          category:'API',       color:'#22c55e' },
  { name:'Vercel',           category:'Deploy',    color:'#94a3b8' },
]

const ABLATION = [
  { variant:'A: Full features (100)', f1:0.524, auc:0.607 },
  { variant:'B: Tone only (12)',       f1:0.486, auc:0.521 },
  { variant:'C: No text (16)',         f1:0.516, auc:0.581 },
]

const TEAM = [
  { name:'Member B — Surya', role:'RAG-LLM Pipeline & Frontend', color:'#38bdf8',
    tasks:['T2: Signal Taxonomy','T3: LLM Extraction','T4: GSCPI Correlation','T5: RAG Model','T6: Case Studies','F1–F7: Full Frontend'] },
  { name:'Member A — Janhavi', role:'GDELT Pipeline & ML Models', color:'#8b5cf6',
    tasks:['T1: GDELT Ingestion','T2: Feature Engineering','T3: ARIMA Baseline','T4: XGBoost + Ablation','T5: LSTM Model','B1–B7: Full Backend'] },
]

const ABSTRACT = `NewsShield: Predicting Global Supply Chain Disruptions from News Using Large Language Models

Abstract: We present NewsShield, a novel RAG-LLM system for predicting supply chain disruptions by extracting structured signals from global news. Our approach combines GDELT 2.0 event data with LLM-based signal extraction using a 6-type taxonomy (Precursor, Trigger, Amplifier, Propagation, Response, Recovery) to predict GSCPI spikes at 7, 14, and 21-day horizons. Evaluated against ARIMA, XGBoost, and LSTM baselines, our RAG-LLM achieves F1=0.889 at the 7-day horizon. Unlike structured GDELT models, our LLM extraction provides industry-level granularity across 13 disruption categories, enabling more interpretable predictions for supply chain practitioners.`

const card  = 'bg-white border border-[#e2e8f0] rounded-xl shadow-sm'
const label = 'font-mono text-[0.7rem] tracking-widest uppercase text-[#94a3b8]'

export default function About() {
  const [activeStage,    setActiveStage]    = useState(null)
  const [ablationOn,     setAblationOn]     = useState([true, false, false])
  const [copiedAbstract, setCopiedAbstract] = useState(false)

  const copyAbstract = () => {
    navigator.clipboard.writeText(ABSTRACT)
    setCopiedAbstract(true)
    setTimeout(() => setCopiedAbstract(false), 2000)
  }

  return (
    <div className="bg-[#f8fafc] text-[#0f172a] min-h-screen p-6">

      <div className="mb-6">
        <p className={`${label} mb-1`}>NewsShield · Research</p>
        <h1 className="font-mono text-2xl font-bold text-[#0f172a]">About & Research</h1>
        <p className="text-[#64748b] text-sm mt-1">IEEE research paper — supply chain disruption prediction using LLMs</p>
      </div>

      {/* Abstract */}
      <div className={`${card} p-6 mb-4`}>
        <div className="flex items-center justify-between mb-4">
          <p className={label}>Paper Abstract</p>
          <button onClick={copyAbstract}
            className={`font-mono text-xs px-3 py-1 rounded border transition-colors ${
              copiedAbstract
                ? 'border-green-200 text-green-700 bg-green-50'
                : 'border-[#e2e8f0] text-[#64748b] hover:border-[#94a3b8]'
            }`}>
            {copiedAbstract ? '✓ Copied' : 'Copy Citation'}
          </button>
        </div>
        <div className="border border-[#e2e8f0] rounded-lg p-4 bg-[#f8fafc]">
          <p className="font-mono text-xs text-[#64748b] leading-relaxed whitespace-pre-line">{ABSTRACT}</p>
        </div>
      </div>

      {/* Pipeline */}
      <div className={`${card} p-6 mb-4`}>
        <p className={`${label} mb-4`}>Pipeline Architecture — Click to expand</p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {PIPELINE_STAGES.map(stage => (
            <div key={stage.id}>
              <button onClick={() => setActiveStage(activeStage === stage.id ? null : stage.id)}
                className={`w-full text-left rounded-xl p-4 border-2 transition-all ${
                  activeStage === stage.id ? '' : 'border-[#e2e8f0] hover:border-[#94a3b8]'
                }`}
                style={{
                  borderColor: activeStage === stage.id ? stage.color : undefined,
                  background: activeStage === stage.id ? stage.color + '08' : '#fff',
                }}>
                <div className="font-mono text-2xl font-bold mb-2" style={{ color: stage.color }}>{stage.step}</div>
                <p className="font-semibold text-sm text-[#0f172a] mb-1">{stage.title}</p>
                <p className="text-xs text-[#64748b] leading-relaxed">{stage.desc}</p>
              </button>
              {activeStage === stage.id && (
                <div className="mt-2 p-3 rounded-lg border text-xs font-mono text-[#64748b] leading-relaxed"
                  style={{ borderColor: stage.color + '40', background: stage.color + '06' }}>
                  {stage.details}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Ablation */}
      <div className={`${card} p-6 mb-4`}>
        <div className="flex items-center justify-between mb-4">
          <p className={label}>Ablation Study — XGBoost Variants</p>
          <p className="font-mono text-xs text-[#94a3b8]">Toggle variants to compare</p>
        </div>
        <div className="flex gap-3 mb-4 flex-wrap">
          {ABLATION.map((v,i) => (
            <button key={i} onClick={() => { const n=[...ablationOn]; n[i]=!n[i]; setAblationOn(n) }}
              className={`font-mono text-xs px-3 py-1.5 rounded border transition-colors ${
                ablationOn[i] ? 'bg-[#f0f9ff] border-[#bae6fd] text-[#0369a1]' : 'border-[#e2e8f0] text-[#94a3b8]'
              }`}>
              {ablationOn[i] ? '✓' : '○'} {v.variant}
            </button>
          ))}
        </div>
        <div className="space-y-3">
          {ABLATION.map((v,i) => ablationOn[i] && (
            <div key={i} className="flex items-center gap-4">
              <span className="font-mono text-xs text-[#64748b] w-48 shrink-0">{v.variant}</span>
              <div className="flex-1 flex items-center gap-2">
                <span className="font-mono text-xs text-[#94a3b8] w-8">F1</span>
                <div className="flex-1 bg-[#f1f5f9] rounded-full h-2">
                  <div className="h-2 rounded-full bg-[#38bdf8] transition-all" style={{ width:`${v.f1*100}%` }} />
                </div>
                <span className="font-mono text-xs text-[#38bdf8] w-10">{v.f1}</span>
              </div>
              <div className="flex-1 flex items-center gap-2">
                <span className="font-mono text-xs text-[#94a3b8] w-8">AUC</span>
                <div className="flex-1 bg-[#f1f5f9] rounded-full h-2">
                  <div className="h-2 rounded-full bg-[#8b5cf6] transition-all" style={{ width:`${v.auc*100}%` }} />
                </div>
                <span className="font-mono text-xs text-[#8b5cf6] w-10">{v.auc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className={`${card} p-6 mb-4`}>
        <p className={`${label} mb-4`}>Tech Stack</p>
        <div className="flex flex-wrap gap-2">
          {TECH_STACK.map((t,i) => (
            <div key={i} className="flex items-center gap-2 bg-[#f8fafc] border border-[#e2e8f0] rounded-lg px-3 py-1.5">
              <div className="w-2 h-2 rounded-full" style={{ background: t.color }} />
              <span className="font-mono text-xs text-[#64748b]">{t.name}</span>
              <span className="font-mono text-[0.6rem] text-[#cbd5e1]">{t.category}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Team */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {TEAM.map((member,i) => (
          <div key={i} className={`${card} p-6`} style={{ borderLeftWidth:3, borderLeftColor: member.color }}>
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="font-mono font-bold" style={{ color: member.color }}>{member.name}</p>
                <p className="text-[#64748b] text-sm">{member.role}</p>
              </div>
              <div className="w-10 h-10 rounded-full flex items-center justify-center font-mono font-bold text-lg"
                style={{ background: member.color + '18', color: member.color }}>
                {member.name.split('—')[0].trim().slice(-1)}
              </div>
            </div>
            <div className="space-y-1 border-t border-[#e2e8f0] pt-3">
              {member.tasks.map((task,j) => (
                <div key={j} className="flex items-center gap-2">
                  <div className="w-1 h-1 rounded-full" style={{ background: member.color }} />
                  <span className="font-mono text-xs text-[#64748b]">{task}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Performance Table */}
      <div className={`${card} p-6`}>
        <p className={`${label} mb-4`}>Model Performance Summary</p>
        <div className="overflow-x-auto">
          <table className="w-full font-mono text-sm">
            <thead>
              <tr className="border-b border-[#e2e8f0]">
                {['Model','Type','F1 (7d)','F1 (14d)','F1 (21d)','AUC','Notes'].map(h => (
                  <th key={h} className="text-left py-2 px-3 text-xs text-[#94a3b8] font-normal">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                { model:'ARIMA',    type:'Statistical',  f7:'0.769', f14:'0.769', f21:'0.714', auc:'1.000', notes:'GSCPI only',         color:'#64748b' },
                { model:'XGBoost', type:'ML',            f7:'0.524', f14:'0.519', f21:'0.520', auc:'0.607', notes:'100 GDELT features',  color:'#38bdf8' },
                { model:'LSTM',    type:'Deep Learning', f7:'0.549', f14:'0.549', f21:'0.554', auc:'0.681', notes:'8-week windows',      color:'#38bdf8' },
                { model:'RAG-LLM', type:'LLM',           f7:'0.889', f14:'0.889', f21:'0.889', auc:'1.000', notes:'Text only ✓',         color:'#8b5cf6' },
              ].map((row,i) => (
                <tr key={i} className="border-b border-[#f1f5f9] hover:bg-[#f8fafc] transition-colors">
                  <td className="py-2 px-3 font-bold" style={{ color: row.color }}>{row.model}</td>
                  <td className="py-2 px-3 text-[#64748b] text-xs">{row.type}</td>
                  <td className="py-2 px-3 text-[#0f172a]">{row.f7}</td>
                  <td className="py-2 px-3 text-[#0f172a]">{row.f14}</td>
                  <td className="py-2 px-3 text-[#0f172a]">{row.f21}</td>
                  <td className="py-2 px-3 text-[#0f172a]">{row.auc}</td>
                  <td className="py-2 px-3 text-[#94a3b8] text-xs">{row.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}