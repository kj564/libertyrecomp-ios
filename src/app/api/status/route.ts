import { NextResponse } from "next/server";

declare global {
  // eslint-disable-next-line no-var
  var __libertyProcess: { child: import("child_process").ChildProcess; pid: number; startedAt: number } | undefined;
}

// ─── GET /api/status — is the game running? ──────────────────────────
export async function GET() {
  const proc = globalThis.__libertyProcess;
  if (!proc) {
    return NextResponse.json({ running: false, reachable: true });
  }
  // Check if process still alive
  try {
    process.kill(proc.pid, 0);
    return NextResponse.json({
      running: true,
      reachable: true,
      pid: proc.pid,
      startedAt: proc.startedAt,
      uptime: Math.floor((Date.now() - proc.startedAt) / 1000),
    });
  } catch {
    globalThis.__libertyProcess = undefined;
    return NextResponse.json({ running: false, reachable: true });
  }
}
