import { type DemoRace } from '@/lib/races'

/** Separate the live race identity from the static good/bad demo identifiers. */
export type DashboardRace = Omit<DemoRace, 'id'> & { id: DemoRace['id'] | 'live' }

/** JSON contract returned by GET /api/analysis/[id]. */
export type LiveAnalysis = {
 id: string
 filename: string
 track: string
 engineClass: number
 resultStatus: 'scored' | 'partial'
 score: number
 paceBand: string
 worldRecordSeconds: number
 finalTimeSeconds: number
 finalTimeSource?: string | null
 lapTimesSeconds: [number, number, number]
 lapPerformanceScore: number | null
 coinManagementScore: number | null
 averageCoins: number
 coinCoverage: number
 fractionRaceAtTen: number
 firstTenSeconds: number
 longestTenSeconds: number
 belowFiveSeconds: number
 strongLossCandidates: number
 possibleCappedLosses: number
 ambiguousDecreases: number
 timingIsEstimate: boolean
 scoringWarning: string | null
 limitations: string[]
}

const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const positive = (value: unknown): value is number => finite(value) && value > 0
const nonnegative = (value: unknown): value is number => finite(value) && value >= 0
const fraction = (value: unknown): value is number => nonnegative(value) && value <= 1
const whole = (value: unknown): value is number => nonnegative(value) && Number.isInteger(value)

/** Reject incomplete results rather than silently backfilling the dashboard with demos. */
export function isDashboardReady(payload: unknown): payload is LiveAnalysis {
 if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return false
 const x = payload as Record<string, unknown>
 return typeof x.id === 'string' && /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(x.id)
  && typeof x.filename === 'string' && x.filename.length > 0
  && x.track === 'SNES Rainbow Road' && x.engineClass === 150
  && x.resultStatus === 'scored' && finite(x.score) && x.score >= 0 && x.score <= 100
  && typeof x.paceBand === 'string' && x.paceBand.length > 0
  && positive(x.worldRecordSeconds) && positive(x.finalTimeSeconds)
  && Array.isArray(x.lapTimesSeconds) && x.lapTimesSeconds.length === 3 && x.lapTimesSeconds.every(positive)
  && finite(x.averageCoins) && x.averageCoins >= 0 && x.averageCoins <= 10
  && fraction(x.coinCoverage) && fraction(x.fractionRaceAtTen)
  && nonnegative(x.firstTenSeconds) && nonnegative(x.longestTenSeconds) && nonnegative(x.belowFiveSeconds)
  && whole(x.strongLossCandidates) && whole(x.possibleCappedLosses) && whole(x.ambiguousDecreases)
  && (x.lapPerformanceScore === null || (finite(x.lapPerformanceScore) && x.lapPerformanceScore >= 0 && x.lapPerformanceScore <= 100))
  && (x.coinManagementScore === null || (finite(x.coinManagementScore) && x.coinManagementScore >= 0 && x.coinManagementScore <= 100))
  && typeof x.timingIsEstimate === 'boolean'
  && (x.scoringWarning === null || typeof x.scoringWarning === 'string')
 }

/** Every displayed telemetry field comes directly from the saved analysis result. */
export function toDashboardRace(result: LiveAnalysis): DashboardRace {
 return {
  id: 'live',
  filename: result.filename,
  score: result.score,
  pace: result.paceBand,
  totalSeconds: result.finalTimeSeconds,
  laps: [...result.lapTimesSeconds],
  averageCoins: result.averageCoins,
  maxCoinPercent: Math.round(result.fractionRaceAtTen * 1000) / 10,
  firstTenSeconds: result.firstTenSeconds,
  longestTenSeconds: result.longestTenSeconds,
  belowFiveSeconds: result.belowFiveSeconds,
  coverage: Math.round(result.coinCoverage * 1000) / 10,
  strongLosses: result.strongLossCandidates,
  cappedLosses: result.possibleCappedLosses,
  ambiguousLosses: result.ambiguousDecreases,
  lapScore: result.lapPerformanceScore === null ? undefined : result.lapPerformanceScore,
  coinScore: result.coinManagementScore === null ? undefined : result.coinManagementScore,
 }
}
