'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Activity, ArrowDownRight, ArrowRight, ArrowUpRight, BarChart3, Check, ChevronDown, CircleHelp, Clock3, Coins, FileVideo2, Flag, Gauge, LayoutDashboard, Lightbulb, Menu, MoreHorizontal, Plus, Upload, Zap } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { type DemoRace, formatTime, getRecommendations, races, WORLD_RECORD_SECONDS } from '@/lib/races'
import { type DashboardRace, type LiveAnalysis, isDashboardReady, toDashboardRace } from '@/lib/live-analysis'
import { type CoinPoint, demoCoinTimeline } from '@/lib/demo-timelines'

function Metric({ label, value, detail, icon: Icon, tone = 'cyan' }: { label: string; value: string; detail: string; icon: typeof Gauge; tone?: string }) {
  return <article className="metric-card"><div className="metric-top"><span>{label}</span><Icon className={`metric-icon ${tone}`} size={17}/></div><strong>{value}</strong><small>{detail}</small></article>
}

function Sidebar({ active = 'results' }: { active?: string }) {
  return <aside className="sidebar"><Link href="/" className="brand"><span className="brand-mark"><Gauge size={19}/></span><span>KART<span className="brand-accent">SCOPE</span><small>TIME TRIAL ANALYTICS</small></span></Link><div className="nav-label">WORKSPACE</div><nav className="side-nav"><Link className={active === 'results' ? 'selected' : ''} href="/"><LayoutDashboard size={17}/> Race analysis</Link><Link className={active === 'races' ? 'selected' : ''} href="/dashboard"><BarChart3 size={17}/> Demo races<span className="nav-count">02</span></Link><Link className={active === 'upload' ? 'selected' : ''} href="/upload"><Upload size={17}/> Analyze video</Link></nav><div className="sidebar-bottom"><div className="track-mini"><div className="track-line"/><span className="track-caption">CURRENT TRACK</span><strong>SNES Rainbow Road</strong><small>150cc · Time Trial</small></div><Link href="/scoring" className="help-link"><CircleHelp size={16}/> How scoring works</Link><div className="user-chip"><div className="avatar">MK</div><span><b>Demo workspace</b><small>Capstone preview</small></span><MoreHorizontal size={17}/></div></div></aside>
}

function Header({ race, onSelect, live }: { race: DashboardRace; onSelect: (id: DemoRace['id']) => void; live: boolean }) {
  return <header className="topbar"><div className="crumb"><span>ANALYSIS</span><span className="crumb-slash">/</span><b>Race results</b></div><div className="header-actions"><div className="demo-label"><span/> {live ? 'UPLOADED VIDEO' : 'DEMO DATA'}</div><label className="race-select-label" htmlFor="race-select">Race</label><div className="select-wrap"><select id="race-select" value={live ? "live" : race.id} onChange={e => onSelect(e.target.value as DemoRace['id'])}><option value="live" disabled={true} hidden={!live}>Uploaded race</option><option value="good">Good race</option><option value="bad">Bad race</option></select><ChevronDown size={14}/></div><Link className="upload-top" href="/upload"><Plus size={15}/> New analysis</Link></div></header>
}

function ScoreCard({ race, recordSeconds = WORLD_RECORD_SECONDS, timingIsEstimate = true }: { race: DashboardRace; recordSeconds?: number; timingIsEstimate?: boolean }) {
  const delta = race.totalSeconds - recordSeconds
  return <section className="hero-card">
    <div className="hero-glow"/>
    <div className="hero-main">
      <div className="eyebrow"><span className="live-dot"/> TIME TRIAL TELEMETRY <span className="eyebrow-divider">/</span> {race.filename}</div>
      <h1>SNES Rainbow Road <span>· 150cc</span></h1>
      <div className="hero-meta"><span><FileVideo2 size={14}/>{race.filename}</span><span><Clock3 size={14}/>{timingIsEstimate ? 'Estimated from video' : 'Official time supplied'}</span></div>
      <div className="score-layout">
        <div className="score-block"><div className="score-number">{race.score}<span>/100</span></div><div className="score-caption">OVERALL PERFORMANCE</div><div className="score-meter"><i style={{width:`${race.score}%`}}/></div></div>
        <div className="score-divider"/>
        <div className="result-details">
          <div><span>PACE CLASSIFICATION</span><b className={race.score >= 65 ? 'text-green' : 'text-orange'}><i className="status-dot"/>{race.pace}</b></div>
          <div><span>FINISH TIME</span><b className="mono finish-time">{formatTime(race.totalSeconds)}</b></div>
        </div>
      </div>
      <div className="hero-foot"><span><Flag size={13}/> PLAYER SPLITS ARE VIDEO-DERIVED ESTIMATES</span><span>WR · {formatTime(recordSeconds)} · backend reference</span></div>
    </div>
    <div className="hero-visual" aria-label="Original luminous rainbow road illustration">
      <div className="hero-visual-top"><span><i/> CIRCUIT VIEW</span><span>SNES / 150</span></div>
      <svg className="rainbow-road" viewBox="0 0 720 360" role="img" aria-labelledby="road-title">
        <title id="road-title">A glowing road winding through a field of stars</title>
        <defs>
          <linearGradient id="roadSpectrum" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#46eaff"/><stop offset=".22" stopColor="#477eff"/><stop offset=".42" stopColor="#b35bff"/><stop offset=".62" stopColor="#ff5cb8"/><stop offset=".8" stopColor="#ffb84c"/><stop offset="1" stopColor="#ffe86b"/></linearGradient>
          <linearGradient id="roadSurface" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#26324b"/><stop offset="1" stopColor="#10182b"/></linearGradient>
          <radialGradient id="roadAura"><stop stopColor="#8a58ff" stopOpacity=".32"/><stop offset="1" stopColor="#101528" stopOpacity="0"/></radialGradient>
          <filter id="roadGlow" x="-50%" y="-100%" width="200%" height="300%"><feGaussianBlur stdDeviation="12"/></filter>
        </defs>
        <ellipse cx="415" cy="185" rx="310" ry="170" fill="url(#roadAura)"/>
        <g className="hero-stars" fill="#e5efff"><circle cx="92" cy="71" r="1.5"/><circle cx="170" cy="123" r="1"/><circle cx="266" cy="47" r="1.3"/><circle cx="374" cy="83" r="1"/><circle cx="546" cy="54" r="1.5"/><circle cx="622" cy="128" r="1"/><circle cx="675" cy="81" r="1.3"/><circle cx="493" cy="161" r="1"/><circle cx="247" cy="200" r="1.2"/></g>
        <path d="M40 288 C135 267 175 226 243 224 C324 222 322 288 420 275 C510 263 515 192 599 170 C655 155 691 175 722 186" fill="none" stroke="#9a55ff" strokeWidth="60" strokeLinecap="round" opacity=".35" filter="url(#roadGlow)"/>
        <path d="M40 288 C135 267 175 226 243 224 C324 222 322 288 420 275 C510 263 515 192 599 170 C655 155 691 175 722 186" fill="none" stroke="#080d1b" strokeWidth="48" strokeLinecap="round"/>
        <path d="M40 288 C135 267 175 226 243 224 C324 222 322 288 420 275 C510 263 515 192 599 170 C655 155 691 175 722 186" fill="none" stroke="url(#roadSurface)" strokeWidth="39" strokeLinecap="round"/>
        <path d="M40 288 C135 267 175 226 243 224 C324 222 322 288 420 275 C510 263 515 192 599 170 C655 155 691 175 722 186" fill="none" stroke="url(#roadSpectrum)" strokeWidth="5" strokeLinecap="round"/>
        <path d="M45 302 C140 281 179 241 245 239 C320 237 321 303 418 290 C505 278 513 207 596 185 C649 171 689 190 718 201" fill="none" stroke="#edf6ff" strokeOpacity=".37" strokeWidth="1.5" strokeDasharray="5 9"/>
        <g transform="translate(533 147) rotate(-15)"><rect width="26" height="8" rx="2" fill="#eff8ff"/><path d="M4 0v8m6-8v8m6-8v8m6-8v8" stroke="#303c58" strokeWidth="3"/></g>
      </svg>
      <div className="hero-world-record"><span className="record-icon"><Flag size={14}/></span><div><small>WORLD RECORD</small><b className="mono">{formatTime(recordSeconds)}</b></div><span className="record-gap">+{formatTime(delta)}</span></div>
    </div>
  </section>
}

function LapChart({ race }: { race: DashboardRace }) {
 const data = race.laps.map((time, i) => ({ lap: `Lap ${i + 1}`, time, label: formatTime(time), color: time === Math.min(...race.laps) ? '#37d9e7' : '#536477' }))
 const best = Math.min(...race.laps), worst = Math.max(...race.laps)
 return <section className="panel lap-panel"><div className="panel-heading"><div><div className="section-kicker">PACE BREAKDOWN</div><h2>Lap performance</h2></div><button className="text-button" aria-label="Lap chart details"><MoreHorizontal size={18}/></button></div><div className="lap-summary"><div><small>FASTEST LAP</small><b className="mono">{formatTime(best)}</b><span className="positive"><ArrowDownRight size={13}/> Lap {race.laps.indexOf(best) + 1}</span></div><div><small>SLOWEST LAP</small><b className="mono">{formatTime(worst)}</b><span className="negative"><ArrowUpRight size={13}/> +{(worst - best).toFixed(3)}s</span></div><div><small>LAP SPREAD</small><b className="mono">{(Math.max(...race.laps) - Math.min(...race.laps)).toFixed(3)}s</b><span className="muted-text">fastest to slowest</span></div></div><div className="chart-area"><ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{top:20,right:12,left:-24,bottom:0}}><CartesianGrid stroke="#202b37" vertical={false}/><XAxis dataKey="lap" tick={{fill:'#77879a',fontSize:11}} axisLine={false} tickLine={false} dy={8}/><YAxis domain={[0, Math.ceil(worst / 10) * 10]} tick={{fill:'#647386',fontSize:10}} axisLine={false} tickLine={false} tickFormatter={v => `${v}s`}/><Tooltip cursor={{fill:'#ffffff08'}} contentStyle={{background:'#111a24',border:'1px solid #53627b',borderRadius:10,color:'#f4f8ff',boxShadow:'0 12px 30px #0009'}} labelStyle={{color:'#afc0d7',fontSize:12}} itemStyle={{color:'#f4f8ff',fontSize:13,fontWeight:700}} formatter={(v) => [`${Number(v).toFixed(3)}s`, 'Lap time']}/><Bar dataKey="time" radius={[5,5,0,0]} barSize={40}>{data.map((entry,i)=><Cell key={i} fill={entry.color}/>)}</Bar></BarChart></ResponsiveContainer></div><div className="chart-legend"><span><i className="legend-cyan"/> Fastest lap</span><span><i className="legend-muted"/> Other laps</span><span className="lap-foot-note">No world-record split data available</span></div></section>
}

function CoinTimeline({ analysisId, demoId }: { analysisId: string | null; demoId: DemoRace['id'] }) {
  const [status, setStatus] = useState<'loading' | 'ready' | 'missing'>(analysisId ? 'loading' : 'ready')
  const [livePoints, setLivePoints] = useState<CoinPoint[]>([])
  useEffect(() => {
    if (!analysisId) { setStatus('ready'); setLivePoints([]); return }
    const controller = new AbortController()
    setStatus('loading')
    setLivePoints([])
    fetch('/api/analysis/' + encodeURIComponent(analysisId) + '/timeline', { cache: 'no-store', signal: controller.signal })
      .then(async response => {
        const payload: unknown = await response.json()
        if (!response.ok) throw new Error('Timeline unavailable')
        if (!payload || typeof payload !== 'object' || !('points' in payload) || !Array.isArray(payload.points)) throw new Error('Invalid timeline')
        const points: CoinPoint[] = []
        for (const point of payload.points) {
          if (!point || typeof point !== 'object') continue
          const p = point as Record<string, unknown>
          if (typeof p.seconds !== 'number' || !Number.isFinite(p.seconds) || p.seconds < 0) continue
          const coins = typeof p.coins === 'number' && Number.isInteger(p.coins) && p.coins >= 0 && p.coins <= 10 ? p.coins : null
          points.push({ seconds: p.seconds, coins })
        }
        if (!points.length) throw new Error('Empty timeline')
        return points
      })
      .then(points => { if (!controller.signal.aborted) { setLivePoints(points); setStatus('ready') } })
      .catch(() => { if (!controller.signal.aborted) setStatus('missing') })
    return () => controller.abort()
  }, [analysisId])

  const points = analysisId ? livePoints : demoCoinTimeline[demoId]
  const available = status === 'ready' && points.length > 0
  return <div className="coin-timeline" style={{ marginTop: 18, padding: '12px 10px 8px', border: '1px solid #38475c', borderRadius: 10, background: '#0d1724' }}>
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 10 }}>
      <b style={{ fontSize: 12 }}>Coin count over time</b>
      <small style={{ color: '#94a3b8' }}>{analysisId ? 'Race telemetry · 0–10 coins' : 'Sampled demo telemetry'}</small>
    </div>
    {available ? <div style={{ width: '100%', height: 180 }} role="img" aria-label="Coin count over elapsed race time; straight lines visually connect known readings, including across unreadable intervals">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 8, right: 10, left: -24, bottom: 4 }}>
          <CartesianGrid stroke="#273749" vertical={false} strokeDasharray="3 5" />
          <XAxis dataKey="seconds" type="number" domain={[0, 'dataMax']} tick={{ fill: '#8296ad', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(value: number) => `${Math.round(value)}s`} />
          <YAxis type="number" domain={[0, 10]} ticks={[0, 2, 4, 6, 8, 10]} tick={{ fill: '#8296ad', fontSize: 10 }} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={{ background: '#101b2b', border: '1px solid #40526b', borderRadius: 8, color: '#eaf4ff' }} labelStyle={{ color: '#b9cee3' }} labelFormatter={(value) => `${Number(value).toFixed(1)} seconds`} formatter={(value) => [value === null || value === undefined ? 'Unreadable' : `${value} coins`, 'Coin count']} />
          <Line name="Coins" type="linear" dataKey="coins" stroke="#f5b544" strokeWidth={2.5} dot={false} connectNulls={true} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div> : <div role="status" style={{ padding: '20px 8px', fontSize: 12, color: '#94a3b8' }}>{status === 'loading' ? 'Loading coin timeline…' : 'Coin timeline unavailable for this saved race. Other analysis results are unaffected.'}</div>}
    <small style={{ display: 'block', color: '#879db2', marginTop: 5 }}>Line segments connect available readings for display, including across unreadable intervals. Intermediate values are not measurements; unresolved readings remain unknown, not zero. {analysisId ? 'Values are estimated from video frames.' : 'Demo timeline is downsampled from stored race measurements.'}</small>
  </div>
}

function CoinPanel({ race, live = false, analysisId = null }: { race: DashboardRace; live?: boolean; analysisId?: string | null }) {
 return <section className="panel coin-panel"><div className="panel-heading"><div><div className="section-kicker">COIN MANAGEMENT</div><h2>Coin economy</h2></div><span className="coverage-tag"><span/> {race.coverage}% coverage</span></div><div className="coin-big"><span className="coin-emblem"><Coins size={20}/></span><div><b>{race.averageCoins.toFixed(3)}</b><small>average coins</small></div><div className="coin-max"><span>AT MAX COINS</span><b>{race.maxCoinPercent}%</b><small>of full race duration</small></div></div><div className="coin-stats"><div><span>TIME TO 10 COINS</span><b>{race.firstTenSeconds.toFixed(2)}s</b></div><div><span>LONGEST 10-COIN STREAK</span><b>{race.longestTenSeconds.toFixed(2)}s</b></div><div><span>TIME BELOW 5 COINS</span><b>{race.belowFiveSeconds.toFixed(2)}s</b></div></div><CoinTimeline analysisId={analysisId} demoId={race.id === 'bad' ? 'bad' : 'good'} /><div className="event-summary"><div><span className="event-dot orange-dot"/>Strong loss candidates <b>{race.strongLosses}</b></div><div><span className="event-dot gray-dot"/>Possible capped losses <b>{race.cappedLosses}</b></div><div><span className="event-dot gray-dot"/>Ambiguous decreases <b>{race.ambiguousLosses}</b></div><small>Candidates are unconfirmed detections from video analysis.</small></div></section>
}

function Suggestions({ race }: { race: DashboardRace }) {
 return <section className="panel suggestions"><div className="panel-heading"><div><div className="section-kicker">NEXT SESSION</div><h2>Where to improve</h2></div><span className="spark-icon"><Lightbulb size={16}/></span></div><div className="tips-list">{getRecommendations({ ...race, id: race.id === 'live' ? 'good' : race.id }).slice(0,3).map((tip,i)=><article className="tip" key={tip.title}><span className={`tip-number ${tip.color}`}>{String(i+1).padStart(2,'0')}</span><div><b>{tip.title}</b><p>{tip.text}</p></div><ArrowRight size={15}/></article>)}</div><div className="suggestion-note"><Zap size={13}/> Recommendations use measured race data only</div></section>
}

/** Keep demo mode separate from uploaded analyses. URL changes are supported via popstate. */
export default function Home() {
 const [raceId, setRaceId] = useState<DemoRace['id']>('good')
 const [analysisId, setAnalysisId] = useState<string | null>(null)
 const [hydrated, setHydrated] = useState(false)
 const [liveResult, setLiveResult] = useState<LiveAnalysis | null>(null)
 const [liveError, setLiveError] = useState<string | null>(null)
 const [menuOpen, setMenuOpen] = useState(false)

 useEffect(() => {
  function readLocation() {
   const query = new URLSearchParams(window.location.search)
   setAnalysisId(query.get('analysis'))
   setRaceId(query.get('race') === 'bad' ? 'bad' : 'good')
   setHydrated(true)
  }
  readLocation()
  window.addEventListener('popstate', readLocation)
  return () => window.removeEventListener('popstate', readLocation)
 }, [])

 useEffect(() => {
  if (!analysisId) { setLiveResult(null); setLiveError(null); return }
  const controller = new AbortController()
  setLiveResult(null)
  setLiveError(null)
  if (!/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(analysisId)) {
   setLiveError('The analysis link contains an invalid ID.')
   return () => controller.abort()
  }
  fetch('/api/analysis/' + encodeURIComponent(analysisId), { cache: 'no-store', signal: controller.signal })
   .then(async response => {
    const payload: unknown = await response.json()
    if (!response.ok) {
     const message = payload && typeof payload === 'object' && 'error' in payload && typeof payload.error === 'string' ? payload.error : 'Saved analysis not found.'
     throw new Error(message)
    }
    if (!isDashboardReady(payload) || payload.id.toLowerCase() !== analysisId.toLowerCase()) {
     throw new Error('The saved result is incomplete or uses an unsupported track. The detailed results page can show available metrics.')
    }
    return payload
   })
   .then(result => { if (!controller.signal.aborted) setLiveResult(result) })
   .catch(error => { if (!controller.signal.aborted) setLiveError(error instanceof Error ? error.message : 'Unable to load analysis.') })
  return () => controller.abort()
 }, [analysisId])

 const isLive = Boolean(analysisId && liveResult && liveResult.id.toLowerCase() === analysisId.toLowerCase())
 const race: DashboardRace = isLive ? toDashboardRace(liveResult!) : races[raceId]
 const selectRace = (id: DemoRace['id']) => {
  window.history.pushState(null, '', '/?race=' + id)
  setRaceId(id)
  setAnalysisId(null)
  setLiveResult(null)
  setLiveError(null)
 }

 // Never show demo numbers in place of a missing, failed or in-progress upload.
 if (!hydrated || (analysisId && !isLive)) {
  return <div className="app-shell"><Sidebar/><main className="main-content"><div className="content-wrap"><div className="page-title"><div><div className="page-kicker">UPLOADED RACE</div><h2>{!hydrated || !liveError ? 'Loading race analysis…' : 'Analysis unavailable'}</h2><p role="status">{liveError || 'Reading saved video measurements.'}</p>{analysisId && liveError && <p><Link href={'/analysis/' + encodeURIComponent(analysisId)} className="primary-button">View available details</Link></p>}<p><Link href="/upload">Analyze another video</Link></p></div></div></div></main></div>
 }

 return <div className="app-shell"><Sidebar/><main className="main-content"><Header race={race} onSelect={selectRace} live={isLive}/><div className="mobile-title"><button onClick={()=>setMenuOpen(!menuOpen)} aria-label="Toggle navigation"><Menu size={20}/></button><b>KartScope</b>{menuOpen && <div className="mobile-menu"><Link href="/">Race analysis</Link><Link href="/dashboard">Demo races</Link><Link href="/upload">Analyze video</Link><Link href="/scoring">Scoring</Link></div>}</div><div className="content-wrap"><div className="page-title"><div><div className="page-kicker">YOUR TELEMETRY, DECODED</div><h2>Race analysis</h2><p>{isLive ? 'Measurements from your uploaded time trial.' : 'Turn every lap into your next breakthrough.'}</p></div><Link href="/upload" className="primary-button"><Plus size={16}/> Analyze a race</Link></div><ScoreCard race={race} recordSeconds={isLive ? liveResult!.worldRecordSeconds : undefined} timingIsEstimate={isLive ? liveResult!.timingIsEstimate : true}/><div className="race-flow" aria-label="Analysis sections"><span className="flow-active"><i>01</i> RACE OVERVIEW</span><b/><span><i>02</i> LAP TELEMETRY</span><b/><span><i>03</i> COIN CONTROL</span><b/><span><i>04</i> NEXT SESSION</span></div><div className="section-title-row"><div><span className="section-kicker">PERFORMANCE SNAPSHOT</span><h2>At a glance</h2></div><span className="data-chip"><span/> ANALYSIS COMPLETE</span></div><div className="metrics-grid"><Metric label="Lap performance" value={race.lapScore !== undefined ? race.lapScore.toFixed(1) : '—'} detail={race.lapScore !== undefined ? 'Provisional C# category score' : 'Subscore unavailable'} icon={Activity} tone="blue"/><Metric label="Coin management" value={race.coinScore !== undefined ? race.coinScore.toFixed(1) : '—'} detail={race.coinScore !== undefined ? 'Provisional C# category score' : 'Subscore unavailable'} icon={Coins} tone="orange"/><Metric label="Average coins" value={race.averageCoins.toFixed(2)} detail={`${race.maxCoinPercent}% of full race at 10`} icon={Coins} tone="orange"/><Metric label="Coin data coverage" value={`${race.coverage}%`} detail="OCR-observed race duration" icon={BarChart3} tone="green"/><Metric label="Loss candidates" value={`${race.strongLosses}`} detail="unconfirmed detections" icon={ArrowDownRight} tone="orange"/></div><div className="analytics-grid"><LapChart race={race}/><CoinPanel race={race} live={isLive} analysisId={isLive ? analysisId : null}/></div><Suggestions race={race}/>{isLive && <section className="panel suggestions"><div className="panel-heading"><div><div className="section-kicker">VIDEO ANALYSIS</div><h2>Measurement notes</h2></div></div><p>Lap splits and coin measurements are video-derived estimates. Coin-loss detections are unverified candidates, not confirmed hits.</p>{liveResult!.scoringWarning && <p role="alert">Scoring warning: {liveResult!.scoringWarning}</p>}<p style={{marginTop:14}}><a href={'/api/analysis/' + encodeURIComponent(analysisId!) + '/raw'} download>Download source analysis JSON</a></p><p><Link href={'/analysis/' + encodeURIComponent(analysisId!)}>View detailed results</Link></p></section>}<footer className="footer-note"><span>KARTSCOPE <i>·</i> {isLive ? 'LOCAL VIDEO ANALYSIS' : 'CAPSTONE DEMONSTRATION'}</span><span>Validated scope: SNES Rainbow Road · 150cc <Link href="/scoring">Scoring methodology <ArrowRight size={12}/></Link></span></footer></div></main></div>
}
