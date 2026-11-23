import { readFile } from 'node:fs/promises'
import path from 'node:path'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params
  if (!/^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$/i.test(id)) {
    return new Response('Invalid analysis ID.', { status: 400 })
  }
  const file = path.resolve(process.cwd(), '..', 'video-analysis', 'results', 'uploads', id, 'score_input.json')
  try {
    return new Response(await readFile(file), {
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Content-Disposition': `attachment; filename="score_input_${id}.json"`,
        'Cache-Control': 'no-store',
      },
    })
  } catch {
    return new Response('Analysis not found.', { status: 404 })
  }
}
