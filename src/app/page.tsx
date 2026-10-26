'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const pipeline = [
  {
    step: '1',
    title: 'AI Image Generation',
    tool: 'gen_image_free.py',
    desc: '3 storyboard stills (chess board, queen, checkmate) generated free via z-ai-web-dev-sdk. No API key, $0.',
    icon: '🖼️',
  },
  {
    step: '2',
    title: 'Voice Synthesis (TTS)',
    tool: 'gen_voice_free.py',
    desc: '17 narration lines synthesized via free z-ai TTS (voice: jam) in a single batch call. Word-synced captions baked in.',
    icon: '🎙️',
  },
  {
    step: '3',
    title: 'Sound Design',
    tool: 'mix_sfx + music library',
    desc: 'Background music from the committed library (cinematic-min.mp3) mixed under the voice at -15dB.',
    icon: '🎵',
  },
  {
    step: '4',
    title: 'Video Assembly',
    tool: 'ffmpeg (Ken Burns)',
    desc: 'Images animated with Ken Burns zoom, text overlays synced to voice, scenes concatenated and mixed.',
    icon: '🎬',
  },
]

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-[#0d1117] text-[#c9d1d9]">
      {/* Header */}
      <header className="border-b border-[#30363d] bg-[#161b22]">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-[#6366F1] to-[#4db8a8] text-sm font-bold text-white">
              FC
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">Faceless Shorts Creator</h1>
              <p className="text-xs text-[#8b949e]">100% free pipeline · no API keys</p>
            </div>
          </div>
          <Badge variant="outline" className="border-[#6366F1]/40 text-[#6366F1]">
            Sample Video
          </Badge>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col items-center px-6 py-8">
        {/* Video player */}
        <div className="w-full max-w-sm">
          <div className="mb-4 text-center">
            <h2 className="text-2xl font-bold text-white">The 4-Move Checkmate</h2>
            <p className="mt-1 text-sm text-[#8b949e]">
              1080 × 1920 · 15s · vertical short · voiced + sound-designed
            </p>
          </div>

          {/* Video container — 9:16 aspect ratio */}
          <div className="relative overflow-hidden rounded-2xl border border-[#30363d] bg-black shadow-2xl">
            <video
              className="h-full w-full"
              controls
              autoPlay
              loop
              playsInline
              poster="/sample/chess-board.png"
            >
              <source src="/sample/sample-short.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>

          {/* Stats bar */}
          <div className="mt-4 flex items-center justify-center gap-4 text-xs text-[#8b949e]">
            <span>📁 2.9 MB</span>
            <span>·</span>
            <span>🎯 h264 + aac</span>
            <span>·</span>
            <span>⚙️ ffmpeg + z-ai</span>
          </div>
        </div>

        {/* Pipeline breakdown */}
        <div className="mt-12 w-full">
          <h3 className="mb-6 text-center text-sm font-semibold uppercase tracking-wider text-[#8b949e]">
            How this video was made — $0 API spend
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {pipeline.map((p) => (
              <Card
                key={p.step}
                className="border-[#30363d] bg-[#161b22] py-4 [&_[data-slot=card-header]]:px-4 [&_[data-slot=card-content]]:px-4"
              >
                <CardHeader className="gap-2">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl">{p.icon}</span>
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#6366F1]/15 text-xs font-bold text-[#6366F1]">
                      {p.step}
                    </span>
                  </div>
                  <CardTitle className="text-sm text-white">{p.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <code className="block rounded bg-[#0d1117] px-2 py-1 font-mono text-xs text-[#4db8a8]">
                    {p.tool}
                  </code>
                  <p className="text-xs leading-relaxed text-[#8b949e]">{p.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Tools used */}
        <div className="mt-12 w-full max-w-3xl">
          <Card className="border-[#30363d] bg-[#161b22] py-6 [&_[data-slot=card-content]]:px-6">
            <CardContent className="space-y-4">
              <h3 className="text-base font-semibold text-white">Free tools used</h3>
              <div className="flex flex-wrap gap-2">
                {[
                  'gen_image_free.py',
                  'gen_voice_free.py',
                  'mix_sfx.py',
                  'ffmpeg',
                  'z-ai-web-dev-sdk',
                  'edge-tts (available)',
                  'gen_chords.py',
                  'media/library/sfx (33 clips)',
                  'media/library/music (6 beds)',
                ].map((tool) => (
                  <Badge
                    key={tool}
                    variant="outline"
                    className="border-[#30363d] bg-[#0d1117] font-mono text-xs text-[#4db8a8]"
                  >
                    {tool}
                  </Badge>
                ))}
              </div>
              <p className="border-t border-[#30363d] pt-4 text-sm text-[#8b949e]">
                This entire pipeline runs <span className="text-[#6366F1]">without any paid API keys</span>.
                The <code className="rounded bg-[#0d1117] px-1.5 py-0.5 font-mono text-xs text-[#4db8a8]">.env</code> file
                has empty slots for ElevenLabs, Gemini, and fal.ai — all optional. The free path uses
                z-ai-web-dev-sdk (image + TTS), the committed SFX/music library, and deterministic chord synthesis.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Sticky footer */}
      <footer className="mt-auto border-t border-[#30363d] bg-[#161b22]">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4 text-xs text-[#8b949e]">
          <span>Faceless Shorts Creator · Free Pipeline</span>
          <a
            href="/sample/sample-short.mp4"
            download
            className="text-[#6366F1] transition-colors hover:text-[#818cf8]"
          >
            Download video ↓
          </a>
        </div>
      </footer>
    </div>
  )
}
