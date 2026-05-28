import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import CaseStudies from './pages/CaseStudies'
import NewsExplorer from './pages/NewsExplorer'
import About from './pages/About'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/"            element={<Landing />} />
          <Route path="/dashboard"   element={<Dashboard />} />
          <Route path="/cases"       element={<CaseStudies />} />
          <Route path="/news"        element={<NewsExplorer />} />
          <Route path="/about"       element={<About />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}