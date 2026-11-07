import { spawn } from "child_process";

// ─── GET /api/stream — MJPEG screen capture ──────────────────────────
//
// Captures the PC screen via ffmpeg and streams as multipart/x-mixed-replace
// (MJPEG). Browser displays it as a live <img src="/api/stream">.
//
// Platform-specific capture:
//   Linux:   ffmpeg -f x11grab -i :0.0 ...
//   Windows: ffmpeg -f gdigrab -i desktop ...
//   macOS:   ffmpeg -f avfoundation -i "1" ...
//
// Latency: ~200-500ms (MJPEG is the simplest stream protocol).
// For lower latency, use Sunshine (https://github.com/LizardByte/Sunshine)
// on PC + Moonlight app on iPhone.

export const dynamic = "force-dynamic";
export const maxDuration = 300; // 5 min cap per connection — browser reconnects

const BOUNDARY = "libertyrecompframe";

export async function GET() {
  const platform = process.platform;
  let input: string[] = [];

  if (platform === "linux") {
    const display = process.env.DISPLAY || ":0.0";
    input = ["-f", "x11grab", "-framerate", "30", "-video_size", "1280x720", "-i", display];
  } else if (platform === "win32") {
    input = ["-f", "gdigrab", "-framerate", "30", "-video_size", "1280x720", "-i", "desktop"];
  } else if (platform === "darwin") {
    input = ["-f", "avfoundation", "-framerate", "30", "-video_size", "1280x720", "-i", "1:none"];
  } else {
    return new Response("Unsupported platform: " + platform, { status: 500 });
  }

  const encoder = [
    "-c:v", "mjpeg",
    "-q:v", "5",
    "-pix_fmt", "yuvj420p",
    "-f", "mjpeg",
    "-probesize", "32",
    "-fpsprobesize", "0",
  ];

  const args = [
    "-hide_banner",
    "-loglevel", "error",
    ...input,
    ...encoder,
    "-", // stdout
  ];

  const ffmpeg = spawn("ffmpeg", args, { stdio: ["ignore", "pipe", "pipe"] });

  const encoder_ = new TextEncoder();
  const header = `--${BOUNDARY}\r\nContent-Type: image/jpeg\r\n`;

  const stream = new ReadableStream({
    start(controller) {
      let buffer = Buffer.alloc(0);

      const writeHeader = () => {
        controller.enqueue(encoder_.encode("Content-Type: multipart/x-mixed-replace; boundary=" + BOUNDARY + "\r\n\r\n"));
      };
      writeHeader();

      ffmpeg.stdout.on("data", (chunk: Buffer) => {
        // Buffer until we have a full JPEG (find SOI 0xFFD8 and EOI 0xFFD9)
        buffer = Buffer.concat([buffer, chunk]);
        let soi = buffer.indexOf(Buffer.from([0xff, 0xd8]));
        while (soi !== -1) {
          const eoi = buffer.indexOf(Buffer.from([0xff, 0xd9]), soi + 2);
          if (eoi === -1) break; // wait for more data
          const jpeg = buffer.subarray(soi, eoi + 2);
          const size = jpeg.length;
          const part = header + `Content-Length: ${size}\r\n\r\n`;
          controller.enqueue(encoder_.encode(part));
          controller.enqueue(new Uint8Array(jpeg));
          controller.enqueue(encoder_.encode("\r\n"));
          buffer = buffer.subarray(eoi + 2);
          soi = buffer.indexOf(Buffer.from([0xff, 0xd8]));
        }
      });

      ffmpeg.stderr.on("data", (chunk: Buffer) => {
        console.error(`[ffmpeg] ${chunk.toString().trim()}`);
      });

      ffmpeg.on("exit", (code, signal) => {
        console.log(`[ffmpeg] exited code=${code} signal=${signal}`);
        try { controller.close(); } catch {}
      });

      ffmpeg.on("error", (err) => {
        console.error(`[ffmpeg] spawn error:`, err);
        try { controller.close(); } catch {}
      });
    },
    cancel() {
      console.log("[stream] client disconnected, killing ffmpeg");
      ffmpeg.kill("SIGTERM");
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": `multipart/x-mixed-replace; boundary=${BOUNDARY}`,
      "Cache-Control": "no-cache, no-store, must-revalidate",
      "Pragma": "no-cache",
      "Connection": "close",
    },
  });
}
