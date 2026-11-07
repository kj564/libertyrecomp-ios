import { NextResponse } from "next/server";

declare global {
  // eslint-disable-next-line no-var
  var __libertyProcess: { child: import("child_process").ChildProcess; pid: number; startedAt: number } | undefined;
}

// ─── POST /api/stop — kill the running game ──────────────────────────
export async function POST() {
  const proc = globalThis.__libertyProcess;
  if (!proc) {
    return NextResponse.json({ ok: false, error: "no process running" });
  }
  try {
    proc.child.kill("SIGTERM");
    // Force kill after 3s if still alive
    setTimeout(() => {
      try {
        process.kill(proc.pid, 0);
        process.kill(proc.pid, "SIGKILL");
      } catch {
        // already dead
      }
    }, 3000);
    globalThis.__libertyProcess = undefined;
    return NextResponse.json({ ok: true, killed: proc.pid });
  } catch (err) {
    return NextResponse.json({ ok: false, error: String(err) }, { status: 500 });
  }
}
