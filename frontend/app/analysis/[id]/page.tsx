'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'

type Result = {
  id: string
  filename: string
  track: string
  engineClass: number
  resultStatus: 'scored' | 'partial'
  score: number | null
  paceBand: string | null
  worldRecordSeconds: number | null
  paceBenchmarkScore: number | null
  lapConsistencyScore: number | null
  lapPerformanceScore: number | null
  coinManagementScore: number | null
  finalTimeSeconds: number | null
  finalTimeSource: string | null
  lapTimesSeconds: (number | null)[]
  averageCoins: number | null
  coinCoverage: number | null
  fractionRaceAtTen: number | null
  timeAtTenSeconds: number | null
  firstTenSeconds: number | null
  longestTenSeconds: number | null
  belowFiveSeconds: number | null
  strongLossCandidates: number | null
  possibleCappedLosses: number | null
  ambiguousDecreases: number | null
  scoringWarning: string | null
  timingIsEstimate: boolean
  limitations: string[]
}

function time(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return 'Not available'
  const minutes = Math.floor(value / 60)
  return `${minutes}:${(value - minutes * 60).toFixed(3).padStart(6, '0')}`
}
function decimal(value: number | null, digits = 2, unit = ''): string {
  return value === null || !Number.isFinite(value) ? 'Not available' : value.toFixed(digits) + unit
}
function percent(value: number | null): string {
  return value === null ? 'Not available' : decimal(value * 100, 1, '%')
}

export default function AnalysisResults() {
  const { id } = useParams<{ id: string }>()
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    fetch(`/api/analysis/${encodeURIComponent(id)}`, { cache: 'no-store' })
      .then(async response => {
        const payload = await response.json()
        if (!response.ok) throw new Error(payload.error || 'Unable to load result.')
        if (active) setResult(payload as Result)
      })
      .catch(problem => { if (active) setError(String(problem.message || problem)) })
    return () => { active = false }
  }, [id])

  const cell = { padding: '12px 14px', borderBottom: '1px solid #64748b44' }
  return (
    <main style={{ maxWidth: 980, padding: '24px', margin: '28px auto' }}>
      <nav style={{ display: 'flex', gap: 24 }}><Link href="/analysis">Dashboard</Link><Link href={"/analysis?analysis=" + encodeURIComponent(id)}>View styled dashboard</Link><Link href="/upload">Analyze another video</Link></nav>
      <h1>Video analysis results</h1>
      {error && <p role="alert" style={{ color: '#fb7185' }}>{error}</p>}
      {!result && !error && <p role="status">Loading saved analysis…</p>}
      {result && <>
        <p><strong>{result.track} · {result.engineClass}cc</strong> · {result.filename}</p>
        <section style={{ border: '1px solid #64748b55', padding: 20, borderRadius: 12, marginBottom: 20 }}>
          <h2>{result.score === null ? 'Score unavailable' : `${result.score}/100 – Provisional performance index`}</h2>
          <p>Pace classification: {result.paceBand || 'Not available'}</p>
          <p>Finish: <strong>{time(result.finalTimeSeconds)}</strong> {result.timingIsEstimate ? '(estimated from video)' : '(official time supplied)'}</p>
          <p>World record: {time(result.worldRecordSeconds)}</p>
          {result.scoringWarning && <p style={{ color: '#fbbf24' }}>Scoring warning: {result.scoringWarning}</p>}
        </section>
        <h2>Lap and coin analysis</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <tbody>
            {result.lapTimesSeconds.map((lap, index) => <tr key={index}><th style={cell}>Lap {index + 1}</th><td style={cell}>{time(lap)}</td></tr>)}
            <tr><th style={cell}>Average coins</th><td style={cell}>{decimal(result.averageCoins, 3)} / 10</td></tr>
            <tr><th style={cell}>Coin data coverage</th><td style={cell}>{percent(result.coinCoverage)}</td></tr>
            <tr><th style={cell}>Race duration at 10 coins</th><td style={cell}>{percent(result.fractionRaceAtTen)}</td></tr>
            <tr><th style={cell}>Time at 10 coins</th><td style={cell}>{decimal(result.timeAtTenSeconds, 2, ' s')}</td></tr>
            <tr><th style={cell}>Time to first 10 coins</th><td style={cell}>{decimal(result.firstTenSeconds, 2, ' s')}</td></tr>
            <tr><th style={cell}>Longest observed 10-coin streak</th><td style={cell}>{decimal(result.longestTenSeconds, 2, ' s')}</td></tr>
            <tr><th style={cell}>Time below 5 coins</th><td style={cell}>{decimal(result.belowFiveSeconds, 2, ' s')}</td></tr>
            <tr><th style={cell}>Strong coin-loss candidates</th><td style={cell}>{result.strongLossCandidates ?? 'Not available'}</td></tr>
            <tr><th style={cell}>Possible capped losses</th><td style={cell}>{result.possibleCappedLosses ?? 'Not available'}</td></tr>
            <tr><th style={cell}>Ambiguous decreases</th><td style={cell}>{result.ambiguousDecreases ?? 'Not available'}</td></tr>
          </tbody>
        </table>
        <h2>Measured-category scores</h2>
        <p>Lap performance: {decimal(result.lapPerformanceScore, 1, '/100')} · Coin management: {decimal(result.coinManagementScore, 1, '/100')}</p>
        <p>Coin-loss events are unverified candidates; lap times may be estimates.</p>
        <p><a href={`/api/analysis/${encodeURIComponent(id)}/raw`} download>Download source analysis JSON</a></p>
      </>}
    </main>
  )
}
