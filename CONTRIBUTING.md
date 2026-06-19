# Contributing to Traders

## Repo layout

- `apps/trader_app/` — Frappe / ERPNext app (Python)
- `frontend/trader-ui/` — React + Vite SPA
- `docs/` — architecture, audits, governance, **implementation progress**

## Implementation progress tracker

To pick up work from any session, open **`docs/IMPLEMENTATION_PROGRESS.md`**. It includes an auto-generated checklist driven by **`docs/implementation-progress.manifest.json`**.

After you change the manifest, complete a checkpoint, or before opening a PR:

```bash
npm run progress:sync
```

Commit the updated:

- `docs/IMPLEMENTATION_PROGRESS.md`
- `docs/.implementation-progress.snapshot.json`

CI runs `npm run progress:check` on pull requests; if these files are stale, the check fails until you sync and commit.

## Architecture audits

See root `package.json` for `audit:*` scripts and `docs/governance/`.
