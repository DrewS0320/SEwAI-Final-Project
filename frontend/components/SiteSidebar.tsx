import Link from 'next/link'
import { BarChart3, CircleHelp, Gauge, Home, LayoutDashboard, Upload } from 'lucide-react'

type Section = 'home' | 'results' | 'races' | 'upload' | 'scoring'

export default function SiteSidebar({ active = 'home' }: { active?: Section }) {
  return (
    <>
    <aside className="sidebar">
      <Link href="/" className="brand" aria-label="KartScope home">
        <span className="brand-mark"><Gauge size={19}/></span>
        <span>KART<span className="brand-accent">SCOPE</span><small>TIME TRIAL ANALYTICS</small></span>
      </Link>
      <div className="nav-label">WORKSPACE</div>
      <nav className="side-nav" aria-label="Main navigation">
        <Link className={active === 'home' ? 'selected' : ''} href="/"><Home size={17}/> Home</Link>
        <Link className={active === 'results' ? 'selected' : ''} href="/analysis"><LayoutDashboard size={17}/> Race analysis</Link>
        <Link className={active === 'races' ? 'selected' : ''} href="/dashboard"><BarChart3 size={17}/> Demo races<span className="nav-count">02</span></Link>
        <Link className={active === 'upload' ? 'selected' : ''} href="/upload"><Upload size={17}/> Analyze video</Link>
      </nav>
      <div className="sidebar-bottom">
        <Link href="/scoring" className={`help-link ${active === 'scoring' ? 'selected' : ''}`}><CircleHelp size={16}/> How scoring works</Link>
        <div className="user-chip"><div className="avatar">MK</div><span><b>Demo workspace</b><small>Capstone preview</small></span></div>
      </div>
    </aside>
    <nav className="mobile-site-nav" aria-label="Mobile navigation">
      <Link className={active === 'home' ? 'selected' : ''} href="/"><Home size={17}/> Home</Link>
      <Link className={active === 'results' ? 'selected' : ''} href="/analysis"><LayoutDashboard size={17}/> Results</Link>
      <Link className={active === 'races' ? 'selected' : ''} href="/dashboard"><BarChart3 size={17}/> Demos</Link>
      <Link className={active === 'upload' ? 'selected' : ''} href="/upload"><Upload size={17}/> Analyze</Link>
    </nav>
    </>
  )
}
