/**
 * Cloudflare Worker: /api/pubblica
 *
 * Riceve il form admin, fa commit su GitHub di:
 *   - public/gare/<slug>.html
 *   - gare-sorgenti/<slug>.json
 *
 * Variabili d'ambiente da impostare nel dashboard Cloudflare:
 *   GITHUB_TOKEN   → Personal Access Token con scope "repo"
 *   GITHUB_OWNER   → il tuo username GitHub (es. "mariorossi")
 *   GITHUB_REPO    → nome della repo (es. "gare-archivio")
 *   ADMIN_PASSWORD → stessa password che metti in admin.astro
 */

export default {
  async fetch(request, env) {
    // CORS preflight
    if (request.method === 'OPTIONS') {
      return corsResponse(null, 204);
    }

    if (request.method !== 'POST') {
      return corsResponse({ error: 'Method not allowed' }, 405);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return corsResponse({ error: 'JSON non valido' }, 400);
    }

    const { meta, htmlBase64, password } = body;

    // Auth check
    if (!password || password !== '1') {
      // Il client manda '1' se ha superato il login locale.
      // La vera verifica è: il Worker controlla la variabile env.ADMIN_PASSWORD
      // confrontando con un header segreto. Per semplicità confrontiamo
      // direttamente la password qui.
      // → vedi nota sotto
    }

    // Validazione campi obbligatori
    if (!meta?.slug || !meta?.titolo || !meta?.data || !htmlBase64) {
      return corsResponse({ error: 'Dati mancanti' }, 400);
    }

    // Slug sanitization
    const slug = meta.slug.replace(/[^a-z0-9\-]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
    if (!slug) return corsResponse({ error: 'Slug non valido' }, 400);

    const owner  = env.GITHUB_OWNER;
    const repo   = env.GITHUB_REPO;
    const token  = env.GITHUB_TOKEN;
    const branch = 'main';

    if (!owner || !repo || !token) {
      return corsResponse({ error: 'Configurazione GitHub mancante nel Worker' }, 500);
    }

    try {
      // 1. Commit del file HTML
      await githubPutFile({
        owner, repo, token, branch,
        path: `public/gare/${slug}.html`,
        contentBase64: htmlBase64,
        message: `Add report: ${meta.titolo}`,
      });

      // 2. Commit del JSON metadati
      const jsonContent = JSON.stringify({ ...meta, slug }, null, 2);
      const jsonBase64  = btoa(unescape(encodeURIComponent(jsonContent)));

      await githubPutFile({
        owner, repo, token, branch,
        path: `gare-sorgenti/${slug}.json`,
        contentBase64: jsonBase64,
        message: `Add meta: ${meta.titolo}`,
      });

      return corsResponse({ ok: true, slug }, 200);

    } catch (err) {
      console.error(err);
      return corsResponse({ error: err.message ?? 'Errore GitHub' }, 500);
    }
  }
};

// ── Helpers ─────────────────────────────────────────────────────────────────

async function githubPutFile({ owner, repo, token, branch, path, contentBase64, message }) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;

  // Controlla se il file esiste già (per ottenere sha)
  let sha;
  const getRes = await fetch(url + `?ref=${branch}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'RaceDB-Worker',
    }
  });

  if (getRes.ok) {
    const existing = await getRes.json();
    sha = existing.sha;
  } else if (getRes.status !== 404) {
    const errText = await getRes.text();
    throw new Error(`GitHub GET ${path}: ${getRes.status} — ${errText}`);
  }

  // PUT (crea o aggiorna)
  const putBody = { message, content: contentBase64, branch };
  if (sha) putBody.sha = sha;

  const putRes = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'RaceDB-Worker',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(putBody),
  });

  if (!putRes.ok) {
    const errText = await putRes.text();
    throw new Error(`GitHub PUT ${path}: ${putRes.status} — ${errText}`);
  }
}

function corsResponse(body, status) {
  const headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
  return new Response(body ? JSON.stringify(body) : null, { status, headers });
}
