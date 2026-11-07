// ─── LibertyRecomp Input Server ─────────────────────────────────────
// Mini-service: WebSocket server on port 3003.
// Receives touch input from phone browser, simulates keyboard/mouse on PC.
//
// Platform input simulation:
//   Linux:   xdotool (apt install xdotool) — for dev/testing
//   Windows: nircmd.exe (placed in input-server/nircmd.exe) — see README
//   macOS:   cliclick (brew install cliclick)
//
// Touch events from phone:
//   { type: "key",  key: "w", down: true/false }
//   { type: "mouse", x: 5, y: -3, button: "move" | "left" | "right" | "up" | "down" }

import { createServer } from "http";
import { Server } from "socket.io";
import { spawn, execSync } from "child_process";

const PORT = 3003;

// ─── Detect input simulator ─────────────────────────────────────────
type Backend = "xdotool" | "nircmd" | "cliclick" | "none";

function detectBackend(): Backend {
  const platform = process.platform;
  try {
    if (platform === "linux") {
      execSync("which xdotool", { stdio: "ignore" });
      return "xdotool";
    }
    if (platform === "darwin") {
      execSync("which cliclick", { stdio: "ignore" });
      return "cliclick";
    }
    if (platform === "win32") {
      // Check for nircmd.exe in input-server dir or PATH
      try {
        execSync("nircmd.exe", { stdio: "ignore" });
        return "nircmd";
      } catch {
        // Try relative path
        return "nircmd"; // assume present
      }
    }
  } catch {
    /* not found */
  }
  return "none";
}

const backend = detectBackend();
console.log(`[input] backend: ${backend}`);

// ─── Keyboard simulation ───────────────────────────────────────────
const pressedKeys = new Set<string>();

function sendKey(key: string, down: boolean) {
  // Normalize key
  const k = key.toLowerCase();
  if (down && pressedKeys.has(k)) return; // already pressed
  if (!down && !pressedKeys.has(k)) return; // not pressed
  if (down) pressedKeys.add(k); else pressedKeys.delete(k);

  if (backend === "xdotool") {
    const flag = down ? "down" : "up";
    const xdotoolKey = mapKeyForXdotool(k);
    spawn("xdotool", ["key", flag, xdotoolKey], { stdio: "ignore" });
  } else if (backend === "cliclick") {
    // cliclick doesn't separate keydown/up — use key: for tap, kp: for press, kr: for release
    const cmd = down ? "kp" : "kr";
    spawn("cliclick", [`${cmd}:${k}`], { stdio: "ignore" });
  } else if (backend === "nircmd") {
    // nircmd sendkey <key> <press|release>
    const flag = down ? "press" : "release";
    const nircmdKey = mapKeyForNircmd(k);
    spawn("nircmd.exe", ["sendkey", nircmdKey, flag], { stdio: "ignore" });
  } else {
    // No backend — log only (for testing)
    if (process.env.INPUT_DEBUG) console.log(`[key ${down ? "↓" : "↑"}] ${k}`);
  }
}

function mapKeyForXdotool(k: string): string {
  const map: Record<string, string> = {
    " ": "space",
    "shift": "Shift_L",
    "tab": "Tab",
    "escape": "Escape",
    "enter": "Return",
  };
  return map[k] || k;
}

function mapKeyForNircmd(k: string): string {
  const map: Record<string, string> = {
    " ": "space",
    "shift": "shift",
    "tab": "tab",
    "escape": "esc",
    "enter": "enter",
  };
  return map[k] || k;
}

// ─── Mouse simulation ──────────────────────────────────────────────
function sendMouse(x: number, y: number, button: "move" | "left" | "right" | "up" | "down") {
  if (backend === "xdotool") {
    if (button === "move") {
      spawn("xdotool", ["mousemove_relative", "--", String(x), String(y)], { stdio: "ignore" });
    } else if (button === "left") {
      spawn("xdotool", ["mousedown", "1"], { stdio: "ignore" });
    } else if (button === "up") {
      spawn("xdotool", ["mouseup", "1"], { stdio: "ignore" });
    } else if (button === "right") {
      spawn("xdotool", ["mousedown", "3"], { stdio: "ignore" });
    }
  } else if (backend === "cliclick") {
    if (button === "move") {
      spawn("cliclick", [`m:${x},${y}`], { stdio: "ignore" });
    } else if (button === "left") {
      spawn("cliclick", ["c:."], { stdio: "ignore" });
    }
  } else if (backend === "nircmd") {
    if (button === "move") {
      spawn("nircmd.exe", ["movecursor", String(x), String(y)], { stdio: "ignore" });
    } else if (button === "left") {
      spawn("nircmd.exe", ["sendmouse", "left", "click"], { stdio: "ignore" });
    } else if (button === "right") {
      spawn("nircmd.exe", ["sendmouse", "right", "click"], { stdio: "ignore" });
    }
  } else {
    if (process.env.INPUT_DEBUG) console.log(`[mouse ${button}] x=${x} y=${y}`);
  }
}

// ─── WebSocket server ──────────────────────────────────────────────
const httpServer = createServer();
const io = new Server(httpServer, {
  path: "/",
  cors: { origin: "*", methods: ["GET", "POST"] },
  pingTimeout: 60000,
  pingInterval: 25000,
});

io.on("connection", (socket) => {
  console.log(`[ws] client connected: ${socket.id}`);
  pressedKeys.clear();

  socket.on("input", (data: any) => {
    if (!data || typeof data !== "object") return;
    if (data.type === "key" && typeof data.key === "string") {
      sendKey(data.key, data.down === true);
    } else if (data.type === "mouse") {
      sendMouse(Number(data.x) || 0, Number(data.y) || 0, data.button);
    }
  });

  socket.on("ping", (t: number) => {
    socket.emit("pong", t);
  });

  socket.on("disconnect", () => {
    console.log(`[ws] client disconnected: ${socket.id}`);
    // Release all keys when phone disconnects (avoid stuck keys)
    for (const k of Array.from(pressedKeys)) {
      sendKey(k, false);
    }
    pressedKeys.clear();
  });

  socket.on("error", (err) => {
    console.error(`[ws] error ${socket.id}:`, err);
  });
});

httpServer.listen(PORT, "::", () => {
  console.log(`[input] LibertyRecomp input server on port ${PORT}`);
  console.log(`[input] Backend: ${backend}`);
  if (backend === "none") {
    console.log("[input] ⚠️  No input simulator installed.");
    if (process.platform === "linux") console.log("[input]    apt install xdotool");
    if (process.platform === "darwin") console.log("[input]    brew install cliclick");
    if (process.platform === "win32") console.log("[input]    download nircmd.exe to this folder");
  }
});

process.on("SIGTERM", () => {
  for (const k of Array.from(pressedKeys)) sendKey(k, false);
  httpServer.close(() => process.exit(0));
});
process.on("SIGINT", () => {
  for (const k of Array.from(pressedKeys)) sendKey(k, false);
  httpServer.close(() => process.exit(0));
});

