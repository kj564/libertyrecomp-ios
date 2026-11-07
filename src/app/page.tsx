"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Wifi, Play, Square, Gamepad2, Monitor } from "lucide-react";
import { io, Socket } from "socket.io-client";

type InputEvent =
  | { type: "key"; key: string; down: boolean }
  | { type: "mouse"; x: number; y: number; button: "move" | "down" | "up" | "left" | "right" };

interface JoystickState {
  active: boolean;
  startX: number;
  startY: number;
  dx: number;
  dy: number;
}

export default function HomePage() {
  const [pcReachable, setPcReachable] = useState<boolean | null>(null);
  const [gameRunning, setGameRunning] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [orientation, setOrientation] = useState<"portrait" | "landscape">("portrait");
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [socketConnected, setSocketConnected] = useState(false);

  const socketRef = useRef<Socket | null>(null);
  const moveJoyRef = useRef<JoystickState>({ active: false, startX: 0, startY: 0, dx: 0, dy: 0 });
  const lookJoyRef = useRef<JoystickState>({ active: false, startX: 0, startY: 0, dx: 0, dy: 0 });
  const lastMoveKeyRef = useRef<string>("");
  const lastLookSentRef = useRef<number>(0);

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch("/api/status?_=" + Date.now(), { cache: "no-store" });
        if (r.ok) {
          const data = await r.json();
          setPcReachable(true);
          setGameRunning(data.running === true);
        } else {
          setPcReachable(false);
        }
      } catch {
        setPcReachable(false);
      }
    };
    check();
    const id = setInterval(check, 3000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const handler = () => {
      setOrientation(window.innerWidth > window.innerHeight ? "landscape" : "portrait");
    };
    handler();
    window.addEventListener("resize", handler);
    window.addEventListener("orientationchange", handler);
    return () => {
      window.removeEventListener("resize", handler);
      window.removeEventListener("orientationchange", handler);
    };
  }, []);

  useEffect(() => {
    let sock: Socket | null = null;
    const connect = () => {
      if (sock?.connected) return;
      setConnecting(true);
      sock = io("/?XTransformPort=3003", {
        transports: ["polling"],
        reconnection: true,
        reconnectionAttempts: 5,
      });
      sock.on("connect", () => {
        setPcReachable(true);
        setConnecting(false);
        setSocketConnected(true);
      });
      sock.on("disconnect", () => {
        setConnecting(false);
        setSocketConnected(false);
      });
      sock.on("connect_error", () => {
        setConnecting(false);
        setPcReachable(false);
        setSocketConnected(false);
      });
      sock.on("pong", (t: number) => {
        setLatencyMs(Date.now() - t);
      });
      socketRef.current = sock;
      if (typeof window !== "undefined") {
        (window as unknown as { __libertySocket?: Socket }).__libertySocket = sock;
      }
    };
    connect();
    return () => {
      sock?.disconnect();
      socketRef.current = null;
    };
  }, []);

  const send = useCallback((ev: InputEvent) => {
    socketRef.current?.emit("input", ev);
  }, []);

  useEffect(() => {
    if (!socketConnected) return;
    const id = setInterval(() => {
      socketRef.current?.emit("ping", Date.now());
    }, 2000);
    return () => clearInterval(id);
  }, [socketConnected]);

  const sendMove = useCallback((dx: number, dy: number) => {
    const threshold = 0.3;
    let key = "";
    if (dy < -threshold) key = "w";
    else if (dy > threshold) key = "s";
    else if (dx < -threshold) key = "a";
    else if (dx > threshold) key = "d";

    if (key !== lastMoveKeyRef.current) {
      if (lastMoveKeyRef.current) send({ type: "key", key: lastMoveKeyRef.current, down: false });
      if (key) send({ type: "key", key, down: true });
      lastMoveKeyRef.current = key;
    }
  }, [send]);

  const sendLook = useCallback((dx: number, dy: number) => {
    const now = Date.now();
    if (now - lastLookSentRef.current < 16) return;
    lastLookSentRef.current = now;
    send({ type: "mouse", x: Math.round(dx * 8), y: Math.round(dy * 8), button: "move" });
  }, [send]);

  const handleJoystickStart = (e: React.TouchEvent, ref: typeof moveJoyRef) => {
    const t = e.touches[0];
    ref.current = { active: true, startX: t.clientX, startY: t.clientY, dx: 0, dy: 0 };
  };

  const handleJoystickMove = (e: React.TouchEvent, ref: typeof moveJoyRef, onMove: (dx: number, dy: number) => void) => {
    if (!ref.current.active) return;
    const t = e.touches[0];
    const dx = t.clientX - ref.current.startX;
    const dy = t.clientY - ref.current.startY;
    const max = 60;
    const norm = Math.min(1, Math.hypot(dx, dy) / max);
    const angle = Math.atan2(dy, dx);
    ref.current.dx = Math.cos(angle) * norm;
    ref.current.dy = Math.sin(angle) * norm;
    onMove(ref.current.dx, ref.current.dy);
  };

  const handleJoystickEnd = (ref: typeof moveJoyRef, onEnd: () => void) => {
    ref.current = { active: false, startX: 0, startY: 0, dx: 0, dy: 0 };
    onEnd();
  };

  const pressKey = (key: string) => send({ type: "key", key, down: true });
  const releaseKey = (key: string) => send({ type: "key", key, down: false });

  const launchGame = async () => {
    try {
      const r = await fetch("/api/launch", { method: "POST" });
      if (r.ok) {
        setGameRunning(true);
        setTimeout(() => setStreaming(true), 2000);
      }
    } catch {}
  };

  const stopGame = async () => {
    try {
      await fetch("/api/stop", { method: "POST" });
      setGameRunning(false);
      setStreaming(false);
    } catch {}
  };

  if (orientation === "portrait") {
    return (
      <main className="min-h-screen bg-background flex flex-col items-center justify-center p-6">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 flex flex-col items-center gap-4">
            <Monitor className="w-16 h-16 text-muted-foreground" />
            <h1 className="text-xl font-bold text-center">Rotate your phone</h1>
            <p className="text-sm text-muted-foreground text-center">
              LibertyRecomp Remote needs landscape orientation to play.
            </p>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="h-screen w-screen bg-black text-white overflow-hidden relative flex flex-col select-none">
      <header className="absolute top-0 left-0 right-0 z-30 flex items-center justify-between px-4 py-2 bg-gradient-to-b from-black/80 to-transparent pointer-events-none">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-black/50 backdrop-blur">
            <Wifi className={`w-3 h-3 mr-1 ${pcReachable ? "text-green-400" : "text-red-400"}`} />
            {pcReachable ? "PC Connected" : "PC Offline"}
          </Badge>
          {latencyMs !== null && (
            <Badge variant="outline" className="bg-black/50 backdrop-blur">
              {latencyMs}ms
            </Badge>
          )}
          {gameRunning && (
            <Badge variant="outline" className="bg-black/50 backdrop-blur">
              <span className="w-2 h-2 rounded-full bg-green-400 mr-1 animate-pulse" />
              Running
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 pointer-events-auto">
          {!gameRunning ? (
            <Button size="sm" variant="default" onClick={launchGame} disabled={!pcReachable}>
              <Play className="w-3 h-3 mr-1" /> Launch
            </Button>
          ) : (
            <Button size="sm" variant="destructive" onClick={stopGame}>
              <Square className="w-3 h-3 mr-1" /> Stop
            </Button>
          )}
        </div>
      </header>

      {streaming && pcReachable && (
        <div className="absolute inset-0 z-0">
          <img
            src="/api/stream"
            alt="PC stream"
            className="w-full h-full object-contain"
            onError={() => setStreaming(false)}
          />
        </div>
      )}

      {!streaming && (
        <div className="absolute inset-0 z-0 flex items-center justify-center">
          <Card className="bg-black/60 backdrop-blur border-muted">
            <CardContent className="pt-6 pb-6 px-8 flex flex-col items-center gap-3">
              <Gamepad2 className="w-12 h-12 text-muted-foreground" />
              <h2 className="text-lg font-semibold">
                {connecting ? "Connecting..." : pcReachable ? "Ready" : "PC Offline"}
              </h2>
              <p className="text-xs text-muted-foreground text-center max-w-xs">
                {pcReachable
                  ? "Tap Launch to start LibertyRecomp on your PC."
                  : "Make sure the PC server is running and on the same Wi-Fi."}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <div
        className="absolute left-6 bottom-6 z-20 w-32 h-32 rounded-full bg-white/10 backdrop-blur-sm border-2 border-white/30 touch-none flex items-center justify-center"
        onTouchStart={(e) => handleJoystickStart(e, moveJoyRef)}
        onTouchMove={(e) => handleJoystickMove(e, moveJoyRef, sendMove)}
        onTouchEnd={() => handleJoystickEnd(moveJoyRef, () => {
          if (lastMoveKeyRef.current) {
            send({ type: "key", key: lastMoveKeyRef.current, down: false });
            lastMoveKeyRef.current = "";
          }
        })}
      >
        <div className="w-12 h-12 rounded-full bg-white/40 backdrop-blur" />
      </div>

      <div className="absolute left-44 bottom-8 z-20 flex flex-col gap-2">
        <ActionButton label="Sprint" sub="Shift" size="sm" onPress={() => pressKey("shift")} onRelease={() => releaseKey("shift")} />
        <ActionButton label="Map" sub="Tab" size="sm" onPress={() => pressKey("tab")} onRelease={() => releaseKey("tab")} />
        <ActionButton label="Reload" sub="R" size="sm" onPress={() => pressKey("r")} onRelease={() => releaseKey("r")} />
      </div>

      <div
        className="absolute right-6 bottom-32 z-20 w-28 h-28 rounded-full bg-white/10 backdrop-blur-sm border-2 border-white/30 touch-none flex items-center justify-center"
        onTouchStart={(e) => handleJoystickStart(e, lookJoyRef)}
        onTouchMove={(e) => handleJoystickMove(e, lookJoyRef, sendLook)}
        onTouchEnd={() => handleJoystickEnd(lookJoyRef, () => {})}
      >
        <div className="w-10 h-10 rounded-full bg-white/40 backdrop-blur" />
      </div>

      <div className="absolute right-6 bottom-6 z-20 grid grid-cols-2 gap-3">
        <ActionButton label="Jump" sub="Space" onPress={() => pressKey("space")} onRelease={() => releaseKey("space")} />
        <ActionButton label="Enter" sub="F" onPress={() => pressKey("f")} onRelease={() => releaseKey("f")} />
        <ActionButton label="Aim" sub="RMB" onPress={() => send({ type: "mouse", x: 0, y: 0, button: "right" })} onRelease={() => {}} variant="secondary" />
        <ActionButton label="Fire" sub="LMB" onPress={() => send({ type: "mouse", x: 0, y: 0, button: "left" })} onRelease={() => {}} variant="destructive" />
      </div>

      <div className="absolute top-12 right-4 z-20 grid grid-cols-3 gap-1">
        {[1, 2, 3, 4, 5, 6].map((n) => (
          <button
            key={n}
            className="w-8 h-8 rounded bg-white/10 backdrop-blur text-xs font-mono active:bg-white/30"
            onTouchStart={(e) => { e.preventDefault(); pressKey(String(n)); }}
            onTouchEnd={(e) => { e.preventDefault(); releaseKey(String(n)); }}
          >
            {n}
          </button>
        ))}
      </div>
    </main>
  );
}

function ActionButton({
  label,
  sub,
  onPress,
  onRelease,
  size = "default",
  variant = "default",
}: {
  label: string;
  sub?: string;
  onPress: () => void;
  onRelease: () => void;
  size?: "sm" | "default";
  variant?: "default" | "secondary" | "destructive";
}) {
  return (
    <button
      className={`
        ${size === "sm" ? "w-14 h-14" : "w-16 h-16"}
        rounded-full backdrop-blur border-2 font-semibold
        ${variant === "default" ? "bg-white/15 border-white/40 text-white" : ""}
        ${variant === "secondary" ? "bg-blue-500/30 border-blue-400/50 text-blue-100" : ""}
        ${variant === "destructive" ? "bg-red-500/30 border-red-400/50 text-red-100" : ""}
        active:scale-95 transition-transform touch-none flex flex-col items-center justify-center
      `}
      onTouchStart={(e) => { e.preventDefault(); onPress(); }}
      onTouchEnd={(e) => { e.preventDefault(); onRelease(); }}
      onTouchCancel={(e) => { e.preventDefault(); onRelease(); }}
      onClick={(e) => {
        e.preventDefault();
        onPress();
        setTimeout(onRelease, 100);
      }}
    >
      <span className={size === "sm" ? "text-[10px]" : "text-xs"}>{label}</span>
      {sub && <span className="text-[8px] opacity-60 mt-0.5">{sub}</span>}
    </button>
  );
}
