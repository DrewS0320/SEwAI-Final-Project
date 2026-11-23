'use client'

import { useState } from 'react'
import { Film, Play } from 'lucide-react'

type RaceVideoProps = {
  src: string
  title: string
  preview?: boolean
}

export default function RaceVideo({ src, title, preview = false }: RaceVideoProps) {
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(false)
  return (
    <div className={`race-video ${preview ? 'race-video-preview' : ''}`}>
      {!ready && (
        <div className="race-video-fallback" aria-hidden={ready}>
          <span className="race-video-orbit"/>
          <span className="race-video-track"/>
          <div className="race-video-message">
            {preview ? <Play size={21}/> : <Film size={22}/>}
            <strong>{failed ? 'Gameplay clip not installed' : 'Rainbow Road gameplay'}</strong>
            <small>{failed ? 'Add the corresponding MP4 to frontend/public/videos.' : 'Gameplay preview loads when a clip is available.'}</small>
          </div>
        </div>
      )}
      <video
        className={`race-video-element ${ready ? 'race-video-visible' : ''}`}
        src={src}
        aria-label={title}
        controls={!preview}
        muted={preview}
        autoPlay={preview}
        loop={preview}
        playsInline
        preload="metadata"
        onLoadedData={() => { setReady(true); setFailed(false) }}
        onError={() => { setReady(false); setFailed(true) }}
      />
      {ready && preview && <span className="race-video-overlay">SNES Rainbow Road · Gameplay preview</span>}
    </div>
  )
}
