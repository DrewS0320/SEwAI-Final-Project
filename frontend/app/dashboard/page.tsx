import Link from 'next/link'
import { ArrowRight, FileVideo2, Upload } from 'lucide-react'
import { formatTime, races, WORLD_RECORD_SECONDS } from '@/lib/races'
import SiteSidebar from '@/components/SiteSidebar'
import RaceVideo from '@/components/RaceVideo'

export default function DashboardPage() {
  return <div className="app-shell"><SiteSidebar active="races"/><main className="main-content">
    <header className="topbar"><div className="crumb"><span>WORKSPACE</span><span className="crumb-slash">/</span><b>Demo races</b></div><Link className="upload-top" href="/upload"><Upload size={14}/> New analysis</Link></header>
    <div className="content-wrap"><div className="page-kicker">DEMONSTRATION DATASET</div><h1 className="standalone-title">Race library</h1><p className="standalone-subtitle">Watch the driving behind each score, then explore the lap and coin analysis.</p>
      <div className="race-library">{Object.values(races).map(r=><article key={r.id} className="panel library-card"><div className="library-top"><span className={`demo-score ${r.id}`}>{r.score}<small> / 100</small></span><span className="data-chip"><span/> ANALYZED</span></div><div className="section-kicker">SNES RAINBOW ROAD · 150CC</div><h2>{r.id === 'good' ? 'Good race' : 'Bad race'}</h2><p className="library-file"><FileVideo2 size={14}/>{r.filename}</p>
        <RaceVideo src={`/videos/${r.filename}`} title={`${r.id === 'good' ? 'Good' : 'Bad'} race recording`} />
        <div className="library-stats"><div><small>RACE TIME</small><b className="mono">{formatTime(r.totalSeconds)}</b></div><div><small>PACE</small><b>{r.pace}</b></div><div><small>WR GAP</small><b className="mono">+{formatTime(r.totalSeconds - WORLD_RECORD_SECONDS)}</b></div></div><Link className="primary-button full-button" href={`/analysis?race=${r.id}`}>View full analysis <ArrowRight size={15}/></Link></article>)}</div>
    </div>
  </main></div>
}
