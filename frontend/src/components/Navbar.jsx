import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const { pathname } = useLocation()
  const links = [
    { to: '/',          label: 'Home' },
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/cases',     label: 'Case Studies' },
    { to: '/news',      label: 'News' },
    { to: '/about',     label: 'About' },
  ]
  return (
    <nav className="bg-[#1e293b] border-b border-[#334155] px-6 py-4 flex items-center justify-between">
      <Link to="/" className="text-[#38bdf8] font-mono font-bold text-xl tracking-tight">
        NewsShield
      </Link>
      <div className="flex gap-6 text-sm">
        {links.map(l => (
          <Link key={l.to} to={l.to}
            className={`font-mono transition-colors ${
              pathname === l.to
                ? 'text-[#38bdf8]'
                : 'text-[#94a3b8] hover:text-white'
            }`}>
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  )
}