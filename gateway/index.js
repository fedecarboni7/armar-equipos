const express = require('express');
const path = require('path');
const http = require('http');
const https = require('https');

const backendUrl = process.env.BACKEND_URL;
const port = Number.parseInt(process.env.PORT || '3000', 10);
const proxyConnectTimeoutMs = Number.parseInt(process.env.PROXY_CONNECT_TIMEOUT_MS || '2000', 10);
const healthCheckTimeoutMs = Number.parseInt(process.env.HEALTH_CHECK_TIMEOUT_MS || '1500', 10);

if (!backendUrl) {
  console.error('BACKEND_URL is required. Refusing to start gateway.');
  process.exit(1);
}

const parsedBackend = new URL(backendUrl);
const client = parsedBackend.protocol === 'https:' ? https : http;

const app = express();
const publicDir = path.join(__dirname, 'public');
const statusPhrases = [
  'calentando jugadores',
  'ajustando el algoritmo',
  'acomodando los arcos',
  'marcando la cancha',
  'repartiendo pecheras',
  'sorteando capitanes',
  'afinando el equilibrio de equipos',
  'inflando la pelota'
];

async function checkBackendAwake() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), healthCheckTimeoutMs);

  try {
    const response = await fetch(new URL('/healthz', backendUrl), {
      method: 'GET',
      signal: controller.signal,
      headers: {
        accept: 'application/json, text/plain, */*'
      }
    });

    return response.status >= 200 && response.status < 300;
  } catch (error) {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

function fireAndForgetWakeRequest() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), healthCheckTimeoutMs);

  fetch(new URL('/healthz', backendUrl), {
    method: 'GET',
    signal: controller.signal,
    headers: {
      accept: '*/*'
    }
  }).catch(() => {}).finally(() => clearTimeout(timer));
}

function buildWakingPageHtml() {
  const hasBallImage = false;
  const ballMarkup = hasBallImage
    ? '<img class="ball ball-image" src="/ball.png" alt="Pelota" />'
    : '<span class="ball ball-emoji" aria-hidden="true">⚽</span>';

  return `<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate, proxy-revalidate" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />
  <title>Armando el equipo</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f4ef;
      --panel: rgba(255, 255, 255, 0.78);
      --text: #17212f;
      --muted: #516075;
      --accent: #0f766e;
      --shadow: rgba(15, 23, 42, 0.18);
    }

    html, body {
      margin: 0;
      min-height: 100%;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background:
        radial-gradient(circle at top, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.65) 28%, transparent 60%),
        linear-gradient(180deg, #fffaf1 0%, var(--bg) 100%);
      color: var(--text);
    }

    body {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 32px 20px;
      box-sizing: border-box;
    }

    .card {
      width: min(560px, 100%);
      text-align: center;
      padding: 36px 28px 32px;
      background: var(--panel);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(23, 33, 47, 0.08);
      border-radius: 28px;
      box-shadow: 0 24px 80px rgba(15, 23, 42, 0.10);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 7px 12px;
      border-radius: 999px;
      background: rgba(15, 118, 110, 0.10);
      color: var(--accent);
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }

    h1 {
      margin: 18px 0 8px;
      font-size: clamp(2rem, 5vw, 3.5rem);
      line-height: 1.02;
      letter-spacing: -0.04em;
    }

    .subtitle {
      min-height: 1.6em;
      margin: 0;
      font-size: clamp(1rem, 2vw, 1.2rem);
      color: var(--muted);
      font-weight: 500;
    }

    .scene {
      position: relative;
      width: 180px;
      height: 180px;
      margin: 24px auto 10px;
      display: grid;
      place-items: center;
    }

    .ball {
      position: relative;
      z-index: 2;
      width: 112px;
      height: 112px;
      animation: bounce 1.15s ease-in-out infinite, spin 5s linear infinite;
      transform-origin: center bottom;
      will-change: transform;
      filter: drop-shadow(0 18px 18px rgba(15, 23, 42, 0.16));
    }

    .ball-image {
      object-fit: contain;
    }

    .ball-emoji {
      display: grid;
      place-items: center;
      font-size: 72px;
      line-height: 1;
      width: auto;
      height: auto;
    }

    .shadow {
      position: absolute;
      bottom: 26px;
      left: 50%;
      width: 96px;
      height: 20px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(15, 23, 42, 0.30) 0%, rgba(15, 23, 42, 0.13) 45%, rgba(15, 23, 42, 0) 74%);
      transform: translateX(-50%);
      animation: shadowPulse 1.15s ease-in-out infinite;
      filter: blur(1px);
    }

    .dots {
      display: inline-flex;
      gap: 8px;
      margin-top: 20px;
    }

    .dots span {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: rgba(23, 33, 47, 0.42);
      animation: dotPulse 1.1s infinite ease-in-out;
    }

    .dots span:nth-child(2) { animation-delay: 0.18s; }
    .dots span:nth-child(3) { animation-delay: 0.36s; }

    @keyframes bounce {
      0%, 100% { transform: translateY(0) rotate(0deg) scale(1); }
      35% { transform: translateY(-16px) rotate(-6deg) scale(1.03); }
      55% { transform: translateY(-34px) rotate(5deg) scale(1.04); }
      75% { transform: translateY(-8px) rotate(-3deg) scale(0.98); }
    }

    @keyframes spin {
      from { }
      to { }
    }

    @keyframes shadowPulse {
      0%, 100% { transform: translateX(-50%) scale(1); opacity: 0.78; }
      35% { transform: translateX(-50%) scale(0.72); opacity: 0.52; }
      55% { transform: translateX(-50%) scale(0.58); opacity: 0.38; }
      75% { transform: translateX(-50%) scale(0.88); opacity: 0.65; }
    }

    @keyframes dotPulse {
      0%, 80%, 100% { transform: translateY(0); opacity: 0.36; }
      40% { transform: translateY(-4px); opacity: 1; }
    }
  </style>
</head>
<body>
  <main class="card">
    <div class="badge">Gateway activo</div>
    <h1>Armando el equipo</h1>
    <p class="subtitle" id="subtitle">calentando jugadores</p>

    <div class="scene" aria-hidden="true">
      <div class="shadow"></div>
      ${ballMarkup}
    </div>

    <div class="dots" aria-hidden="true"><span></span><span></span><span></span></div>
  </main>

  <script>
    (() => {
      const phrases = ${JSON.stringify(statusPhrases)};
      const subtitle = document.getElementById('subtitle');
      let phraseIndex = 0;
      let pollInterval = 2000;
      const start = Date.now();
      let timerId = null;

      function rotateSubtitle() {
        phraseIndex = (phraseIndex + 1) % phrases.length;
        subtitle.textContent = phrases[phraseIndex];
      }

      async function pollGatewayHealth() {
        try {
          const response = await fetch('/__gateway/health', {
            method: 'GET',
            cache: 'no-store',
            headers: { accept: 'application/json' }
          });

          if (response.ok) {
            const payload = await response.json().catch(() => null);
            if (payload && payload.awake) {
              window.location.reload();
            }
          }
        } catch (error) {
          void error;
        }

        if (Date.now() - start >= 30000 && pollInterval !== 5000) {
          pollInterval = 5000;
          clearInterval(timerId);
          timerId = setInterval(pollGatewayHealth, pollInterval);
        }
      }

      rotateSubtitle();
      setInterval(rotateSubtitle, 2200);
      timerId = setInterval(pollGatewayHealth, pollInterval);
      pollGatewayHealth();
    })();
  </script>
</body>
</html>`;
}

function sendWakePage(response) {
  response.status(200);
  response.set({
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
    Pragma: 'no-cache',
    Expires: '0'
  });
  response.send(buildWakingPageHtml());
}

function proxyRequest(req, res) {
  const startedAt = Date.now();
  const method = req.method;
  const originalPath = req.originalUrl || req.url || '/';

  let outcome = 'proxied';
  let settled = false;

  let proxyReq;

  const connectTimer = setTimeout(() => {
    if (settled) return;
    settled = true;
    outcome = 'waking';
    proxyReq.destroy();
    fireAndForgetWakeRequest();
    if (!res.headersSent) {
      sendWakePage(res);
    }
    const durationMs = Date.now() - startedAt;
    console.log(`${method} ${originalPath} ${outcome} ${durationMs}ms`);
  }, proxyConnectTimeoutMs);

  const options = {
    protocol: parsedBackend.protocol,
    hostname: parsedBackend.hostname,
    port: parsedBackend.port || (parsedBackend.protocol === 'https:' ? 443 : 80),
    path: originalPath,
    method,
    headers: {
      ...req.headers,
      host: parsedBackend.host,
      connection: 'close'
    }
  };

  proxyReq = client.request(options, (proxyRes) => {
    if (settled) {
      proxyRes.resume();
      return;
    }
    settled = true;
    clearTimeout(connectTimer);
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
    proxyRes.on('end', () => {
      const durationMs = Date.now() - startedAt;
      console.log(`${method} ${originalPath} ${outcome} ${durationMs}ms`);
    });
  });

  proxyReq.on('error', () => {
    if (settled) return;
    settled = true;
    clearTimeout(connectTimer);
    outcome = 'waking';
    fireAndForgetWakeRequest();
    if (!res.headersSent) {
      sendWakePage(res);
    }
    const durationMs = Date.now() - startedAt;
    console.log(`${method} ${originalPath} ${outcome} ${durationMs}ms`);
  });

  req.pipe(proxyReq);
}

app.use('/__gateway/health', async (req, res) => {
  if (req.method !== 'GET') {
    res.status(405).json({ awake: false });
    return;
  }

  const awake = await checkBackendAwake();
  res.status(awake ? 200 : 503).json({ awake });
});

app.use(express.static(publicDir));

app.use((req, res) => {
  proxyRequest(req, res);
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Gateway listening on 0.0.0.0:${port}`);
});