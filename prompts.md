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
