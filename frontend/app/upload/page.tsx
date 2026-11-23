'use client'

import { useState, type FormEvent } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  ArrowLeft, ArrowRight, BarChart3, CheckCircle2, ChevronRight,
  CircleHelp, Clock3, FileVideo2, Flag, Gauge, LayoutDashboard,
  LoaderCircle, MoreHorizontal, ShieldCheck, Upload, Video, XCircle,
} from 'lucide-react'
import styles from './upload.module.css'

const MAX_VIDEO_BYTES = 250 * 1024 * 1024
const ALLOWED_EXTENSIONS = /\.(mp4|mov|mkv|avi)$/i

function Sidebar() {
  return (
    <aside className="sidebar">
      <Link href="/" className="brand">
        <span className="brand-mark"><Gauge size={19}/></span>
        <span>KART<span className="brand-accent">SCOPE</span><small>TIME TRIAL ANALYTICS</small></span>
      </Link>
      <div className="nav-label">WORKSPACE</div>
      <nav className="side-nav">
        <Link href="/"><LayoutDashboard size={17}/> Race analysis</Link>
        <Link href="/dashboard"><BarChart3 size={17}/> Demo races<span className="nav-count">02</span></Link>
        <Link className="selected" href="/upload"><Upload size={17}/> Analyze video</Link>
      </nav>
      <div className="sidebar-bottom">
        <div className="track-mini">
          <div className="track-line"/>
          <span className="track-caption">CURRENT TRACK</span>
          <strong>SNES Rainbow Road</strong>
          <small>150cc · Time Trial</small>
        </div>
        <Link href="/scoring" className="help-link"><CircleHelp size={16}/> How scoring works</Link>
        <div className="user-chip"><div className="avatar">MK</div><span><b>Demo workspace</b><small>Capstone preview</small></span><MoreHorizontal size={17}/></div>
      </div>
    </aside>
  )
}

function formatBytes(bytes: number): string {
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function UploadRace() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [officialTime, setOfficialTime] = useState('')
  const [working, setWorking] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')

  function selectVideo(video: File | null) {
    if (!video || working) return
    setError('')
    if (!ALLOWED_EXTENSIONS.test(video.name)) {
      setFile(null)
      setError('Please choose an MP4, MOV, MKV, or AVI recording.')
      return
    }
    if (video.size > MAX_VIDEO_BYTES) {
      setFile(null)
      setError(`This recording is ${formatBytes(video.size)}. The current limit is 250 MB.`)
      return
    }
    if (video.size === 0) {
      setFile(null)
      setError('This video file is empty. Please choose a playable recording.')
      return
    }
    setFile(video)
  }

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file || working) return
    setWorking(true)
    setError('')
    const form = new FormData()
    form.append('video', file)
    if (officialTime.trim()) form.append('finalTime', officialTime.trim())
    try {
      const response = await fetch('/api/analyze', { method: 'POST', body: form })
      const payload = await response.json()
      if (!response.ok || typeof payload.id !== 'string') {
        throw new Error(payload.error || 'Analysis failed.')
      }
      router.push(`/?analysis=${encodeURIComponent(payload.id)}`)
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'Analysis failed.')
    } finally {
      setWorking(false)
    }
  }

  return (
    <div className="app-shell">
      <Sidebar/>
      <main className="main-content">
        <header className="topbar">
          <div className="crumb"><span>ANALYSIS</span><span className="crumb-slash">/</span><b>Analyze video</b></div>
          <div className={styles.headerRight}><span className={styles.localDot}/> LOCAL PROCESSING</div>
        </header>

        <div className="content-wrap">
          <div className="page-title">
            <div>
              <div className="page-kicker">YOUR NEXT BREAKTHROUGH STARTS HERE</div>
              <h2>Analyze a race</h2>
              <p>Turn your Time Trial recording into actionable racing insights.</p>
            </div>
            <Link href="/" className={styles.backLink}><ArrowLeft size={16}/> Back to dashboard</Link>
          </div>

          <div className={styles.layout}>
            <section className={styles.formPanel} aria-labelledby="upload-heading">
              <div className={styles.panelTop}>
                <div className={styles.iconSquare}><Video size={20}/></div>
                <div>
                  <span className={styles.kicker}>VIDEO INPUT</span>
                  <h3 id="upload-heading">Upload your gameplay</h3>
                  <p>SNES Rainbow Road <span className={styles.dotSeparator}>·</span> 150cc <span className={styles.dotSeparator}>·</span> Time Trial</p>
                </div>
                <span className={styles.stepNumber}>01 / 02</span>
              </div>

              <form onSubmit={analyze} className={styles.form}>
                <label
                  htmlFor="race-video"
                  className={`${styles.dropZone} ${dragging ? styles.dragActive : ''} ${file ? styles.fileChosen : ''} ${working ? styles.dropDisabled : ''}`}
                  onDragOver={event => { event.preventDefault(); if (!working) setDragging(true) }}
                  onDragLeave={event => { event.preventDefault(); setDragging(false) }}
                  onDrop={event => {
                    event.preventDefault()
                    setDragging(false)
                    selectVideo(event.dataTransfer.files[0] ?? null)
                  }}
                >
                  <input
                    id="race-video"
                    className={styles.fileInput}
                    type="file"
                    accept=".mp4,.mov,.mkv,.avi,video/*"
                    required={!file}
                    disabled={working}
                    onChange={event => selectVideo(event.target.files?.[0] ?? null)}
                  />
                  <span className={styles.uploadIcon}>{file ? <FileVideo2 size={27}/> : <Upload size={27}/>}</span>
                  {file ? (
                    <>
                      <strong className={styles.filename}>{file.name}</strong>
                      <span className={styles.dropHint}>{formatBytes(file.size)} <span className={styles.dotSeparator}>·</span> Ready to analyze</span>
                      <span className={styles.browse}>Choose a different file</span>
                    </>
                  ) : (
                    <>
                      <strong>{dragging ? 'Drop your recording here' : 'Drop your race video here'}</strong>
                      <span className={styles.dropHint}>or select a file from your computer</span>
                      <span className={styles.browse}>Browse files <ChevronRight size={15}/></span>
                    </>
                  )}
                  <small>MP4, MOV, MKV, AVI <span className={styles.dotSeparator}>·</span> Maximum 250 MB</small>
                </label>

                <div className={styles.inputGroup}>
                  <div className={styles.labelRow}>
                    <label htmlFor="official-time">Official finishing time <span>(optional)</span></label>
                    <span className={styles.optional}>EXTRA ACCURACY</span>
                  </div>
                  <div className={styles.timeField}>
                    <Clock3 size={17}/>
                    <input
                      id="official-time"
                      type="text"
                      placeholder="1:39.606"
                      value={officialTime}
                      onChange={event => setOfficialTime(event.target.value)}
                      disabled={working}
                      autoComplete="off"
                    />
                  </div>
                  <p>Enter the time shown by the game if available. Otherwise, we estimate it from the recording.</p>
                </div>

                {error && <div className={styles.error} role="alert"><XCircle size={18}/><span>{error}</span></div>}
                {working && <div className={styles.processing} role="status"><LoaderCircle size={18} className={styles.spinner}/><div><strong>Analyzing your race...</strong><span>Detecting GO/FINISH, reading coins and laps, and calculating the performance score. Keep this tab open.</span></div></div>}

                <button className={styles.submit} type="submit" disabled={!file || working}>
                  {working ? <><LoaderCircle size={18} className={styles.spinner}/> Processing video</> : <><BarChart3 size={18}/> Analyze race <ArrowRight size={18}/></>}
                </button>
              </form>
            </section>

            <aside className={styles.infoColumn} aria-label="Analysis information">
              <section className={styles.infoCard}>
                <span className={styles.kicker}>HOW IT WORKS</span>
                <h3>From video to insight</h3>
                <div className={styles.processSteps}>
                  <div><span className={styles.processIcon}><Upload size={18}/></span><div><strong>Upload footage</strong><p>A complete Time Trial with visible GO and FINISH banners.</p></div></div>
                  <div><span className={styles.processIcon}><Gauge size={18}/></span><div><strong>Extract telemetry</strong><p>Python identifies lap transitions and coin counts throughout the race.</p></div></div>
                  <div><span className={styles.processIcon}><BarChart3 size={18}/></span><div><strong>Review performance</strong><p>See video-derived results and provisional scoring in your dashboard.</p></div></div>
                </div>
              </section>
              <section className={styles.scopeCard}>
                <div className={styles.scopeHeading}><ShieldCheck size={18}/><strong>Supported analysis</strong></div>
                <div><CheckCircle2 size={15}/> SNES Rainbow Road / 150cc</div>
                <div><CheckCircle2 size={15}/> Lap timing and coin management</div>
                <div><CheckCircle2 size={15}/> Saved results and raw JSON</div>
                <p>Processing runs locally on this computer. Some readings are estimates and coin-loss events are unverified candidates.</p>
              </section>
            </aside>
          </div>
          <footer className={styles.footer}>
            <span>KARTSCOPE <i>·</i> LOCAL VIDEO ANALYSIS</span>
            <Link href="/scoring">Scoring methodology <Flag size={12}/></Link>
          </footer>
        </div>
      </main>
    </div>
  )
}
