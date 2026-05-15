# Prompt Log

A running log of prompts used to build this repository.

---

## 2026-05-15

### Prompt 1 — Initialize repo and create Copilot instructions

> Analyze this codebase and create a .github/copilot-instructions.md file to help future Copilot sessions work effectively in this repository.
>
> **What to include**
> 1. Build, test, and lint commands - If they exist. Include how to run a single test, not just the full suite
> 2. High-level architecture - Focus on the "big picture" that requires reading multiple files to understand
> 3. Key conventions - Patterns specific to this codebase that aren't obvious from reading a single file
>
> **What NOT to include**
> - Generic development practices (e.g., "write unit tests", "use meaningful names")
> - Obvious instructions that any developer would know
> - Exhaustive file/directory listings that can be easily discovered
> - Made-up sections like "Tips for Development" unless they exist in actual docs
> - Explanations of why something ISN'T relevant (just omit it)
>
> **Integration**
> - If .github/copilot-instructions.md already exists, suggest improvements rather than replacing it entirely
> - Incorporate important parts from README.md, CONTRIBUTING.md, or existing instruction files
> - Check for other AI assistant configs and incorporate their important parts
>
> (Tagged: jomiller-drupal-gap-evaluation.docx — the research plan document)

**Result:** Created `.github/copilot-instructions.md` with project purpose, framework analogies, evaluation methodology (Pass 1 / Pass 2, config export diff method), expected repo structure, and key conventions.

---

### Prompt 2 — Initialize git, create log, push to UI-Research org

> Add my initialization prompt (and this prompt and all future prompts) into a log and git init and push this and future efforts to the UI-Research organization in Github.

**Result:** Created `prompts.md`, initialized git repo, created `UI-Research/drupal-gap-agentic-ai` on GitHub, pushed initial commit.

---

### Prompt 3 — Plan the evaluation architecture

> [[PLAN]] mode session using **Claude Opus 4.6** with **high reasoning effort**.
>
> Designed the full evaluation architecture: reproducible benchmark environments (DDEV Drupal 10, Docker NestJS, Docker Strapi), 3 test patterns × 3 frameworks (9 evals), skill-creator–style eval harness with parallel sub-agents, deterministic grader, and visual report generation.

**Result:** Created `plan.md` with detailed architecture overview, repo layout, environment setup (Phase 1), skill definition (Phase 2), 3 test patterns with gotchas and assertions (Phase 3), eval harness structure (Phase 4), visual report generator (Phase 5), and iterative benchmark guide (Phase 6). Model: Claude Opus 4.6, high effort.

---

### Prompt 4 — Create tasks from the plan

> Create tasks from the plan.md

**Result:** Created 9 todos in session DB from plan phases: 3 environment setups (parallel, no deps), drupal-skill → evals-json → grader-agent → aggregate-script → report-generator → benchmark-guide.

---

### Prompt 5 — Begin implementation

> Yes, reminder to log all of my prompts, commit as you go along, and keep track of progress diligently.

**Result:** Full implementation completed across all 6 phases:

- **Phase 1 — Environments:** Drupal 10 DDEV (`drupal-gap-drupal.ddev.site`), NestJS Docker (`:3000/items`), Strapi 5 Docker (`:1337/api/articles`) — all smoke tests passing
- **Phase 2 — Skill:** `context/drupal-skill.md` with routing, DI, events, cron, config export rules
- **Phase 3 — Evals:** `evals/evals.json` — 9 test cases (3 patterns × 3 frameworks) with assertions
- **Phase 4 — Harness:** `evals/agents/grader.md` (5 assertion types), `evals/aggregate.py` (→ benchmark.json)
- **Phase 5 — Report:** `evals/eval-viewer/generate_report.py` (HTML with color-coded scores, gap analysis)
- **Phase 6 — Guide:** `BENCHMARK_GUIDE.md` (prerequisites, running, iterating, interpreting)

---

### Prompt 6 — Run first benchmark cycle

> Ok, let's run our first benchmarking cycle.

**Result:** Completed Iteration 1 with 12 runs (9 without_skill + 3 Drupal with_skill). Model: Claude Opus 4.6, high effort.

| Metric | Score |
|--------|-------|
| Drupal (no context) | 0.87 avg |
| Drupal (with context) | 1.00 avg |
| Delta | +13pp |
| NestJS baseline | 0.93 avg |
| Strapi baseline | 1.00 avg |
| Gap exists | Yes |
| Gap closed by context | Yes |

Key finding: `auto-populate-on-save` pattern revealed the gap — Drupal scored 0.60 without context (missing `NodeInterface` guard and EventSubscriber pattern) vs 1.00 with `drupal-skill.md` loaded.

---

### Prompt 7 — Publish report via GitHub Pages

> Let's also publish the report using github pages.

**Result:** Enabled GitHub Pages serving from `docs/` on `main`. Updated `generate_report.py` to auto-publish to `docs/index.html`. Live at https://ui-research.github.io/drupal-gap-agentic-ai/

---
