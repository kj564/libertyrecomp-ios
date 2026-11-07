import { NextResponse } from "next/server";
import { spawn, ChildProcess } from "child_process";
import path from "path";
import fs from "fs";

interface GameProcess {
  child: ChildProcess;
  startedAt: number;
  pid: number;
}

declare global {
  // eslint-disable-next-line no-var
  var __libertyProcess: GameProcess | undefined;
}

function getConfig(): { exePath: string; workDir: string } | null {
  const exePath = process.env.LIBERTY_EXE_PATH;
  const workDir = process.env.LIBERTY_WORK_DIR;
  if (!exePath) return null;
  return {
    exePath,
    workDir: workDir || path.dirname(exePath),
  };
}

export async function POST() {
  if (globalThis.__libertyProcess && !globalThis.__libertyProcess.child.killed) {
    try {
      process.kill(globalThis.__libertyProcess.pid, 0);
      return NextResponse.json({
        ok: true,
        alreadyRunning: true,
        pid: globalThis.__libertyProcess.pid,
      });
    } catch {
      globalThis.__libertyProcess = undefined;
    }
  }

  const cfg = getConfig();
  if (!cfg) {
    return NextResponse.json(
      {
        ok: false,
        error:
          "LIBERTY_EXE_PATH not set. Create .env with LIBERTY_EXE_PATH=C:\\path\\to\\LibertyRecomp.exe",
      },
      { status: 500 }
    );
  }

  if (!fs.existsSync(cfg.exePath)) {
    return NextResponse.json(
      { ok: false, error: `Executable not found: ${cfg.exePath}` },
      { status: 404 }
    );
  }

  try {
    const child = spawn(cfg.exePath, [], {
      cwd: cfg.workDir,
      detached: false,
      stdio: "ignore",
      windowsHide: false,
    });

    child.on("exit", (code, signal) => {
      console.log(`[liberty] exited code=${code} signal=${signal}`);
      globalThis.__libertyProcess = undefined;
    });
    child.on("error", (err) => {
      console.error(`[liberty] spawn error:`, err);
      globalThis.__libertyProcess = undefined;
    });

    globalThis.__libertyProcess = {
      child,
      startedAt: Date.now(),
      pid: child.pid ?? 0,
    };

    return NextResponse.json({
      ok: true,
      pid: child.pid,
      startedAt: globalThis.__libertyProcess.startedAt,
    });
  } catch (err) {
    return NextResponse.json({ ok: false, error: String(err) }, { status: 500 });
  }
}
