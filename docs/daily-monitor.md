# AI-CMS: ChatGPT-reviewed content updates

## Responsibility boundary
- The ChatGPT scheduled task executes each day at **07:00 Japan Standard Time**. It researches the Japanese/Global version, distinguishes publication dates from game-effect dates, cross-checks original official notices and third-party guides, and creates a content-only PR **only if verified information changed**. No GitHub cron or duplicated daily updater is needed.
- This repository hosts the public portal only; personal progression is stored separately in a **private Notion workspace**. Do not commit character profiles or Notion credentials.
- Change only `data/portal.json`, `data/sources.json`, future `data/events.json` / `data/updates.json`, and existing `content/**/*.md` for AI-CMS PRs. Do not touch UI, styles, templates, build code, or configurations. Branch names **must start `cms/`**.
- The `Portal content validation` workflow runs on PRs targeting main and checks tests, build, generated site, and change path restrictions for `cms/` branches.
- Currently **auto-merge is disabled**. A reviewer must confirm CI results and source applicability before merging. Only after observed reliability may conditional GitHub auto-merge/branch protection be enabled.
- Keep published facts stable if sources disagree or acquisition fails. Missing data is not evidence of content deletion. Record source URL, region, published/checked dates and source confidence.
- `scripts/monitor_sources.py` and `data/monitor_sources.json` are optional local HTTP change indicators. They are **not scheduled** and do not claim that a changed HTTP page establishes an actual gameplay update; request access ethically. Human- or AI-verified fact checking takes priority.
- Existing `data/portal.json` has a `checked_at` consistency requirement with corresponding article metadata. Change both when **actual verification** is completed, and never advance dates without reading sources.
- The portal has no runtime JavaScript or CMS login. Git content is the CMS backend. Public site rebuild/deploy remains configured independently of the daily ChatGPT task.

## Operator runbook
1. Read current repository content and last verified source records.
2. Read original official Japan/Global notes, then cross-check international DB/guides. Other region versions are not authoritative for JP/Global.
3. Prepare precise content-only changes, retain citation URLs and correct source/verification dates.
4. Open `cms/YYYY-MM-DD-topic` PR only when verified facts genuinely change.
5. Wait for the `Portal content validation` GitHub check and review results. Do not merge automatically during initial rollout.
6. If a source is unavailable or contradictory, do not invent content or dates; report the limitation instead.
