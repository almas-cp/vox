const SYSTEM_PROMPT =
  'You are a shell command generator for Kali Linux (Debian-based) running bash. ' +
  'Output ONLY the exact shell command. No explanations, no markdown, ' +
  'no code blocks, no backticks, no commentary. Just the raw command. ' +
  'If multiple commands are needed, chain them with && or ;.';
const MODEL = 'llama-3.3-70b-versatile';
const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const SKIP_PATHS = new Set(['', 'favicon.ico', 'robots.txt']);

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
    'Source: https://github.com/almas-cp/vox',
    '',
  ].join('\n');

  return new Response(text, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const query = decodeURIComponent(url.pathname.slice(1)).trim();

    if (SKIP_PATHS.has(query)) {
      return usagePage();
    }

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
            { role: 'system', content: SYSTEM_PROMPT },
            { role: 'user', content: query },
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
      },
    });
  },
};
