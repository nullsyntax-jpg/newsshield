import { useState, useEffect, useRef } from 'react'
import { searchNews, askAI } from '../api/api'

const SIGNAL_TYPES = ['All','Trigger','Precursor','Amplifier','Propagation','Response','Recovery']
const INDUSTRIES   = ['All','Semiconductor','Automotive','Logistics','Food','Pharmaceutical','Energy']

const MOCK_ARTICLES = [
  { id:1,  headline:'Taiwan Strait military exercises disrupt commercial shipping lanes',        signal_type:'Trigger',     industry:'Semiconductor', region:'East Asia',     severity:5, date:'2024-01-15' },
  { id:2,  headline:'Houthi militants attack Maersk container vessel in Red Sea',              signal_type:'Trigger',     industry:'Logistics',     region:'Middle East',   severity:5, date:'2024-01-12' },
  { id:3,  headline:'TSMC evacuates fabs temporarily following Taiwan earthquake',             signal_type:'Trigger',     industry:'Semiconductor', region:'East Asia',     severity:4, date:'2024-04-03' },
  { id:4,  headline:'Panama Canal reduces daily transits by half due to historic drought',     signal_type:'Trigger',     industry:'Logistics',     region:'Latin America', severity:5, date:'2023-12-20' },
  { id:5,  headline:'US restricts advanced AI chip exports to China citing national security', signal_type:'Trigger',     industry:'Semiconductor', region:'North America', severity:5, date:'2023-10-17' },
  { id:6,  headline:'UAW strikes Ford GM and Stellantis simultaneously for first time',        signal_type:'Trigger',     industry:'Automotive',    region:'North America', severity:5, date:'2023-09-15' },
  { id:7,  headline:'Taiwan semiconductor orders decline for third consecutive month',         signal_type:'Precursor',   industry:'Semiconductor', region:'East Asia',     severity:4, date:'2023-08-10' },
  { id:8,  headline:'Brazilian drought threatens soybean harvest and global food supply',      signal_type:'Precursor',   industry:'Food',          region:'Latin America', severity:4, date:'2023-07-22' },
  { id:9,  headline:'European chemical industry warns of deindustrialization risk',            signal_type:'Precursor',   industry:'Energy',        region:'Europe',        severity:5, date:'2023-06-14' },
  { id:10, headline:'Monsoon floods damage key rail links used to reroute Red Sea cargo',      signal_type:'Amplifier',   industry:'Logistics',     region:'South Asia',    severity:4, date:'2024-02-01' },
  { id:11, headline:'European steel mills shut down as energy costs make production unviable', signal_type:'Amplifier',   industry:'Energy',        region:'Europe',        severity:5, date:'2022-09-05' },
  { id:12, headline:'Foxconn Zhengzhou iPhone factory output cut as worker protests intensify',signal_type:'Amplifier',   industry:'Electronics',   region:'East Asia',     severity:4, date:'2022-11-23' },
  { id:13, headline:'Red Sea shipping delays now hitting food retailers in West Africa',       signal_type:'Propagation', industry:'Food',          region:'Africa',        severity:4, date:'2024-01-28' },
  { id:14, headline:'Vietnam electronics exports fall as Samsung shifts orders to India',      signal_type:'Propagation', industry:'Electronics',   region:'South Asia',    severity:4, date:'2023-05-18' },
  { id:15, headline:'Maersk reroutes vessels around Cape of Good Hope avoiding Red Sea',       signal_type:'Response',    industry:'Logistics',     region:'Global',        severity:3, date:'2023-12-22' },
  { id:16, headline:'Semiconductor lead times fall below 20 weeks for first time since 2020', signal_type:'Recovery',    industry:'Semiconductor', region:'Global',        severity:1, date:'2023-04-10' },
]

const TYPE_STYLE = {
  Trigger:     'bg-red-50   border-red-200   text-red-700',
  Precursor:   'bg-sky-50   border-sky-200   text-sky-700',
  Amplifier:   'bg-amber-50 border-amber-200 text-amber-700',
  Propagation: 'bg-purple-50 border-purple-200 text-purple-700',
  Response:    'bg-green-50 border-green-200 text-green-700',
  Recovery:    'bg-gray-50  border-gray-200  text-gray-600',
}

const TYPE_LEFT = {
  Trigger:'#ef4444', Precursor:'#38bdf8', Amplifier:'#f59e0b',
  Propagation:'#8b5cf6', Response:'#22c55e', Recovery:'#94a3b8',
}

const card  = 'bg-white border border-[#e2e8f0] rounded-xl shadow-sm'
const label = 'font-mono text-[0.7rem] tracking-widest uppercase text-[#94a3b8]'

export default function NewsExplorer() {
  const [query,      setQuery]      = useState('')
  const [sigFilter,  setSigFilter]  = useState('All')
  const [indFilter,  setIndFilter]  = useState('All')
  const [articles,   setArticles]   = useState(MOCK_ARTICLES)
  const [aiInput,    setAiInput]    = useState('')
  const [aiMessages, setAiMessages] = useState([
    { role:'assistant', text:'Ask me anything about supply chain risks. I can analyse signals, explain disruptions, or predict risk based on current news.' }
  ])
  const [aiLoading, setAiLoading] = useState(false)
  const chatRef = useRef(null)

  useEffect(() => {
    const t = setTimeout(() => {
      let filtered = MOCK_ARTICLES
      if (query.trim()) {
        const q = query.toLowerCase()
        filtered = filtered.filter(a => a.headline.toLowerCase().includes(q) || a.industry.toLowerCase().includes(q) || a.region.toLowerCase().includes(q))
      }
      if (sigFilter !== 'All') filtered = filtered.filter(a => a.signal_type === sigFilter)
      if (indFilter !== 'All') filtered = filtered.filter(a => a.industry === indFilter)
      searchNews(query || 'supply chain').then(r => setArticles(r.data?.results || filtered)).catch(() => setArticles(filtered))
    }, 300)
    return () => clearTimeout(t)
  }, [query, sigFilter, indFilter])

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
  }, [aiMessages])

  const sendMessage = async () => {
    if (!aiInput.trim() || aiLoading) return
    const userMsg = aiInput.trim()
    setAiInput('')
    setAiMessages(prev => [...prev, { role:'user', text: userMsg }])
    setAiLoading(true)
    try {
      const r = await askAI(userMsg)
      setAiMessages(prev => [...prev, { role:'assistant', text: r.data?.answer || r.data?.response || 'Analysis complete.' }])
    } catch {
      const responses = {
        default: 'Based on current signal analysis, global supply chain pressure remains elevated. The Red Sea crisis continues to impact logistics with shipping rates up 340%. Semiconductor lead times have stabilized but geopolitical tensions in the Taiwan Strait pose ongoing Precursor signals.',
        risk:    'Current risk assessment: HIGH for Logistics (Red Sea crisis), MEDIUM-HIGH for Semiconductor (Taiwan tensions), MEDIUM for Automotive (EV transition). Recommend monitoring GSCPI over next 14 days.',
        predict: 'My 21-day forecast shows elevated disruption probability (68%) for Logistics based on 14 active Trigger and Amplifier signals. Primary drivers: Red Sea rerouting and Panama Canal drought restrictions.',
      }
      const key = userMsg.toLowerCase().includes('risk') ? 'risk' : userMsg.toLowerCase().includes('predict') || userMsg.toLowerCase().includes('forecast') ? 'predict' : 'default'
      setAiMessages(prev => [...prev, { role:'assistant', text: responses[key] }])
    }
    setAiLoading(false)
  }

  const heatmapData = INDUSTRIES.slice(1).map(ind => ({
    industry: ind,
    counts: SIGNAL_TYPES.slice(1).map(sig => ({
      type: sig,
      count: MOCK_ARTICLES.filter(a => a.industry === ind && a.signal_type === sig).length,
    }))
  }))
  const maxCount = Math.max(...heatmapData.flatMap(r => r.counts.map(c => c.count)))

  const severityDot = n => n >= 5 ? 'bg-red-400' : n >= 4 ? 'bg-amber-400' : n >= 3 ? 'bg-blue-400' : 'bg-green-400'

  return (
    <div className="bg-[#f8fafc] text-[#0f172a] min-h-screen p-6">

      <div className="mb-6">
        <p className={`${label} mb-1`}>NewsShield · Signal Intelligence</p>
        <h1 className="font-mono text-2xl font-bold text-[#0f172a]">News Explorer</h1>
        <p className="text-[#64748b] text-sm mt-1">Search and filter supply chain signals extracted from global news</p>
      </div>

      <div className={`${card} p-4 mb-4`}>
        <input type="text" value={query} onChange={e => setQuery(e.target.value)}
          placeholder="Search headlines, industries, regions..."
          className="w-full bg-[#f8fafc] border border-[#e2e8f0] rounded-lg px-4 py-3 font-mono text-sm text-[#0f172a] placeholder-[#cbd5e1] focus:outline-none focus:border-[#38bdf8] mb-4" />
        <div className="flex flex-wrap gap-4">
          <div>
            <p className={`${label} mb-2`}>Signal Type</p>
            <div className="flex flex-wrap gap-1">
              {SIGNAL_TYPES.map(t => (
                <button key={t} onClick={() => setSigFilter(t)}
                  className={`font-mono text-xs px-3 py-1 rounded-full border transition-colors ${
                    sigFilter === t ? 'bg-[#0f172a] text-white border-[#0f172a]' : 'text-[#64748b] border-[#e2e8f0] hover:border-[#94a3b8]'
                  }`}>{t}</button>
              ))}
            </div>
          </div>
          <div>
            <p className={`${label} mb-2`}>Industry</p>
            <div className="flex flex-wrap gap-1">
              {INDUSTRIES.map(i => (
                <button key={i} onClick={() => setIndFilter(i)}
                  className={`font-mono text-xs px-3 py-1 rounded-full border transition-colors ${
                    indFilter === i ? 'bg-[#0f172a] text-white border-[#0f172a]' : 'text-[#64748b] border-[#e2e8f0] hover:border-[#94a3b8]'
                  }`}>{i}</button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <div className="lg:col-span-2 space-y-3 max-h-[600px] overflow-y-auto pr-1">
          <p className={`${label} mb-2`}>{articles.length} signals found</p>
          {articles.length === 0 ? (
            <div className={`${card} p-8 text-center text-[#94a3b8] font-mono text-sm`}>No signals match your filters</div>
          ) : articles.map((a,i) => (
            <div key={a.id ?? i} className="bg-white border border-[#e2e8f0] rounded-xl p-4 shadow-sm border-l-4 hover:shadow-md transition-shadow"
              style={{ borderLeftColor: TYPE_LEFT[a.signal_type] ?? '#94a3b8' }}>
              <div className="flex items-start justify-between gap-2 mb-2">
                <p className="text-sm text-[#0f172a] font-medium leading-snug flex-1">{a.headline}</p>
                <div className={`w-2.5 h-2.5 rounded-full shrink-0 mt-1 ${severityDot(a.severity)}`} />
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`font-mono text-xs px-2 py-0.5 rounded border ${TYPE_STYLE[a.signal_type] ?? 'bg-gray-50 border-gray-200 text-gray-600'}`}>
                  {a.signal_type}
                </span>
                <span className="font-mono text-xs text-[#64748b]">{a.industry}</span>
                <span className="font-mono text-xs text-[#cbd5e1]">·</span>
                <span className="font-mono text-xs text-[#64748b]">{a.region}</span>
                <span className="font-mono text-xs text-[#94a3b8] ml-auto">{a.date}</span>
              </div>
            </div>
          ))}
        </div>

        <div className={`${card} p-4 flex flex-col`} style={{ height:600 }}>
          <p className={`${label} mb-3`}>Ask the AI</p>
          <div ref={chatRef} className="flex-1 overflow-y-auto space-y-3 mb-3 pr-1">
            {aiMessages.map((msg,i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-xl px-3 py-2 text-xs font-mono leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-[#0f172a] text-white'
                    : 'bg-[#f1f5f9] text-[#64748b] border border-[#e2e8f0]'
                }`}>{msg.text}</div>
              </div>
            ))}
            {aiLoading && (
              <div className="flex justify-start">
                <div className="bg-[#f1f5f9] border border-[#e2e8f0] rounded-xl px-3 py-2">
                  <div className="flex gap-1">
                    {[0,1,2].map(i => (
                      <div key={i} className="w-1.5 h-1.5 bg-[#94a3b8] rounded-full animate-bounce"
                        style={{ animationDelay:`${i*0.15}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <input type="text" value={aiInput} onChange={e => setAiInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder="Ask about supply chain risks..."
              className="flex-1 bg-[#f8fafc] border border-[#e2e8f0] rounded-lg px-3 py-2 font-mono text-xs text-[#0f172a] placeholder-[#cbd5e1] focus:outline-none focus:border-[#38bdf8]" />
            <button onClick={sendMessage} disabled={aiLoading}
              className="bg-[#0f172a] hover:bg-[#1e293b] disabled:opacity-50 text-white font-mono font-bold px-3 py-2 rounded-lg text-xs transition-colors">
              →
            </button>
          </div>
        </div>
      </div>

      <div className={`${card} p-6`}>
        <p className={`${label} mb-4`}>Industry × Signal Type Heatmap</p>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr>
                <th className="text-left font-mono text-xs text-[#94a3b8] pb-2 pr-4">Industry</th>
                {SIGNAL_TYPES.slice(1).map(t => (
                  <th key={t} className="font-mono text-xs text-[#94a3b8] pb-2 px-2 text-center">{t}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {heatmapData.map((row,i) => (
                <tr key={i} className="border-t border-[#f1f5f9]">
                  <td className="font-mono text-xs text-[#64748b] pr-4 py-2">{row.industry}</td>
                  {row.counts.map((cell,j) => (
                    <td key={j} className="px-2 py-2 text-center">
                      <div className="w-8 h-8 mx-auto rounded flex items-center justify-center font-mono text-xs font-bold"
                        style={{
                          background: cell.count > 0 ? `rgba(56,189,248,${(cell.count/maxCount)*0.7+0.1})` : '#f8fafc',
                          color: cell.count > 0 ? '#0369a1' : '#cbd5e1',
                          border: cell.count > 0 ? '1px solid rgba(56,189,248,0.3)' : '1px solid #e2e8f0',
                        }}>
                        {cell.count || '·'}
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}