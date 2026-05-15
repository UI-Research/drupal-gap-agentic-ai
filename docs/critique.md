# Critique of the Drupal Gap Benchmark Methodology

*Evaluated against established evidence-based standards for LLM code generation assessment.*

---

## Reference Benchmarks Consulted

| Benchmark | Citation | Relevance |
|---|---|---|
| **HumanEval** | Chen et al., 2021 (arXiv:2107.03374) | Functional-correctness baseline using pass@k against test suites |
| **EvalPlus** | Liu et al., 2023 (arXiv:2305.01210) | Showed static assertions under-count failures by 19–29% |
| **SWE-bench** | Jimenez et al., 2023 (arXiv:2310.06770) | Real-world multi-file issues; gold standard for framework-level tasks |
| **ClassEval** | Du et al., 2023 (arXiv:2308.01861) | Class-level generation; method-level results don't transfer |
| **τ-bench** | Yao et al., 2024 (arXiv:2406.12045) | Reliability over multiple trials; introduced pass^k consistency metric |
| **CodeT** | Chen et al., 2022 (arXiv:2207.10397) | Dual-execution agreement; self-generated test cases miss bugs |

---

## Our Results (Iteration 1 Summary)

| Metric | Value |
|---|---|
| Drupal (no context) | 0.87 avg |
| Drupal (with context) | 1.00 avg |
| Delta | +13 pp |
| NestJS baseline | 0.93 avg |
| Strapi baseline | 1.00 avg |
| Gap exists | Yes |
| Gap closed by context | Yes |

The gap was localized entirely to the **auto-populate-on-save** Drupal eval (0.60 without context), driven by two failed assertions: missing `NodeInterface` guard and no EventSubscriber pattern.

---

## Critiques

### 1. Sample Size Is Too Small to Support Causal Claims

**Problem:** 3 patterns × 3 frameworks = 9 evals total. The Drupal "gap" is a difference of **1 eval** (eval-6 scoring 0.60 vs 1.00 across all others). With N=3 per framework, a single eval outcome determines whether the gap "exists."

**Evidence-based standard:** SWE-bench uses 2,294 problems. EvalPlus uses 164 HumanEval + 378 MBPP problems at minimum. ClassEval uses 100 class-level tasks. The field norm is 100+ samples before drawing distributional conclusions.

**Recommended fix:** Expand to ≥10 patterns per framework (30+ evals) before reporting `gap_exists` as a finding. Current data supports "gap detected in one case" not "systematic gap."

---

### 2. The Grader Has the Same Failure Modes It Is Testing For

**Problem:** The grader agent is an LLM (Claude Opus 4.6) evaluating outputs produced by the same model family. Assertions like `"event-subscriber-preferred"` require semantic judgment: the grader must decide whether the implementation satisfies the spirit of the assertion, not just pattern-match strings.

**Evidence-based standard:** EvalPlus found that LLM-generated test cases miss 19–29% of bugs that augmented ground-truth test suites catch. CodeT's dual-execution agreement shows that self-referential evaluation inflates pass rates. τ-bench explicitly separates the evaluating LM from the generating LM.

**In our data:** eval-6 `without_skill` received `passed: false` for `event-subscriber-preferred` with evidence: *"No EventSubscriber with service tag found"* — but this is correct behavior for a procedural hook implementation. The grader conflated "preferred pattern absent" with "wrong pattern used," which is a semantic judgment call, not a deterministic check.

**Recommended fix:** Separate deterministic assertions (file exists, string pattern, compile check) from preference assertions. Deterministic checks are reliable; preference checks need human review or execution verification.

---

### 3. The Most Important Assertion (`drush-cex-clean`) Was Never Actually Executed

**Problem:** The original plan called for `drush cex -y` producing a zero structural diff as the gold-standard Drupal accuracy check. Reviewing `grading.json` files for Drupal evals, this assertion does not appear in any of them. The grader evaluated file structure and string patterns instead.

**Evidence-based standard:** SWE-bench's key innovation is using the repository's *existing test suite* as the oracle — not LLM judgment. Running `drush cex` and diffing is our equivalent: it's deterministic, framework-authoritative, and not gameable by the grader.

**Impact:** The Drupal scores may be overstated. Code that has the right file names and string patterns but wrong YAML nesting would pass our grader but fail `drush cex`. This is especially relevant for the protected-route eval (routing.yml + permissions.yml structure).

**Recommended fix:** Implement actual DDEV execution in the eval loop. The environment exists — the harness just doesn't use it.

---

### 4. No pass@k Sampling — Single-Sample Results Have High Variance

**Problem:** Each eval is run once per variant. HumanEval's original contribution was the `pass@k` metric precisely because single-sample results are noisy. An LLM that generates correct code 60% of the time would score either 0.0 or 1.0 per assertion in our framework.

**Evidence-based standard:** Chen et al. (2021) show that a model solving 28.8% of problems at pass@1 solves 70.2% at pass@100. τ-bench introduces `pass^k` (all k trials must pass) to measure *reliability*, not just peak capability.

**In our data:** The `auto-populate-on-save` without_skill score of 0.60 could reflect a model that nearly always produces the wrong pattern, or one that produces it correctly 80% of the time but happened to fail on this run. We cannot distinguish these.

**Recommended fix:** Run each eval 3–5 times, report mean ± std. Low-cost mitigation: add temperature=0 for the "without_skill" runs to reduce variance in the baseline.

---

### 5. Context-Leak Bias: The Skill Was Written *After* Observing the Gap

**Problem:** `context/drupal-skill.md` was authored knowing which assertions would fail. The `NodeInterface` rule and EventSubscriber preference appear in the skill document specifically because they were identified as failure modes during task design — before the benchmark ran. This is training-on-test-set contamination.

**Evidence-based standard:** EvalPlus and SWE-bench use held-out test cases specifically to prevent this. The skill under evaluation should be written without knowledge of the specific assertions.

**In our data:** The `with_skill` run for eval-6 scores 1.00, with evidence showing `NodeInterface` used exactly as the skill prescribes. This is expected — but it validates the skill document as a solution spec, not as a genuine test of whether LLM knowledge improves with context.

**Recommended fix:** Add a **held-out eval set** (patterns 4–6) not referenced in `drupal-skill.md`. The `with_skill` improvement on held-out evals would be a much stronger signal than improvement on in-distribution evals.

---

### 6. Inter-Rater Reliability Is Unmeasured

**Problem:** Assertion grades are produced by a single LLM run with no human spot-check or inter-rater agreement calculation. In eval-6, the `entity-type-guard` assertion passed for `getEntityTypeId() !== 'node'` in one run and failed it in another run's preamble — the difference was which implementation was generated, but the grader's judgment threshold for "acceptable guard" is undefined.

**Evidence-based standard:** Standard practice in NLP evaluation (e.g., SQuAD, BIG-Bench) requires either deterministic evaluation or human inter-rater agreement (Cohen's κ ≥ 0.7 is typical). For non-deterministic assertions, agreement between 2–3 grader runs should be measured.

**Recommended fix:** For subjective assertions, run the grader twice and flag disagreements for human review. Alternatively, convert subjective assertions to deterministic ones (e.g., `grep -r 'NodeInterface'` instead of "entity type guard present").

---

### 7. The NestJS/Strapi Baselines Are Not Task-Equivalent in Difficulty

**Problem:** The plan acknowledges that the three framework tasks are "paired" but the assertions have different strictness levels. Strapi's protected-route eval checks 5 assertions; the NestJS eval checks 5 assertions; the Drupal eval checks 4. More importantly, the NestJS assertions include `tsc --noEmit` (a machine-verified check) while Drupal's `drush-cex-clean` was not executed. This means NestJS scores are held to a harder standard than Drupal scores — which would *understate* the Drupal gap, not overstate it, but still makes cross-framework comparison unreliable.

**Recommended fix:** Standardize assertion count and types across frameworks. All three should include at least one execution-verified check.

---

## Summary Assessment

| Criterion | Status | Severity |
|---|---|---|
| Sample size | ❌ N=3 per framework | High — undermines distributional claims |
| Execution verification | ❌ `drush cex` not run | High — gold standard omitted |
| Grader independence | ⚠️ Same model family | Medium — inflates with/without delta |
| pass@k sampling | ❌ Single sample | Medium — high variance in reported scores |
| Context-leak bias | ⚠️ Skill written against known failures | Medium — limits generalizability claim |
| Inter-rater reliability | ❌ Unmeasured | Medium — subjective assertions ungated |
| Cross-framework equivalence | ⚠️ Assertion strictness varies | Low — directionally consistent but noisy |

**Bottom line:** Iteration 1 results are best described as a **proof of concept** that the eval infrastructure works and that at least one Drupal pattern (entity type guard + EventSubscriber) is predictably improved by context loading. They are not sufficient to claim a *systematic* Drupal gap with statistical confidence. The infrastructure is sound; expanding sample size, executing `drush cex`, and adding a held-out eval set would produce publishable findings.

---

*Report generated: 2026-05-15. Sources: arXiv abstracts for HumanEval (2107.03374), EvalPlus (2305.01210), SWE-bench (2310.06770), ClassEval (2308.01861), τ-bench (2406.12045), CodeT (2207.10397).*
