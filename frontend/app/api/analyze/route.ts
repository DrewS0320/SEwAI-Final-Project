import { NextRequest, NextResponse } from 'next/server'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { randomUUID } from 'node:crypto'
import { access, mkdir, readFile, writeFile } from 'node:fs/promises'
import { existsSync } from 'node:fs'
import path from 'node:path'

// Local development integration. Requires a persistent, writable Node.js host,
// the project's Python venv/OpenCV dependencies, and the .NET SDK.
export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const execFileAsync = promisify(execFile)
const MAX_BYTES = 250 * 1024 * 1024
const PROCESS_TIMEOUT_MS = 12 * 60 * 1000
const ALLOWED_EXTENSIONS = new Set(['.mp4', '.mov', '.mkv', '.avi'])

type JsonMap = Record<string, unknown>

function object(value: unknown): JsonMap {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? value as JsonMap
    : {}
}

function number(value: unknown): number | null {
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

function integer(value: unknown): number | null {
  const v = number(value)
  return v !== null && Number.isInteger(v) ? v : null
}

function getPython(root: string): string {
  if (process.env.KART_PYTHON) return process.env.KART_PYTHON
  const local = process.platform === 'win32'
    ? path.join(root, '.venv', 'Scripts', 'python.exe')
    : path.join(root, '.venv', 'bin', 'python')
  return existsSync(local) ? local : process.platform === 'win32' ? 'python' : 'python3'
}

function parseNumber(text: string, label: string): number | null {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = text.match(new RegExp(`^${escaped}:\\s*([0-9]+(?:\\.[0-9]+)?)`, 'im'))
  return match ? Number(match[1]) : null
}

function parseTime(s: string): number | null {
  const match = s.match(/^(\d+):(\d{2})\.(\d{3})$/)
  if (!match || Number(match[2]) > 59) return null
  return Number(match[1]) * 60 + Number(match[2]) + Number(match[3]) / 1000
}

function scoreFields(stdout: string) {
  const score = stdout.match(/PROVISIONAL PERFORMANCE INDEX:\s*(\d+)\s*\/\s*100/i)
  const band = stdout.match(/^Pace Band:\s*(.+)$/im)
  const wr = stdout.match(/^World Record:\s*([^\r\n]+)$/im)
  const lap = stdout.match(/^Lap Performance\s*\(\s*\d+%\s*\):\s*([\d.]+)/im)
  return {
    overallScore: score ? Number(score[1]) : null,
    paceBand: band?.[1]?.trim() ?? null,
    worldRecordSeconds: wr ? parseTime(wr[1].trim()) : null,
    paceBenchmarkScore: parseNumber(stdout, 'Benchmark Score'),
    lapConsistencyScore: parseNumber(stdout, 'Lap Consistency'),
    lapPerformanceScore: lap ? Number(lap[1]) : null,
    coinManagementScore: parseNumber(stdout, 'Adjusted Coin Score'),
  }
}

export async function POST(request: NextRequest) {
  let id: string | null = null
  try {
    const contentLength = Number(request.headers.get('content-length'))
    if (Number.isFinite(contentLength) && contentLength > MAX_BYTES + 1024 * 1024) {
      return NextResponse.json({ error: 'Video exceeds 250 MB.' }, { status: 413 })
    }

    const form = await request.formData()
    const video = form.get('video')
    if (!(video instanceof File)) {
      return NextResponse.json({ error: 'Choose a video file first.' }, { status: 400 })
    }
    if (video.size === 0 || video.size > MAX_BYTES) {
      return NextResponse.json({ error: 'Video must be between 1 byte and 250 MB.' }, { status: 413 })
    }
    const originalName = video.name.replaceAll('\\', '/').split('/').pop() || 'video.mp4'
    const extension = path.extname(originalName).toLowerCase()
    if (!ALLOWED_EXTENSIONS.has(extension)) {
      return NextResponse.json({ error: 'Please use an MP4, MOV, MKV, or AVI video.' }, { status: 400 })
    }
    const finalTime = String(form.get('finalTime') ?? '').trim()
    if (finalTime && !/^\d{1,2}:[0-5]\d\.\d{3}$/.test(finalTime)) {
      return NextResponse.json({ error: 'Official time must be in M:SS.mmm format, for example 1:39.606.' }, { status: 400 })
    }

    // Running `npm run dev` from frontend/ means this is the repo root.
    const root = path.resolve(process.cwd(), '..')
    const analysisDir = path.join(root, 'video-analysis')
    const backendDir = path.join(root, 'backend')
    const required = ['analyzer.py', 'rois.json', 'go_reference.png', 'finish_reference.png']
    for (const file of required) await access(path.join(analysisDir, file))
    await access(backendDir)

    id = randomUUID()
    const outputDir = path.join(analysisDir, 'results', 'uploads', id)
    await mkdir(outputDir, { recursive: true })
    const inputPath = path.join(outputDir, `uploaded${extension}`)
    await writeFile(inputPath, Buffer.from(await video.arrayBuffer()))

    const pythonArgs = [
      path.join(analysisDir, 'analyzer.py'), 'analyze', inputPath,
      '--rois', path.join(analysisDir, 'rois.json'),
      '--out', outputDir,
      '--every', '0.2',
      '--auto-boundaries',
      '--go-reference', path.join(analysisDir, 'go_reference.png'),
      '--finish-reference', path.join(analysisDir, 'finish_reference.png'),
    ]
    if (finalTime) pythonArgs.push('--final-time', finalTime)

    await execFileAsync(getPython(root), pythonArgs, {
      cwd: analysisDir, timeout: PROCESS_TIMEOUT_MS, maxBuffer: 4 * 1024 * 1024,
      windowsHide: true,
    })

    const analysisPath = path.join(outputDir, 'score_input.json')
    const analysis = object(JSON.parse(await readFile(analysisPath, 'utf8')))
    // Preserve the user's recognizable name in the exported analyzer JSON.
    analysis.video_name = originalName
    await writeFile(analysisPath, JSON.stringify(analysis, null, 2), 'utf8')
    const metricsPath = path.join(outputDir, 'race_metrics.json')
    const advanced = existsSync(metricsPath)
      ? object(JSON.parse(await readFile(metricsPath, 'utf8'))) : {}
    const advancedCoins = object(advanced.coin_metrics)
    const coinV4 = object(analysis.coin_v4)
    const losses = object(analysis.coin_loss_detection)

    let scoringWarning: string | null = null
    let scoreOutput = ''
    try {
      const result = await execFileAsync('dotnet', [
        'run', '--no-launch-profile', '--project', backendDir,
        '--', analysisPath, '150',
      ], {
        cwd: root, timeout: PROCESS_TIMEOUT_MS, maxBuffer: 4 * 1024 * 1024,
        windowsHide: true,
      })
      scoreOutput = result.stdout
    } catch (error) {
      // Don't invent a score if OCR failed to detect enough laps, or .NET failed.
      const problem = error as Error & { stderr?: string; stdout?: string }
      scoreOutput = problem.stdout ?? ''
      scoringWarning = (problem.stderr || problem.message || 'C# scoring unavailable').trim().slice(0, 1200)
    }

    const computed = scoreFields(scoreOutput)
    if (computed.overallScore === null && !scoringWarning) {
      scoringWarning = 'The scorer did not return a provisional performance index.'
    }
    const laps = Array.isArray(analysis.lap_times_seconds_approx)
      ? analysis.lap_times_seconds_approx.map(number)
      : []

    const result = {
      id,
      filename: originalName,
      mode: 'TimeTrial',
      track: typeof analysis.track === 'string' ? analysis.track : 'SNES Rainbow Road',
      engineClass: 150,
      resultStatus: computed.overallScore === null ? 'partial' : 'scored',
      score: computed.overallScore,
      paceBand: computed.paceBand,
      worldRecordSeconds: computed.worldRecordSeconds,
      paceBenchmarkScore: computed.paceBenchmarkScore,
      lapConsistencyScore: computed.lapConsistencyScore,
      lapPerformanceScore: computed.lapPerformanceScore,
      coinManagementScore: computed.coinManagementScore,
      finalTimeSeconds: number(analysis.final_time_seconds),
      finalTimeSource: analysis.final_time_source,
      lapTimesSeconds: laps,
      averageCoins: number(analysis.average_coins),
      coinCoverage: number(coinV4.time_coverage_fraction),
      fractionRaceAtTen: number(coinV4.fraction_of_race_time_assigned_10_coins),
      timeAtTenSeconds: number(coinV4.time_at_10_coins_seconds_estimated),
      firstTenSeconds: number(advancedCoins.time_to_first_observed_10_coins_seconds_estimate),
      longestTenSeconds: number(advancedCoins.longest_observed_10_coin_streak_seconds_estimate),
      belowFiveSeconds: number(advancedCoins.time_below_5_coins_seconds_estimate),
      strongLossCandidates: integer(losses.strong_candidates),
      possibleCappedLosses: integer(losses.possible_capped_losses),
      ambiguousDecreases: integer(losses.ambiguous_decreases),
      scoringWarning,
      timingIsEstimate: analysis.final_time_source !== 'user_verified_manual',
      limitations: Array.isArray(analysis.limitations)
        ? analysis.limitations.filter((s): s is string => typeof s === 'string') : [],
    }
    await writeFile(path.join(outputDir, 'result.json'), JSON.stringify(result, null, 2), 'utf8')
    return NextResponse.json({ id, resultStatus: result.resultStatus })
  } catch (error) {
    const problem = error as Error & { stderr?: string; stdout?: string }
    // Show just the last useful error lines, not a stack trace or local paths.
    const details = (problem.stderr || problem.message || 'Analysis failed').trim()
    console.error('Mario Kart video analysis failed', { runId: id, error: details })
    const safeMessage = details.includes('Couldn\'t detect')
      ? 'Could not detect the GO or FINISH banner. This tool currently expects the calibrated SNES Rainbow Road capture layout.'
      : details.includes('ENOENT')
      ? 'Python, .NET, or a required analyzer file could not be found. Check the local setup.'
      : 'Video analysis failed. Check the Next.js terminal for details.'
    return NextResponse.json({ error: safeMessage, runId: id }, { status: 500 })
  }
}
