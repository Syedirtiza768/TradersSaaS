#!/usr/bin/env node
/**
 * Regenerates docs/IMPLEMENTATION_PROGRESS.md and docs/.implementation-progress.snapshot.json
 * from docs/implementation-progress.manifest.json + repo scans (TODOS.md, git).
 *
 * Usage: node scripts/update-implementation-progress.mjs
 *    or: npm run progress:sync
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, '..');
const MANIFEST = path.join(ROOT, 'docs', 'implementation-progress.manifest.json');
const OUT_MD = path.join(ROOT, 'docs', 'IMPLEMENTATION_PROGRESS.md');
const OUT_JSON = path.join(ROOT, 'docs', '.implementation-progress.snapshot.json');
const TODOS = path.join(ROOT, 'TODOS.md');

const MARK_START = '<!-- IMPLEMENTATION_PROGRESS:AUTO:START -->';
const MARK_END = '<!-- IMPLEMENTATION_PROGRESS:AUTO:END -->';

function read(p) {
  return fs.readFileSync(p, 'utf8');
}

function exists(rel) {
  return fs.existsSync(path.join(ROOT, rel));
}

function evalVerify(rule) {
  const abs = path.join(ROOT, rule.path);
  switch (rule.type) {
    case 'file_exists':
      return { ok: fs.existsSync(abs), detail: rule.path };
    case 'file_missing':
      return { ok: !fs.existsSync(abs), detail: `missing ${rule.path}` };
    case 'file_contains': {
      if (!fs.existsSync(abs)) return { ok: false, detail: `no file ${rule.path}` };
      const t = read(abs);
      return { ok: t.includes(rule.substring), detail: rule.substring.slice(0, 60) };
    }
    case 'file_not_contains': {
      if (!fs.existsSync(abs)) return { ok: false, detail: `no file ${rule.path}` };
      const t = read(abs);
      return { ok: !t.includes(rule.substring), detail: `not: ${rule.substring.slice(0, 40)}` };
    }
    case 'substring_count': {
      if (!fs.existsSync(abs)) return { ok: false, detail: `no file ${rule.path}` };
      const t = read(abs);
      const n = t.split(rule.substring).length - 1;
      const want = Number(rule.equals);
      return { ok: n === want, detail: `count ${rule.substring}=${n} want ${want}` };
    }
    default:
      return { ok: false, detail: `unknown rule ${rule.type}` };
  }
}

function parseTodosStats() {
  if (!fs.existsSync(TODOS)) {
    return { lines: 0, byTag: {} };
  }
  const text = read(TODOS);
  const byTag = {};
  const re = /^###\s+\[([^\]]+)\]/gm;
  let m;
  while ((m = re.exec(text)) !== null) {
    const tag = m[1];
    byTag[tag] = (byTag[tag] || 0) + 1;
  }
  return { lines: text.split('\n').length, byTag };
}

function gitHead() {
  try {
    return execSync('git rev-parse --short HEAD', { cwd: ROOT, encoding: 'utf8' }).trim();
  } catch {
    return null;
  }
}

function gitRecent(n = 8) {
  try {
    return execSync(`git log -${n} --oneline`, { cwd: ROOT, encoding: 'utf8' }).trim();
  } catch {
    return '(git log unavailable)';
  }
}

function evaluateItem(item) {
  if (item.manual) {
    return {
      id: item.id,
      title: item.title,
      priority: item.priority || 'P2',
      status: 'manual',
      manual: true,
      note: item.note || '',
      refs: item.refs || [],
    };
  }
  const failures = [];
  for (const rule of item.verify || []) {
    const r = evalVerify(rule);
    if (!r.ok) failures.push(`${rule.type}(${rule.path || ''}): ${r.detail}`);
  }
  return {
    id: item.id,
    title: item.title,
    priority: item.priority || 'P2',
    status: failures.length === 0 ? 'done' : 'pending',
    manual: false,
    failures,
    refs: item.refs || [],
  };
}

function buildAutoBody({ generatedAt, commit, todos, results }) {
  const verified = results.filter((r) => !r.manual);
  const manual = results.filter((r) => r.manual === true);
  const done = verified.filter((r) => r.status === 'done').length;
  const pending = verified.filter((r) => r.status === 'pending').length;

  const priOrder = { P0: 0, P1: 1, P2: 2, P3: 3 };
  const sorted = [...results].sort((a, b) => {
    const pa = priOrder[a.priority] ?? 9;
    const pb = priOrder[b.priority] ?? 9;
    if (pa !== pb) return pa - pb;
    return a.id.localeCompare(b.id);
  });

  const tagRows = Object.entries(todos.byTag)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `| \`${k}\` | ${v} |`)
    .join('\n');

  const tableRows = sorted
    .map((r) => {
      const st = r.manual ? '🟡 Manual' : r.status === 'done' ? '✅ Done' : '⬜ Pending';
      const refs = (r.refs || []).map((x) => `\`${x}\``).join(' ');
      const note = r.note ? `<br><sub>${escapeHtml(r.note)}</sub>` : '';
      const fail =
        r.failures && r.failures.length
          ? `<br><sub>${escapeHtml(r.failures.slice(0, 2).join('; '))}</sub>`
          : '';
      return `| ${r.priority} | \`${r.id}\` | ${st} | ${escapeHtml(r.title)}${note}${fail} | ${refs || '—'} |`;
    })
    .join('\n');

  return `
_Generated: **${generatedAt}** · git: \`${commit || 'n/a'}\` · verified: **${done}/${verified.length}** done, **${pending}** pending, **${manual.length}** manual_

### TODOS.md tag counts (section headers)

| Tag | Count |
|-----|-------|
${tagRows || '| _(no ### [TAG] headers found)_ | — |'}

### Checklist (manifest-driven)

| Priority | ID | Status | Title | Refs |
|----------|-----|--------|-------|------|
${tableRows}

### Recent commits

\`\`\`text
${escapeHtml(gitRecent(10))}
\`\`\`

### Machine snapshot

Full JSON: [\`docs/.implementation-progress.snapshot.json\`](./.implementation-progress.snapshot.json) (commit this file so PRs show diffs).
`.trim();
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const DEFAULT_MANUAL = `<!-- MANUAL_NOTES:START -->
_Add dated bullets here; the sync script preserves your edits between these markers._
<!-- MANUAL_NOTES:END -->`;

function extractManualBlock(prevContent) {
  const s = prevContent.indexOf('<!-- MANUAL_NOTES:START -->');
  const e = prevContent.indexOf('<!-- MANUAL_NOTES:END -->');
  if (s === -1 || e === -1 || e <= s) return DEFAULT_MANUAL;
  return prevContent.slice(s, e + '<!-- MANUAL_NOTES:END -->'.length);
}

function main() {
  const manifest = JSON.parse(read(MANIFEST));
  const items = manifest.items || [];
  const results = items.map(evaluateItem);

  const verified = results.filter((r) => !r.manual);
  const done = verified.filter((r) => r.status === 'done').length;
  const pending = verified.filter((r) => r.status === 'pending').length;

  const generatedAt = new Date().toISOString();
  const commit = gitHead();
  const todos = parseTodosStats();

  const snapshot = {
    generatedAt,
    gitCommit: commit,
    manifestVersion: manifest.version,
    summary: {
      verifiedTotal: verified.length,
      verifiedDone: done,
      verifiedPending: pending,
      manualTotal: results.filter((r) => r.manual).length,
    },
    todosTagCounts: todos.byTag,
    items: results,
  };

  fs.writeFileSync(OUT_JSON, JSON.stringify(snapshot, null, 2), 'utf8');

  const autoBody = buildAutoBody({ generatedAt, commit, todos, results });

  const header = `# Implementation progress

Use this file to **resume implementation** from any machine or session. The **auto block** is regenerated by a script so it stays aligned with the repo.

## How to refresh (required after manifest or checkpoint changes)

\`\`\`bash
npm run progress:sync
\`\`\`

Then commit \`docs/IMPLEMENTATION_PROGRESS.md\` and \`docs/.implementation-progress.snapshot.json\`.

## Sources of truth

| Source | Role |
|--------|------|
| [\`docs/implementation-progress.manifest.json\`](./implementation-progress.manifest.json) | Checklist rules (edit as work is planned or finished) |
| [\`TODOS.md\`](../TODOS.md) | Narrative backlog, spikes, security |
| [\`docs/audits/\`](./audits/) | Gap analyses and delivery order |

## CI

Pull requests run \`npm run progress:check\` — if the tracker is stale, sync locally and commit.

## Manual notes (optional — preserved by the sync script)

${'__MANUAL_BLOCK__'}

${MARK_START}

`;

  const footer = `
${MARK_END}
`;

  const prevManual = fs.existsSync(OUT_MD) ? extractManualBlock(read(OUT_MD)) : DEFAULT_MANUAL;
  const headerFilled = header.replace('__MANUAL_BLOCK__', prevManual);

  let out = `${headerFilled}${autoBody}${footer}`;

  fs.writeFileSync(OUT_MD, out.replace(/\n{3,}/g, '\n\n'), 'utf8');
  console.log('Wrote', path.relative(ROOT, OUT_MD));
  console.log('Wrote', path.relative(ROOT, OUT_JSON));
  console.log(`Summary: ${done}/${verified.length} verified done, ${pending} pending, ${snapshot.summary.manualTotal} manual.`);
}

main();
