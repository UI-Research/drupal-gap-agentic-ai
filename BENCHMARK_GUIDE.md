# Benchmark Guide

A step-by-step guide for running the Drupal Gap benchmark to measure whether loading Drupal-specific context closes the quality gap between Copilot's Drupal output and its JS framework output.

## Prerequisites

- **Docker Desktop** running (required for DDEV)
- **DDEV** installed (`brew install ddev/ddev/ddev`)
- **Node.js 22+** and npm (for NestJS and Strapi environments)
- **Python 3.10+** (for aggregation and report generation)

## Verifying Environments

Before running a benchmark session, confirm all three target environments are up and responding:

```bash
# Drupal (DDEV)
curl -s http://drupal-gap-drupal.ddev.site/jsonapi/node/article | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {len(d[\"data\"])} articles')"

# NestJS
curl -s http://localhost:3000/items

# Strapi
curl -s http://localhost:1337/api/articles | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'OK: {len(d[\"data\"])} articles')"
```

If any environment is not responding, start it:

```bash
# Drupal
cd environments/drupal && ddev start

# NestJS
cd environments/nestjs && npm run start:dev

# Strapi
cd environments/strapi && npm run develop
```

## Running a Benchmark Session

### 1. Verify all environments

Run the verification commands above. All three must return valid responses.

### 2. The orchestrating agent reads `evals/evals.json`

The eval definitions file contains all test cases with their framework, pattern, prompt, and assertions. Each eval has a numeric `id` used to create its output directory.

### 3. For each eval, spawn sub-agents

The orchestrator creates two variants per Drupal eval, one for NestJS, and one for Strapi:

- **without_skill**: Agent receives only the task prompt. No framework-specific context is loaded.
- **with_skill** (Drupal only): Agent receives `context/drupal-skill.md` prepended to the task prompt.

Each sub-agent writes generated code files to:
```
evals/drupal-gap-workspace/iteration-{N}/eval-{ID}/{variant}/
```

### 4. Sub-agents write files to the target environment

The sub-agent implements the task in the appropriate environment, then copies/saves its output files to the workspace directory above.

### 5. Grader agent evaluates outputs

The grader agent (defined in `evals/agents/grader.md`) checks each output against the eval's assertions and writes a `grading.json` file in each variant directory.

### 6. Run aggregation and report

```bash
python evals/aggregate.py --iteration 1
python evals/eval-viewer/generate_report.py --iteration 1
open evals/eval-viewer/report.html
```

## Updating Context to Improve Scores

The benchmark is designed as an iterative loop:

1. **Review `report.html`** — Failed assertions indicate specific knowledge gaps. Look at the evidence field to understand what went wrong.

2. **Edit `context/drupal-skill.md`** — Add the missing patterns, API references, or structural knowledge that would have prevented the failure. Focus on:
   - Correct YAML config structure (services.yml, permissions.yml, routing.yml)
   - Modern API patterns (avoid deprecated hooks)
   - Required annotations and plugin definitions
   - Drupal coding standards

3. **Re-run benchmark with next iteration number**:
   ```bash
   # Run orchestrator targeting iteration 2
   python evals/aggregate.py --iteration 2
   python evals/eval-viewer/generate_report.py --iteration 2
   ```

4. **Compare `benchmark.json` between iterations** — The `delta_pp` value shows improvement. Continue iterating until `gap_closed_by_context` is `true`.

## Interpreting Results

| Metric | Meaning |
|--------|---------|
| `drupal_avg_without` | Copilot's raw Drupal capability (no context loaded) |
| `drupal_avg_with` | Drupal score with `drupal-skill.md` context |
| `nestjs_avg` | NestJS baseline — the "expected" quality level for a well-known framework |
| `strapi_avg` | Strapi baseline — another JS framework reference point |
| `delta_pp` | Percentage points recovered by loading Drupal context |
| `gap_exists` | `true` if Drupal baseline < both JS baselines |
| `gap_closed_by_context` | `true` if Drupal+context reaches ≥90% of the lower JS baseline |

### What the results tell you

- **gap_exists = true, gap_closed_by_context = true**: The gap is real but explained by missing context. The `drupal-skill.md` file is effective.
- **gap_exists = true, gap_closed_by_context = false**: The gap is real and not fully explained by context alone. May indicate deeper model training gaps.
- **gap_exists = false**: No significant quality difference between Drupal and JS frameworks (either Copilot is good at Drupal, or the tasks are too easy).

## Adding New Test Patterns

1. **Add entries to `evals/evals.json`** with a new pattern name. Include entries for all three frameworks (drupal, nestjs, strapi) to maintain paired comparisons.

2. **Include assertions that test known LLM failure modes**:
   - Using deprecated APIs (e.g., `hook_menu()` instead of routing.yml)
   - Wrong config nesting levels
   - Missing required keys in YAML
   - Hallucinated method names
   - Incorrect annotation syntax

3. **Update `evals/agents/grader.md`** if new assertion types are needed beyond `file_exists`, `file_contains`, `file_not_contains`, `command`, and `content_check`.

4. **Run the benchmark** with a new iteration number to get fresh results that include the new patterns.
