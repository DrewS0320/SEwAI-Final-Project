import { NextResponse } from 'next/server'
import { readFile, stat } from 'node:fs/promises'
import path from 'node:path'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

/** Return observed/estimated coin states; never map unreadable readings to zero. */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  if (!/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(id)) {
    return NextResponse.json({ error: 'Invalid analysis ID.' }, { status: 400 })
  }
  const base = path.resolve(process.cwd(), '..', 'video-analysis', 'results', 'uploads', id)
  try {
    // Require a completed upload. Do not expose arbitrary result-directory files.
    await stat(path.join(base, 'result.json'))
    const file = path.join(base, 'race_metrics.json')
    const metadata = await stat(file)
    if (metadata.size > 8 * 1024 * 1024) {
      return NextResponse.json({ error: 'Timeline exceeds the supported size.' }, { status: 413 })
    }
    const payload: unknown = JSON.parse(await readFile(file, 'utf8'))
    const record = payload && typeof payload === 'object' && !Array.isArray(payload)
      ? payload as Record<string, unknown> : {}
    const items = record.coin_timeline
    if (!Array.isArray(items) || items.length === 0 || items.length > 10000) {
      return NextResponse.json({ error: 'No coin timeline available for this analysis.' }, { status: 422 })
    }
    const points: { seconds: number; coins: number | null; source: string }[] = []
    for (const item of items) {
      if (!item || typeof item !== 'object' || Array.isArray(item)) continue
      const data = item as Record<string, unknown>
      const seconds = data.race_elapsed_seconds
      if (typeof seconds !== 'number' || !Number.isFinite(seconds) || seconds < 0) continue
      const rawCoins = data.coins
      const coins = typeof rawCoins === 'number' && Number.isInteger(rawCoins) && rawCoins >= 0 && rawCoins <= 10
        ? rawCoins : null
      if (points.length > 0 && seconds <= points[points.length - 1].seconds) continue
      points.push({ seconds, coins, source: typeof data.source === 'string' ? data.source.slice(0, 60) : 'unspecified' })
    }
    if (!points.length) return NextResponse.json({ error: 'Timeline contains no valid timestamps.' }, { status: 422 })
    return NextResponse.json({ points }, { headers: { 'Cache-Control': 'no-store' } })
  } catch {
    return NextResponse.json({ error: 'Coin timeline not found for this analysis.' }, { status: 404 })
  }
}
