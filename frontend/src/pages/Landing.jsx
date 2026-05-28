import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { getRisk, getAlerts } from '../api/api'

const INDUSTRIES = ['Semiconductor', 'Automotive', 'Logistics', 'Food', 'Pharmaceutical', 'Energy']

const TICKER_ITEMS = [
  '🔴 Red Sea shipping delays +340% — Houthi attacks forcing Cape reroutes',
  '🟡 Taiwan Strait military exercises disrupting shipping lanes',
  '🔴 Panama Canal drought restrictions — daily transits cut by half',
  '🟢 Suez Canal operations normalized after Ever Given recovery',
  '🟡 UAW strike risk elevated — Ford GM Stellantis contract talks',
  '🔴 Baltic Dry Index down 12% — demand signals weakening',
]

const STATS = [
  { value: '100+', label: 'Signals Extracted',  sub: 'from global news via Gemini' },
  { value: '21d',  label: 'Prediction Horizon', sub: 'advance warning window' },
  { value: '0.89', label: 'RAG-LLM F1 Score',   sub: 'at 7-day horizon' },
]

const HOW_IT_WORKS = [
  { step: '01', title: 'News Ingestion',   desc: 'Global news sources scraped and preprocessed. GDELT 2.0 event data covering 182,888 events across 2019–2024.' },
  { step: '02', title: 'LLM Extraction',   desc: 'Gemini extracts structured signals — severity score, signal type, propagation risk, disruption category.' },
  { step: '03', title: 'RAG Retrieval',    desc: 'TF-IDF + FAISS retrieves relevant historical signals. Context-aware queries per prediction horizon.' },
  { step: '04', title: 'Risk Prediction',  desc: 'Model predicts GSCPI spike probability at 7, 14, 21-day horizons using taxonomy-weighted scoring.' },
]

const FAQS = [
  { q: 'What is NewsShield?',
    a: 'NewsShield is an AI system that predicts global supply chain disruptions by extracting structured signals from news articles using large language models, then correlating them with the NY Fed Global Supply Chain Pressure Index.' },
  { q: 'How accurate are the predictions?',
    a: 'Our RAG-LLM model achieves F1=0.89 at the 7-day horizon. Traditional baselines: ARIMA F1=0.77, LSTM F1=0.55, XGBoost F1=0.52.' },
  { q: 'What industries are covered?',
    a: 'Semiconductor, Automotive, Logistics, Food, Pharmaceutical, Energy — extracted directly from LLM signal categories.' },
  { q: 'Is this based on real research?',
    a: 'Yes. NewsShield is built on an IEEE research paper combining GDELT event data, NY Fed GSCPI ground truth, and LLM-based signal extraction.' },
]

const card  = 'bg-white border border-[#e2e8f0] rounded-xl shadow-sm'
const label = 'font-mono text-[0.7rem] tracking-widest uppercase text-[#94a3b8]'

export default function Landing() {
  const navigate = useNavigate()
  const [ticker,      setTicker]      = useState(0)
  const [riskData,    setRiskData]    = useState(null)
  const [alerts,      setAlerts]      = useState([])
  const [selIndustry, setSelIndustry] = useState('Semiconductor')

  useEffect(() => {
    const t = setInterval(() => setTicker(p => (p + 1) % TICKER_ITEMS.length), 3500)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    getRisk(selIndustry)
      .then(r => setRiskData(r.data))
      .catch(() => setRiskData({
        risk_score: selIndustry === 'Semiconductor' ? 72
                  : selIndustry === 'Logistics'     ? 85
                  : selIndustry === 'Automotive'    ? 61
                  : selIndustry === 'Food'          ? 54
                  : selIndustry === 'Energy'        ? 67 : 48,
        trend: 'rising', signals: 14,
      }))
  }, [selIndustry])

  useEffect(() => {
    getAlerts()
      .then(r => setAlerts(r.data?.alerts || []))
      .catch(() => setAlerts([
        { id:1, severity:'high',   title:'Red Sea Crisis',            industry:'Logistics' },
        { id:2, severity:'high',   title:'Taiwan Strait Tensions',    industry:'Semiconductor' },
        { id:3, severity:'medium', title:'Chip Shortage Emerging',    industry:'Semiconductor' },
        { id:4, severity:'medium', title:'Panama Canal Restrictions', industry:'Logistics' },
        { id:5, severity:'low',    title:'Port Congestion LA',        industry:'Automotive' },
      ]))
  }, [])

  const riskScore = riskData?.risk_score ?? 0
  const riskColor = riskScore >= 70 ? '#ef4444' : riskScore >= 40 ? '#f59e0b' : '#22c55e'

  const severityStyle = s => ({
    high:   'border-red-200   bg-red-50   text-red-700',
    medium: 'border-amber-200 bg-amber-50 text-amber-700',
    low:    'border-green-200 bg-green-50 text-green-700',
  }[s] ?? 'border-gray-200 text-gray-600')

  return (
    <div className="bg-[#f8fafc] text-[#0f172a]">

      {/* Ticker */}
      <div className="bg-[#1e293b] py-2 px-4">
        <AnimatePresence mode="wait">
          <motion.p key={ticker}
            initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.4 }}
            className="text-center text-sm text-[#94a3b8] font-mono">
            {TICKER_ITEMS[ticker]}
          </motion.p>
        </AnimatePresence>
      </div>

      {/* Hero */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 text-center bg-gradient-to-b from-[#f8fafc] to-white">
        <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9 }} className="max-w-4xl">
          <div className="inline-block border border-[#e2e8f0] bg-white rounded-full px-4 py-1 mb-8 shadow-sm">
            <span className={label}>AI-Powered Supply Chain Intelligence</span>
          </div>
          <h1 className="font-mono text-5xl md:text-7xl font-bold mb-6 leading-tight text-[#0f172a]">
            Predict Disruptions
            <br />
            <span style={{ color: '#38bdf8' }}>Before They Hit</span>
          </h1>
          <p className="text-[#64748b] text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
            NewsShield uses LLMs to extract supply chain signals from global news,
            predicting GSCPI spikes up to 21 days in advance.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/dashboard')}
              className="bg-[#0f172a] hover:bg-[#1e293b] text-white font-mono font-bold px-8 py-3 rounded-lg transition-colors text-sm tracking-wider">
              Open Dashboard
            </motion.button>
            <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
              onClick={() => navigate('/about')}
              className="border border-[#e2e8f0] hover:border-[#94a3b8] bg-white text-[#64748b] hover:text-[#0f172a] px-8 py-3 rounded-lg transition-colors font-mono text-sm">
              How It Works
            </motion.button>
          </div>
        </motion.div>
        <motion.div className="mt-20 flex flex-col items-center gap-1 text-[#cbd5e1] font-mono text-xs"
          animate={{ y: [0, 8, 0] }} transition={{ repeat: Infinity, duration: 2.5 }}>
          <span>SCROLL</span><span>↓</span>
        </motion.div>
      </section>

      {/* Stats */}
      <section className="py-20 px-6 border-t border-[#e2e8f0]">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          {STATS.map((s, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ delay: i * 0.15 }}
              className={`${card} p-8 text-center`}>
              <div className="font-mono text-5xl font-bold mb-3" style={{ color: '#38bdf8' }}>{s.value}</div>
              <div className="font-semibold text-[#0f172a] mb-1">{s.label}</div>
              <div className="text-[#94a3b8] text-sm">{s.sub}</div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Industry Demo */}
      <section className="py-20 px-6 border-t border-[#e2e8f0] bg-white">
        <div className="max-w-4xl mx-auto">
          <p className={`${label} text-center mb-3`}>Live Risk Demo</p>
          <h2 className="font-mono text-3xl font-bold text-center mb-2 text-[#0f172a]">Select an Industry</h2>
          <p className="text-[#64748b] text-center mb-10">
            Real-time disruption risk powered by <span style={{ color: '#38bdf8' }}>/api/risk</span>
          </p>
          <div className="flex flex-wrap gap-2 justify-center mb-8">
            {INDUSTRIES.map(ind => (
              <button key={ind} onClick={() => setSelIndustry(ind)}
                className={`px-4 py-2 rounded-lg text-sm font-mono transition-colors border ${
                  selIndustry === ind
                    ? 'bg-[#0f172a] text-white border-[#0f172a] font-bold'
                    : 'bg-white text-[#64748b] border-[#e2e8f0] hover:border-[#94a3b8] hover:text-[#0f172a]'
                }`}>
                {ind}
              </button>
            ))}
          </div>
          <AnimatePresence mode="wait">
            <motion.div key={selIndustry} initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.3 }} className={`${card} p-10 text-center`}>
              <p className={`${label} mb-4`}>{selIndustry} · Current Risk Score</p>
              <div className="font-mono text-8xl font-bold mb-4" style={{ color: riskColor }}>
                {riskScore}
              </div>
              <div className="flex justify-center gap-10 text-sm font-mono mt-4">
                <div><span className="text-[#94a3b8]">TREND </span><span className="text-[#0f172a] capitalize">{riskData?.trend ?? '—'}</span></div>
                <div><span className="text-[#94a3b8]">SIGNALS </span><span className="text-[#0f172a]">{riskData?.signals ?? '—'}</span></div>
                <div><span className="text-[#94a3b8]">LEVEL </span><span style={{ color: riskColor }}>{riskScore >= 70 ? 'HIGH' : riskScore >= 40 ? 'MEDIUM' : 'LOW'}</span></div>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-6 border-t border-[#e2e8f0]">
        <div className="max-w-5xl mx-auto">
          <p className={`${label} text-center mb-3`}>Pipeline</p>
          <h2 className="font-mono text-3xl font-bold text-center mb-12 text-[#0f172a]">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {HOW_IT_WORKS.map((s, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ delay: i * 0.1 }}
                className={`${card} p-6`}>
                <div className="font-mono text-3xl font-bold mb-4" style={{ color: '#38bdf8' }}>{s.step}</div>
                <div className="font-semibold text-[#0f172a] mb-2">{s.title}</div>
                <div className="text-[#64748b] text-sm leading-relaxed">{s.desc}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Alerts */}
      <section className="py-20 px-6 border-t border-[#e2e8f0] bg-white">
        <div className="max-w-3xl mx-auto">
          <p className={`${label} text-center mb-3`}>Live Feed</p>
          <h2 className="font-mono text-3xl font-bold text-center mb-10 text-[#0f172a]">Latest Alerts</h2>
          <div className="space-y-3">
            {alerts.map((a, i) => (
              <motion.div key={a.id ?? i} initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className={`border rounded-xl p-4 flex items-center justify-between ${severityStyle(a.severity)}`}>
                <div>
                  <div className="font-semibold text-sm">{a.title}</div>
                  <div className="text-xs opacity-60 font-mono mt-1">{a.industry}</div>
                </div>
                <div className="font-mono text-xs font-bold uppercase border border-current rounded px-2 py-1 ml-4">
                  {a.severity}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-6 border-t border-[#e2e8f0]">
        <div className="max-w-3xl mx-auto">
          <p className={`${label} text-center mb-3`}>Questions</p>
          <h2 className="font-mono text-3xl font-bold text-center mb-12 text-[#0f172a]">FAQ</h2>
          <div className="space-y-3">
            {FAQS.map((faq, i) => <FAQItem key={i} q={faq.q} a={faq.a} />)}
          </div>
        </div>
      </section>

    </div>
  )
}

function FAQItem({ q, a }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="bg-white border border-[#e2e8f0] rounded-xl overflow-hidden shadow-sm">
      <button onClick={() => setOpen(o => !o)}
        className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-[#f8fafc] transition-colors">
        <span className="font-mono text-sm text-[#0f172a]">{q}</span>
        <span className="font-mono text-[#38bdf8] text-lg ml-4">{open ? '−' : '+'}</span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25 }} className="overflow-hidden">
            <div className="px-6 py-4 text-[#64748b] text-sm leading-relaxed border-t border-[#e2e8f0]">{a}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}