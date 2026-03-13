const MODEL = 'llama-3.3-70b-versatile';
const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const SKIP_PATHS = new Set(['', 'favicon.ico', 'robots.txt']);

// ---------------------------------------------------------------------------
// User-Agent → system / shell detection
// ---------------------------------------------------------------------------

/**
 * Lightweight heuristic that inspects a User-Agent string and returns a best-
 * guess { os, shell, detail } object.  When detection fails the default is
 * Debian Linux running bash.
 */
function detectSystem(ua) {
  if (!ua) return { os: 'Linux', distro: 'Debian', shell: 'bash', detail: 'unknown agent' };

  const lower = ua.toLowerCase();

  // — Windows —
  if (lower.includes('windows') || lower.includes('win32') || lower.includes('win64')) {
    if (lower.includes('powershell')) {
      const ver = ua.match(/PowerShell[\/\s]?([\d.]+)/i);
      return {
        os: 'Windows',
        distro: 'Windows',
        shell: 'powershell',
        detail: ver ? `PowerShell ${ver[1]}` : 'PowerShell',
      };
    }
    if (lower.includes('cmd') || lower.includes('command prompt')) {
      return { os: 'Windows', distro: 'Windows', shell: 'cmd', detail: 'CMD' };
    }
    // Default Windows → PowerShell (most modern setups)
    return { os: 'Windows', distro: 'Windows', shell: 'powershell', detail: 'Windows (assumed PowerShell)' };
  }

  // — macOS —
  if (lower.includes('darwin') || lower.includes('macos') || lower.includes('mac os x') || lower.includes('macintosh')) {
    return { os: 'macOS', distro: 'macOS', shell: 'zsh', detail: 'macOS (zsh default)' };
  }

  // — Linux distros —
  const distros = [
    { pattern: /kali/i,       distro: 'Kali Linux',  shell: 'bash' },
    { pattern: /ubuntu/i,     distro: 'Ubuntu',       shell: 'bash' },
    { pattern: /fedora/i,     distro: 'Fedora',       shell: 'bash' },
    { pattern: /arch/i,       distro: 'Arch Linux',   shell: 'bash' },
    { pattern: /centos/i,     distro: 'CentOS',       shell: 'bash' },
    { pattern: /rhel|red\s?hat/i, distro: 'RHEL',     shell: 'bash' },
    { pattern: /alpine/i,     distro: 'Alpine Linux', shell: 'ash'  },
    { pattern: /suse|sles/i,  distro: 'openSUSE',     shell: 'bash' },
    { pattern: /debian/i,     distro: 'Debian',       shell: 'bash' },
    { pattern: /manjaro/i,    distro: 'Manjaro',      shell: 'bash' },
    { pattern: /mint/i,       distro: 'Linux Mint',   shell: 'bash' },
    { pattern: /gentoo/i,     distro: 'Gentoo',       shell: 'bash' },
  ];

  for (const d of distros) {
    if (d.pattern.test(ua)) {
      return { os: 'Linux', distro: d.distro, shell: d.shell, detail: d.distro };
    }
  }

  // Generic Linux
  if (lower.includes('linux')) {
    return { os: 'Linux', distro: 'Debian', shell: 'bash', detail: 'Linux (defaulting to Debian)' };
  }

  // — Android / iOS / FreeBSD / other —
  if (lower.includes('android'))             return { os: 'Android', distro: 'Android', shell: 'bash', detail: 'Android (Termux assumed)' };
  if (lower.includes('iphone') || lower.includes('ipad')) return { os: 'iOS', distro: 'iOS', shell: 'sh', detail: 'iOS' };
  if (lower.includes('freebsd'))             return { os: 'FreeBSD', distro: 'FreeBSD', shell: 'sh', detail: 'FreeBSD' };

  // Fallback → Debian bash
  return { os: 'Linux', distro: 'Debian', shell: 'bash', detail: 'unrecognised agent — defaulting to Debian' };
}

/**
 * Build the dynamic system prompt using the detected system info.
 */
function buildSystemPrompt(sys) {
  return (
    `You are a shell command generator for ${sys.distro} (${sys.os}) running ${sys.shell}. ` +
    'Output ONLY the exact shell command. No explanations, no markdown, ' +
    'no code blocks, no backticks, no commentary. Just the raw command. ' +
    (sys.shell === 'powershell'
      ? 'If multiple commands are needed, chain them with ; or use pipelines.'
      : sys.shell === 'cmd'
        ? 'If multiple commands are needed, chain them with & or &&.'
        : 'If multiple commands are needed, chain them with && or ;.')
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function cleanResponse(text) {
  return text
    .replace(/```[\w]*\n?/g, '')
    .replace(/^`+|`+$/g, '')
    .trim();
}

function usagePage() {
  const text = [
    'vox — natural language to shell commands',
    '',
    'Usage:',
    '  curl "https://vox.workers.dev/list all files"',
    '  curl "https://vox.workers.dev/find python files modified today"',
    '  curl "https://vox.workers.dev/compress this folder to tar.gz"',
    '  curl "https://vox.workers.dev/show disk usage sorted by size"',
    '  curl "https://vox.workers.dev/kill process on port 3000"',
    '',
    'The system your request agent reports is auto-detected (default: Debian).',
    '',
    'Source: https://github.com/almas-cp/vox',
    '',
  ].join('\n');

  return new Response(text, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}

// ---------------------------------------------------------------------------
// Worker entry
// ---------------------------------------------------------------------------

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const query = decodeURIComponent(url.pathname.slice(1)).trim();

    if (SKIP_PATHS.has(query)) {
      return usagePage();
    }

    // Detect system from User-Agent
    const userAgent = request.headers.get('User-Agent') || '';
    const sys = detectSystem(userAgent);
    const systemPrompt = buildSystemPrompt(sys);

    // Build user message with agent context so Groq can further refine
    const userMessage =
      `[Agent context — User-Agent: "${userAgent}" → detected: ${sys.detail} (${sys.os}/${sys.shell})]\n\n` +
      query;

    let apiRes;
    try {
      apiRes = await fetch(GROQ_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${env.GROQ_API_KEY}`,
        },
        body: JSON.stringify({
          model: MODEL,
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userMessage },
          ],
          max_tokens: 400,
          temperature: 0,
        }),
      });
    } catch {
      return new Response('error: could not reach groq API\n', { status: 502 });
    }

    if (!apiRes.ok) {
      const status = apiRes.status;
      if (status === 401) return new Response('error: invalid API key\n', { status: 502 });
      if (status === 429) return new Response('error: rate limited, try again shortly\n', { status: 429 });
      return new Response(`error: groq returned HTTP ${status}\n`, { status: 502 });
    }

    let command;
    try {
      const data = await apiRes.json();
      command = cleanResponse(data.choices[0].message.content);
    } catch {
      return new Response('error: unexpected response from API\n', { status: 502 });
    }

    if (!command) {
      return new Response('error: empty response, try rephrasing\n', { status: 400 });
    }

    return new Response(command + '\n', {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'X-Detected-System': `${sys.distro} (${sys.shell})`,
      },
    });
  },
};
