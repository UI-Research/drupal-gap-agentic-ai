# Copilot Instructions

## Project Purpose

This repository is a structured evaluation of GitHub Copilot's output quality across three framework targets: **Drupal (PHP)**, **NestJS (TypeScript)**, and **Strapi (Node.js)**. The goal is to test whether any performance gap between Drupal and JS frameworks is explained by framework-specific knowledge gaps rather than language (PHP vs TS/JS).

The research question: *Does the Drupal gap actually exist, and if so, does loading Drupal-specific context close it?*

## Evaluation Architecture

Tasks are **paired across all three frameworks** by what they're actually testing — not by language. Each task triple tests one of these capabilities:

| Task type | Drupal | NestJS | Strapi |
|---|---|---|---|
| Service registration | `services.yml` + DI | `@Injectable()` provider | Service in `register()` |
| Event/lifecycle interception | Hook or EventSubscriber | Interceptor / Guard | Lifecycle hook |
| Schema definition | Config entity YAML | TypeORM entity / DTO | Content type schema |
| Custom extension points | Plugin (annotation-based) | Custom decorator / module | Plugin API |

## Framework Analogies (Critical Context)

**Drupal ↔ NestJS** is the *architectural* analog:
- Drupal DI container (`services.yml`) = NestJS DI container (`@Module` providers)
- Drupal plugins (annotation discovery) = NestJS decorators + metadata
- Drupal event subscribers = NestJS interceptors/guards
- Drupal hooks = NestJS lifecycle hooks + module `onModuleInit`

**Drupal ↔ Strapi** is the *CMS domain* analog:
- Drupal module = Strapi plugin
- Drupal hook = Strapi lifecycle hook
- Drupal service = Strapi service in `./src/api/<name>/services/`
- Drupal content entity = Strapi content type

## Evaluation Methodology

### Pass 1 (no context)
Run each task with no Drupal-specific context loaded. Record:
- Whether output is deployable without revision
- Number of revision cycles required
- Type of error (wrong API, hallucinated method, wrong config structure, etc.)

### Pass 2 (context loaded — Drupal tasks only)
Reload with `AGENTS.md` (tailored to the UI repos) plus skills from the `ai_best_practices` Drupal project. Re-run the same Drupal tasks and measure delta.

### Accuracy baseline for Drupal tasks — the config export diff method
1. Make the change through the Drupal UI
2. Export config: `lando drush cex -y`
3. Diff the exported YAML against what Copilot produced
4. A passing result = zero structural diff (values may differ, structure must match)

### Metrics to record per task
- `deployable_without_revision`: boolean
- `revision_cycles`: integer
- `error_types`: list of categories (wrong API, hallucinated method, config structure, etc.)
- `pass`: `1` (no context) or `2` (context loaded)
- `framework`: `drupal` | `nestjs` | `strapi`

## Repository Structure (expected)

```
tasks/
  drupal/        # PHP task files + expected config YAML
  nestjs/        # TypeScript task files
  strapi/        # Node.js task files
results/
  pass1/         # Raw outputs, diffs, and scores from no-context run
  pass2/         # Raw outputs, diffs, and scores from context-loaded run
context/
  AGENTS.md      # Drupal-specific agent context for Pass 2
  ai_best_practices/  # Skills/snippets from the ai_best_practices Drupal module
```

## Key Conventions

- Each task file should be self-contained: include the prompt given to Copilot, the raw output received, and the evaluation result.
- Drupal config diffs go in `results/pass*/drupal/<task-name>.diff`
- NestJS and Strapi tasks are evaluated by manual code review, not config diff.
- The unit of comparison is the **task triple** (same capability, three frameworks). Do not compare tasks that aren't equivalent in complexity.
- When writing Pass 2 context for `AGENTS.md`, draw from the actual `UI-Research/urban-main-site` repo conventions — that's the production Drupal codebase being used as the baseline.
