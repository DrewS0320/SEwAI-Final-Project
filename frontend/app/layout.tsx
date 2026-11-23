import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'KartScope — Time Trial Analytics',
  description: 'Turn Mario Kart 8 Deluxe time trial footage into clear performance insights.',
  applicationName: 'KartScope',
}

export const viewport: Viewport = {
  colorScheme: 'dark',
  themeColor: '#0b1118',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
