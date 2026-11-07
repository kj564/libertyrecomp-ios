module.exports = [
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
"[externals]/child_process [external] (child_process, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("child_process", () => require("child_process"));

module.exports = mod;
}),
"[project]/src/app/api/stream/route.ts [app-route] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "GET",
    ()=>GET,
    "dynamic",
    ()=>dynamic,
    "maxDuration",
    ()=>maxDuration
]);
var __TURBOPACK__imported__module__$5b$externals$5d2f$child_process__$5b$external$5d$__$28$child_process$2c$__cjs$29$__ = __turbopack_context__.i("[externals]/child_process [external] (child_process, cjs)");
;
const dynamic = "force-dynamic";
const maxDuration = 300; // 5 min cap per connection — browser reconnects
const BOUNDARY = "libertyrecompframe";
async function GET() {
    const platform = process.platform;
    let input = [];
    if ("TURBOPACK compile-time truthy", 1) {
        const display = process.env.DISPLAY || ":0.0";
        input = [
            "-f",
            "x11grab",
            "-framerate",
            "30",
            "-video_size",
            "1280x720",
            "-i",
            display
        ];
    } else //TURBOPACK unreachable
    ;
    const encoder = [
        "-c:v",
        "mjpeg",
        "-q:v",
        "5",
        "-pix_fmt",
        "yuvj420p",
        "-f",
        "mjpeg",
        "-probesize",
        "32",
        "-fpsprobesize",
        "0"
    ];
    const args = [
        "-hide_banner",
        "-loglevel",
        "error",
        ...input,
        ...encoder,
        "-"
    ];
    const ffmpeg = (0, __TURBOPACK__imported__module__$5b$externals$5d2f$child_process__$5b$external$5d$__$28$child_process$2c$__cjs$29$__["spawn"])("ffmpeg", args, {
        stdio: [
            "ignore",
            "pipe",
            "pipe"
        ]
    });
    const encoder_ = new TextEncoder();
    const header = `--${BOUNDARY}\r\nContent-Type: image/jpeg\r\n`;
    const stream = new ReadableStream({
        start (controller) {
            let buffer = Buffer.alloc(0);
            const writeHeader = ()=>{
                controller.enqueue(encoder_.encode("Content-Type: multipart/x-mixed-replace; boundary=" + BOUNDARY + "\r\n\r\n"));
            };
            writeHeader();
            ffmpeg.stdout.on("data", (chunk)=>{
                // Buffer until we have a full JPEG (find SOI 0xFFD8 and EOI 0xFFD9)
                buffer = Buffer.concat([
                    buffer,
                    chunk
                ]);
                let soi = buffer.indexOf(Buffer.from([
                    0xff,
                    0xd8
                ]));
                while(soi !== -1){
                    const eoi = buffer.indexOf(Buffer.from([
                        0xff,
                        0xd9
                    ]), soi + 2);
                    if (eoi === -1) break; // wait for more data
                    const jpeg = buffer.subarray(soi, eoi + 2);
                    const size = jpeg.length;
                    const part = header + `Content-Length: ${size}\r\n\r\n`;
                    controller.enqueue(encoder_.encode(part));
                    controller.enqueue(new Uint8Array(jpeg));
                    controller.enqueue(encoder_.encode("\r\n"));
                    buffer = buffer.subarray(eoi + 2);
                    soi = buffer.indexOf(Buffer.from([
                        0xff,
                        0xd8
                    ]));
                }
            });
            ffmpeg.stderr.on("data", (chunk)=>{
                console.error(`[ffmpeg] ${chunk.toString().trim()}`);
            });
            ffmpeg.on("exit", (code, signal)=>{
                console.log(`[ffmpeg] exited code=${code} signal=${signal}`);
                try {
                    controller.close();
                } catch  {}
            });
            ffmpeg.on("error", (err)=>{
                console.error(`[ffmpeg] spawn error:`, err);
                try {
                    controller.close();
                } catch  {}
            });
        },
        cancel () {
            console.log("[stream] client disconnected, killing ffmpeg");
            ffmpeg.kill("SIGTERM");
        }
    });
    return new Response(stream, {
        headers: {
            "Content-Type": `multipart/x-mixed-replace; boundary=${BOUNDARY}`,
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Connection": "close"
        }
    });
}
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__8adba364._.js.map