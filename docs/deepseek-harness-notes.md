# DeepSeek Harness — notes from building this project

Issue 4 of this repo asks for setup notes on DeepSeek Harness (developer
preview, released 2026-08-13). This project was built **inside** DeepSeek
Harness end to end — the triage agent, data pipeline, dashboard, and docs were
all produced by a Harness agent session. Notes below are honest observations,
including rough edges.

## What DeepSeek Harness is (as experienced here)

- An open-source AI agent framework: a long-running agent with tools
  (bash, file read/write/edit, web search, background jobs, subagents,
  goals/workflows) working inside a sandboxed workspace.
- The agent runs through a web GUI (`dsh web`) that boots the app at a local
  URL; file changes land in the repo and are visible after rebuilds/refreshes.
- Structured workflow features: goals (persisted multi-round objectives),
  subagents for delegation, background jobs for long-running work, and
  `ask_user_question` for human-in-the-loop checkpoints.

## What worked well

- **Long-running objective support** — the "build the whole pipeline" goal
  persisted across rounds and kept the work anchored.
- **Background jobs** — long downloads (STAC metadata, masks, previews) ran in
  the background while other work (agent code, docs) proceeded in parallel.
- **Tool discipline** — read/edit/write for files, glob/grep for discovery,
  background jobs with `job_output` — everything is observable and auditable.

## Rough edges / surprises

1. **No image input for the default model** — the agent could not *see* the
   downloaded previews/thumbnails (model lacks image input), so scene
   selection had to be evidence-based from mask statistics. That turned out to
   be the *right* constraint for this project (QA should be mechanical, not
   "looks bad"), but it was a genuine limitation to work around.
2. **File sandbox semantics** — some operations (e.g. pip installs into a
   Homebrew Python) were blocked by PEP 668 / sandbox policies; a project
   virtualenv solved it cleanly.
3. **Rate limits on upstream hosts** (Wyvern's data CDN) required retry/backoff
   logic in download scripts — not a Harness issue, but worth noting that
   long data pulls need to be written defensively.
4. **Client-plugin HMR** requires a dev watcher; shell/plain-package changes
   need a rebuild + refresh to show in the GUI — minor friction when
   iterating on the dashboard.

## Bottom line

Harness worked as the agent framework for this whole build: real data pulled,
real agent run, real dashboard — all produced by the agent in this repo.
Setup steps for the project itself are in [`agent/SETUP.md`](../agent/SETUP.md).
