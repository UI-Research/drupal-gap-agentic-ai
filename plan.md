# Plan: Drupal Gap — Reproducible Benchmark Environments + Agent-Based Eval

## Context

The research question: *Does GitHub Copilot have a "Drupal gap" vs JS frameworks, and does loading Drupal-specific context close it?*

Following the Anthropics skill-creator evaluation pattern: an orchestrating agent spawns parallel sub-agents per test case — one **with** Drupal context loaded, one **without** — each working in a live environment. Outputs are graded against deterministic assertions and produce a visual benchmark report. The whole cycle is designed to be run repeatedly as context improves.

---

## Architecture Overview

```
Phase 1 ─ Working Environments
┌────────────────────────────────────────────────────────┐
│  DDEV Drupal 10   Docker NestJS   Docker Strapi        │
│  └─ JSON:API      └─ GET /items   └─ GET /api/articles │
│     curl ✓           curl ✓          curl ✓            │
└────────────────────────────────────────────────────────┘
            │
Phase 2 ─ Eval Harness (skill-creator pattern)
            │
┌───────────▼────────────────────────────────────────────┐
│         Orchestrating Agent  (evals/evals.json)        │
│                                                         │
│  for each eval × framework:                             │
│    ├── Spawn sub-agent A: with_skill  ──────────┐      │
│    └── Spawn sub-agent B: without_skill ────────┤      │
│                             (parallel)          │      │
│                                                 ▼      │
│         Live envs ←── agent writes files, runs checks  │
│         Grader ──────────────── grading.json           │
│         aggregate.py ─────────── benchmark.json        │
└────────────────────────────────────────────────────────┘
            │
Phase 3 ─ Visual Report
            │
┌───────────▼────────────────────────────────────────────┐
│  generate_report.py                                     │
│                                                         │
│  Pattern          Drupal         NestJS   Strapi        │
│  Protected Route  w/o: 25% ↑75%  72%      55%          │
│  Scheduled Task   w/o: 33% ↑83%  80%      60%          │
│  Auto-Populate    w/o: 50% ↑88%  85%      65%          │
│                   gap: -50%      baseline  baseline     │
│                   context delta: +40pp                  │
└────────────────────────────────────────────────────────┘
```

---

## Repo Layout

```
envs/
  drupal/
    .ddev/config.yaml            ← DDEV, Drupal 10, SQLite
    web/                          ← Composer-managed docroot
  nestjs/
    docker-compose.yml
    src/                          ← NestJS scaffold + /items endpoint
  strapi/
    docker-compose.yml
    src/                          ← Strapi scaffold + Article content type

context/
  drupal-skill.md                 ← The "skill" under test (Drupal-specific context)

evals/
  evals.json                      ← 9 test cases (3 patterns × 3 frameworks)
  agents/
    grader.md                     ← Grader agent instructions
  eval-viewer/
    generate_report.py            ← Produces visual HTML/markdown benchmark report
  aggregate.py
  drupal-gap-workspace/
    iteration-1/
      eval-{0..8}/
        eval_metadata.json
        with_skill/outputs/
        without_skill/outputs/
        grading.json
      benchmark.json

BENCHMARK_GUIDE.md                ← How to run, update context, re-run, interpret scores
prompts.md                        ← Session log (updated)
```

---

## Phase 1 — Working Environments with Verification

The goal is not just "container starts" — each environment must serve real content over HTTP that proves the full stack is alive. These curl commands are the smoke test run before every benchmark session.

### Drupal

1. Bootstrap Drupal 10 with Composer + DDEV
2. Enable `jsonapi` module + create one `Article` node via `drush`:
   ```bash
   ddev drush en jsonapi -y
   ddev drush php-eval "
     \$node = \Drupal\node\Entity\Node::create([
       'type' => 'article', 'title' => 'Benchmark baseline', 'status' => 1,
     ]); \$node->save();
   "
   ```
3. **Smoke test:** `curl http://drupal-gap-drupal.ddev.site/jsonapi/node/article`  
   → Must return a JSON:API collection with at least one result.

### NestJS

1. Bootstrap NestJS scaffold
2. Add a `ItemsModule` with `ItemsController` returning a hardcoded list:
   ```typescript
   @Get('items')
   findAll() { return [{ id: 1, name: 'Benchmark item' }]; }
   ```
3. **Smoke test:** `curl http://localhost:3000/items`  
   → Must return `[{"id":1,"name":"Benchmark item"}]`

### Strapi

1. Bootstrap Strapi 5 with quickstart
2. Create an `Article` content type via CLI schema, create one entry, set public read permissions in bootstrap:
   ```ts
   // src/index.ts bootstrap()
   await strapi.db.query('plugin::users-permissions.permission').update({
     where: { action: 'api::article.article.find' }, data: { enabled: true }
   });
   ```
3. **Smoke test:** `curl http://localhost:1337/api/articles`  
   → Must return a Strapi v5 response with `data` array containing at least one entry.

All three curl commands must pass before any benchmark run is valid. The state of each environment at this point is captured as the "clean baseline" (committed to git) so every reset is deterministic.

---

## Phase 2 — The Skill Under Test

`context/drupal-skill.md` encodes the Drupal-specific knowledge that should close the gap:
- Config must be exported via `drush cex`, never hand-written
- New permissions require `mymodule.permissions.yml` (not just `_permission` in routing)
- EventSubscribers with service tags are preferred over procedural hooks in modern Drupal
- `hook_menu()` does not exist in Drupal 10
- Services are declared in `mymodule.services.yml` with class + arguments

Pass 1 (without_skill): agent receives only the task prompt  
Pass 2 (with_skill): agent receives `drupal-skill.md` as system context + prompt  
NestJS/Strapi: baseline runs only — no skill variant. They establish the "gap" baseline.

---

## Phase 3 — 3 Test Patterns (9 evals total)

Each prompt is surface-level easy but includes 1–2 predictable LLM failure modes requiring framework-specific knowledge.

### Pattern 1 — Protected Route

**Prompt:** *"Create a new route at `/reports` that returns a list of items and requires authentication."*

| | Drupal | NestJS | Strapi |
|---|---|---|---|
| Gotcha 1 | Omits `permissions.yml` → `_permission` references undefined permission, silently denies all | Generates service but omits `exports: [ReportsService]` → "Cannot inject" at runtime | Uses `strapi.entityService` (v4 deprecated) instead of `strapi.documents()` (v5) |
| Gotcha 2 | Writes `hook_menu()` (Drupal 7, nonexistent in D10) | Applies `@UseGuards()` but doesn't add `AuthModule` to consuming module `imports` | Uses numeric `id` instead of `documentId` (v5 breaking change) |

**Assertions:**
- Drupal: `permissions.yml` exists + defines the permission; `routing.yml` references it; no `hook_menu()`;  `drush cex -y` zero structural diff
- NestJS: `exports` array present in module; `tsc --noEmit` exits 0
- Strapi: no `entityService`; `documentId` used; `tsc --noEmit` exits 0

### Pattern 2 — Scheduled Task

**Prompt:** *"Add a job that runs every day at midnight and logs how many published records exist."*

| | Drupal | NestJS | Strapi |
|---|---|---|---|
| Gotcha 1 | `hook_cron()` fires on cron cadence, not at midnight — time-specific logic needs Queue Worker or Scheduler module | Adds `@Cron()` but forgets `ScheduleModule.forRoot()` in AppModule — decorator silently ignored, cron never fires | Writes `strapi.config.cron` (v4) or a free-standing file that is never auto-discovered |
| Gotcha 2 | Long-running `hook_cron()` blocks all other cron tasks (Queue Worker is correct pattern) | Forgets to add the task service to AppModule `providers` | Puts cron logic in a service expecting Strapi to call it without registration |

**Assertions:**
- Drupal: `drush cron` exits 0; Queue Worker tagged correctly if used
- NestJS: `ScheduleModule.forRoot()` in AppModule imports; `tsc --noEmit` exits 0
- Strapi: cron in `config/cron-tasks.ts` or via `strapi.cron.add()`; no `strapi.config.cron`

### Pattern 3 — Auto-Populate on Save

**Prompt:** *"When a new Article is created, automatically set a `slug` field from the title."*

| | Drupal | NestJS | Strapi |
|---|---|---|---|
| Gotcha 1 | Procedural `hook_entity_presave()` works but EventSubscriber with service tag is preferred — config export diff surfaces which was chosen | Slug logic placed in controller instead of entity/service layer | Lifecycle logic placed in service file — Strapi ignores it, doesn't auto-discover |
| Gotcha 2 | Missing entity type guard (`$entity instanceof NodeInterface`) — runs on all entities | Uses `@AfterInsert()` instead of `@BeforeInsert()` — too late | Uses `afterCreate` and throws an error (only `beforeX` hooks should throw) |

**Assertions:**
- Drupal: EventSubscriber service tag present OR `hook_entity_presave()` with entity type guard; config export clean
- NestJS: Logic in entity subscriber or service (not controller); `@BeforeInsert()` used; `tsc --noEmit` exits 0
- Strapi: File at correct lifecycle path; `beforeCreate` exported; no error-throw in `afterCreate`

---

## Phase 4 — Eval Harness

### `evals/evals.json` structure

```json
{
  "skill_name": "drupal-gap-benchmark",
  "evals": [
    {
      "id": 0,
      "framework": "drupal",
      "pattern": "protected-route",
      "prompt": "In the Drupal environment (envs/drupal, running via DDEV), create a custom module called `reports` with a route at /reports returning published nodes. The user must have a custom 'access reports' permission to view it.",
      "expected_output": "Module with reports.routing.yml, reports.permissions.yml, and a Controller class",
      "env_reset": "git checkout -- envs/drupal/web/modules/custom/",
      "assertions": [
        { "name": "permissions-yml-exists", "description": "reports.permissions.yml defines 'access reports'" },
        { "name": "routing-references-permission", "description": "reports.routing.yml uses _permission: 'access reports'" },
        { "name": "no-hook-menu", "description": "No hook_menu() in generated code" },
        { "name": "drush-cex-clean", "description": "drush cex -y produces zero structural diff" }
      ]
    }
    // evals 1-8: nestjs + strapi for pattern 1, all three for patterns 2-3
  ]
}
```

### Sub-agent invocation (spawned in parallel per eval)

**With-skill (Drupal only):**
```
You are working in the Drupal 10 environment at envs/drupal (DDEV running).
Skill context: [contents of context/drupal-skill.md]
Task: [eval prompt]
Before starting, run: git checkout -- envs/drupal/web/modules/custom/
Write all generated files, then run: ddev drush cex -y
Save outputs to: evals/drupal-gap-workspace/iteration-1/eval-{id}/with_skill/outputs/
```

**Without-skill (baseline):**
```
You are working in the Drupal 10 environment at envs/drupal (DDEV running).
Task: [eval prompt]
Before starting, run: git checkout -- envs/drupal/web/modules/custom/
Write all generated files, then run: ddev drush cex -y
Save outputs to: evals/drupal-gap-workspace/iteration-1/eval-{id}/without_skill/outputs/
```

### Grader (`evals/agents/grader.md`)

For each eval the grader runs deterministic checks and emits `grading.json`:
```json
{
  "expectations": [
    { "text": "permissions-yml-exists", "passed": true,  "evidence": "File found at reports/reports.permissions.yml with 'access reports' key" },
    { "text": "no-hook-menu",           "passed": false, "evidence": "hook_menu() found in reports.module at line 12" }
  ]
}
```

### `benchmark.json` shape (output of `aggregate.py`)

```json
{
  "protected-route": {
    "drupal":  { "without_skill": 0.25, "with_skill": 0.75, "delta": 0.50 },
    "nestjs":  { "without_skill": 0.75 },
    "strapi":  { "without_skill": 0.50 }
  },
  "scheduled-task":      { ... },
  "auto-populate-on-save": { ... },
  "_summary": {
    "drupal_avg_without": 0.36,
    "drupal_avg_with":    0.79,
    "delta_pp":           43,
    "nestjs_avg":         0.80,
    "strapi_avg":         0.58
  }
}
```

---

## Phase 5 — Visual Report (`generate_report.py`)

Produces an HTML report (same style as skill-creator viewer) with:

- **Score table** — each pattern × framework, with/without skill, delta highlighted
- **Gap analysis** — Drupal baseline vs NestJS/Strapi baseline (is there a gap?)
- **Context delta** — how many percentage points does loading `drupal-skill.md` recover?
- **Per-assertion breakdown** — which specific assertions pass/fail most often
- **Evidence excerpts** — grader evidence for failed assertions

Run: `python evals/eval-viewer/generate_report.py`  
Output: `evals/eval-viewer/report.html` (open in browser)

---

## Phase 6 — `BENCHMARK_GUIDE.md` (Iterative Workflow)

This file documents the expected iterative cycle. Sections:

### Running a benchmark session
```bash
# 0. Verify all environments healthy (run before every session)
ddev start && curl http://drupal-gap-drupal.ddev.site/jsonapi/node/article
curl http://localhost:3000/items
curl http://localhost:1337/api/articles

# 1. Run all evals (orchestrating agent reads evals/evals.json)
#    Spawns sub-agents, collects outputs, runs grader
# See: evals/evals.json for test case definitions

# 2. Aggregate + report
python evals/aggregate.py
python evals/eval-viewer/generate_report.py
open evals/eval-viewer/report.html
```

### Updating context to improve scores
1. Look at failed assertions in `report.html` — they point to which knowledge is missing
2. Add the missing pattern/rule to `context/drupal-skill.md`
3. Re-run the benchmark: `iteration-2/` is created automatically
4. Compare `benchmark.json` delta between iterations

### Interpreting the scores
- **Drupal without_skill** — Copilot's raw capability on Drupal tasks
- **NestJS / Strapi baselines** — equivalent tasks in frameworks with more training data
- **delta** — how much `drupal-skill.md` recovers; target: delta ≥ 0.40 (close gap to JS baseline)
- **Assertion breakdown** — shows *which* failures are systematic (gotcha patterns) vs random

### Adding a new test pattern
1. Add to `evals/evals.json` with new id, framework, assertions
2. Add expected output files to `evals/test-patterns/<pattern-name>/`
3. Update `evals/agents/grader.md` with new assertion checks
4. Run benchmark

---

## File Creation Order

1. `envs/drupal/.ddev/config.yaml` + Composer scaffold → `ddev start` → seed content → smoke test
2. `envs/nestjs/docker-compose.yml` + NestJS scaffold + `/items` endpoint → smoke test
3. `envs/strapi/docker-compose.yml` + Strapi scaffold + Article content type + public perms → smoke test
4. `context/drupal-skill.md`
5. `evals/evals.json` — all 9 test cases
6. `evals/agents/grader.md`
7. `evals/aggregate.py`
8. `evals/eval-viewer/generate_report.py`
9. `BENCHMARK_GUIDE.md`
10. `prompts.md` — append session entry

---

## Sources

- [Anthropics skill-creator SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
- [Drupal routing + permissions structure](https://www.drupal.org/docs/drupal-apis/routing-system/structure-of-routes)
- [NestJS: Why services won't inject](https://dev.to/adamthedeveloper/nestjs-dependency-injection-why-your-services-wont-inject-and-how-to-fix-it-properly-3phf)
- [Strapi 5: Entity Service deprecated](https://docs.strapi.io/cms/migration/v4-to-v5/breaking-changes/entity-service-deprecated)
- [Strapi 5: documentId vs id](https://docs.strapi.io/cms/migration/v4-to-v5/breaking-changes/use-document-id)
- [Strapi v5 lifecycle hook issues](https://github.com/strapi/strapi/issues/20551)
- [7 common Strapi 5 mistakes](https://strapi.io/blog/common-mistakes-when-starting-with-strapi)
- [Avoid circular deps in NestJS](https://blog.logrocket.com/avoid-circular-dependencies-nestjs/)
