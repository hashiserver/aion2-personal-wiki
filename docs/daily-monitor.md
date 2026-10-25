# Daily Global source monitor (MVP)
- Run: `python3 scripts/monitor_sources.py`. Scheduled 07:17 JST via GitHub Actions.
- `data/monitor_sources.json`: allowlisted HTTPS sites. Global applicability must be validated independently.
- `data/source_monitor.json`: timestamps, content hashes, HTTP status and errors; no extracted or copied article body.
- Monitor opens a review PR for observation changes, not an automatic portal rewrite. It does **not** claim that an HTTP change is a game update.
- Verified news, events and daily/weekly descriptions remain manually approved in `data/portal.json` and `data/sources.json`.
- Third-party sites may return anti-bot/403 errors. The last successful digest is preserved, failure explicitly recorded; do not attempt to evade protections.
- Scheduled workflow can require the repository Actions setting “Allow GitHub Actions to create and approve pull requests”. Deploy continues through the existing main-branch process.
- Personal Notion records never enter this public repository.
- Planned next phase: parse officially published update feeds where permitted, compare independent region-tagged claims, build /updates page with source URLs and verified-on dates; no automatic publishing of unverified mechanics.
