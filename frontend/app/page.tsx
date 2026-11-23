import Link from 'next/link'
import { redirect } from 'next/navigation'
import { ArrowRight, BarChart3, ChartNoAxesCombined, Coins, Film, Gauge, ShieldCheck, Sparkles, Upload } from 'lucide-react'
import SiteSidebar from '@/components/SiteSidebar'

export default async function LandingPage({ searchParams }: { searchParams: Promise<{ analysis?: string; race?: string }> }) {
  const params = await searchParams
  // Keep previously shared /?analysis=UUID and /?race=good|bad links working.
  if (params.analysis) redirect(`/analysis?analysis=${encodeURIComponent(params.analysis)}`)
  if (params.race === 'good' || params.race === 'bad') redirect(`/analysis?race=${params.race}`)
  return (
    <div className="app-shell">
      <SiteSidebar active="home" />
      <main className="main-content">
        <header className="topbar"><div className="crumb"><span>WELCOME</span><span className="crumb-slash">/</span><b>KartScope</b></div><Link href="/upload" className="upload-top"><Upload size={14}/> Analyze a race</Link></header>
        <div className="content-wrap landing-wrap">
          <section className="landing-hero">
            <div className="landing-copy">
              <span className="landing-kicker"><Sparkles size={14}/> PRECISION FOR EVERY LAP</span>
              <h1>Race smarter.<br/><span>Find your next second.</span></h1>
              <p>Turn your Mario Kart 8 Deluxe Time Trial recording into a clear picture of your pace, coin management, and where to improve next.</p>
              <div className="landing-actions"><Link className="primary-button landing-primary" href="/upload"><Upload size={17}/> Analyze your race <ArrowRight size={16}/></Link><Link className="landing-secondary" href="/dashboard"><Film size={17}/> Explore demo races</Link></div>
              <div className="landing-scope"><ShieldCheck size={15}/> Calibrated for SNES Rainbow Road · 150cc Time Trials</div>
            </div>
            <div className="landing-art" aria-hidden="true">
              <div className="landing-stars"/>
              <div className="landing-planet"/>
              <div className="landing-road-glow"/>
              <svg viewBox="0 0 520 350" className="landing-art-svg" focusable="false"><defs><linearGradient id="homeRoad" x1="0" x2="1"><stop stopColor="#46eaff"/><stop offset=".22" stopColor="#477eff"/><stop offset=".48" stopColor="#bb63ff"/><stop offset=".7" stopColor="#ff69b2"/><stop offset="1" stopColor="#ffc568"/></linearGradient></defs><path d="M-25 300 C80 270 107 140 230 170 S372 334 553 81" fill="none" stroke="#080e21" strokeWidth="65" strokeLinecap="round"/><path d="M-25 300 C80 270 107 140 230 170 S372 334 553 81" fill="none" stroke="#243150" strokeWidth="48" strokeLinecap="round"/><path d="M-25 300 C80 270 107 140 230 170 S372 334 553 81" fill="none" stroke="url(#homeRoad)" strokeWidth="7" strokeLinecap="round"/><path d="M-25 315 C90 281 110 157 225 186 S379 347 564 94" fill="none" stroke="#bbcee8" strokeWidth="2" strokeDasharray="6 10" opacity=".5"/></svg>
              <span className="landing-art-chip"><Gauge size={15}/> PERFORMANCE, DECODED</span>
            </div>
          </section>
          <div className="landing-section-label">FROM FOOTAGE TO FEEDBACK</div>
          <div className="landing-feature-grid">
            <article className="landing-feature"><span className="landing-feature-icon cyan"><ChartNoAxesCombined size={23}/></span><h2>Measure your pace</h2><p>Review estimated lap splits, consistency, and finishing performance.</p></article>
            <article className="landing-feature"><span className="landing-feature-icon gold"><Coins size={23}/></span><h2>Master your coins</h2><p>Visualize coin counts over time and identify potential losses.</p></article>
            <article className="landing-feature"><span className="landing-feature-icon purple"><BarChart3 size={23}/></span><h2>Know what to improve</h2><p>Get a performance score with focused suggestions for your next session.</p></article>
          </div>
          <div className="landing-bottom"><span>Already have results?</span><Link href="/analysis">Open race analysis <ArrowRight size={14}/></Link><Link href="/scoring">How scoring works <ArrowRight size={14}/></Link></div>
          <footer className="footer-note"><span>KARTSCOPE · CAPSTONE DEMONSTRATION</span><span>Measurements are video-derived estimates; loss detections are unverified.</span></footer>
        </div>
      </main>
    </div>
  )
}
