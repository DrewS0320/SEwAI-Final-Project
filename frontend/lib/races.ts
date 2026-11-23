export type DemoRace = {
  id: 'good' | 'bad'
  filename: string
  score: number
  pace: string
  totalSeconds: number
  laps: number[]
  averageCoins: number
  maxCoinPercent: number
  firstTenSeconds: number
  longestTenSeconds: number
  belowFiveSeconds: number
  coverage: number
  strongLosses: number
  cappedLosses: number
  ambiguousLosses: number
  lapScore?: number
  coinScore?: number
}

export const races: Record<DemoRace['id'], DemoRace> = {
  good: {
    id: 'good', filename: 'good_race.mp4', score: 85, pace: 'Advanced', totalSeconds: 99.736,
    laps: [35.4, 32.019, 32.317], averageCoins: 8.143, maxCoinPercent: 67.2,
    firstTenSeconds: 31.82, longestTenSeconds: 52.7, belowFiveSeconds: 13.42,
    coverage: 97.41, strongLosses: 0, cappedLosses: 0, ambiguousLosses: 0,
    lapScore: 86.6, coinScore: 81.4,
  },
  bad: {
    id: 'bad', filename: 'bad_race.mp4', score: 42, pace: 'Entry-Level', totalSeconds: 139.142,
    laps: [45.054, 46.349, 47.739], averageCoins: 3.372, maxCoinPercent: 4.3,
    firstTenSeconds: 75.19, longestTenSeconds: 5.97, belowFiveSeconds: 82.25,
    coverage: 88.13, strongLosses: 3, cappedLosses: 1, ambiguousLosses: 2,
    lapScore: 51.1, coinScore: 23.7,
  },
}

export const WORLD_RECORD_SECONDS = 85.117
export const formatTime = (seconds: number) => {
  const minutes = Math.floor(seconds / 60)
  const remainder = seconds - minutes * 60
  return `${minutes}:${remainder.toFixed(3).padStart(6, '0')}`
}

export function getRecommendations(race: DemoRace) {
  const tips: { title: string; text: string; color: string }[] = []
  if (race.averageCoins < 6) tips.push({ title: 'Build your coin economy', text: 'Your average is below 6 coins. Prioritize early pickups and avoid giving away coins where possible.', color: 'orange' })
  if (race.firstTenSeconds > 45) tips.push({ title: 'Reach 10 coins sooner', text: `It took ${race.firstTenSeconds.toFixed(1)}s to first observe 10 coins. Early collection helps maximize top-speed time.`, color: 'blue' })
  if (race.laps[2] - race.laps[0] > 2) tips.push({ title: 'Stabilize lap pace', text: 'Your lap times trend slower. Work toward repeating your best pace across all three laps.', color: 'purple' })
  else if (Math.max(...race.laps) - Math.min(...race.laps) > 2.5) tips.push({ title: 'Tighten lap consistency', text: `Your fastest-to-slowest lap spread is ${(Math.max(...race.laps) - Math.min(...race.laps)).toFixed(3)}s. Aim to bring each lap closer to your best split.`, color: 'purple' })
  if (race.maxCoinPercent < 75) tips.push({ title: 'Extend time at 10 coins', text: `${race.maxCoinPercent}% of the full race duration was at the 10-coin cap. Earlier collection could increase time spent at maximum coins.`, color: 'orange' })
  if (race.totalSeconds - WORLD_RECORD_SECONDS > 10) tips.push({ title: 'Close the pace gap', text: `The estimated race is ${formatTime(race.totalSeconds - WORLD_RECORD_SECONDS)} behind the stored world-record total.`, color: 'blue' })
  if (race.strongLosses > 0) tips.push({ title: 'Review possible coin-loss moments', text: `${race.strongLosses} strong candidate${race.strongLosses === 1 ? '' : 's'} detected. These are unconfirmed video-analysis candidates, not verified mistakes.`, color: 'orange' })
  if (!tips.length) tips.push({ title: 'Keep your coin lead', text: 'Strong coin-loss candidates were not detected. Continue building coins early and protecting your pace.', color: 'green' })
  return tips
}
