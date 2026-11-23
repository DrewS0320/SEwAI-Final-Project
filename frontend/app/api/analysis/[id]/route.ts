import { NextResponse } from 'next/server'
import { readFile } from 'node:fs/promises'
import path from 'node:path'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

function validId(id: string) {
  return /^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(id)
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  if (!validId(id)) return NextResponse.json({ error: 'Invalid analysis ID.' }, { status: 400 })
  const file = path.resolve(process.cwd(), '..', 'video-analysis', 'results', 'uploads', id, 'result.json')
  try {
    const data = JSON.parse(await readFile(file, 'utf8'))
    return NextResponse.json(data, { headers: { 'Cache-Control': 'no-store' } })
  } catch {
    return NextResponse.json({ error: 'Analysis not found.' }, { status: 404 })
  }
}
