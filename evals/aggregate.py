#!/usr/bin/env python3
"""Aggregate grading results into a benchmark.json summary."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_evals_json(evals_path: Path) -> list[dict]:
    """Load the evals definition file."""
    if not evals_path.exists():
        print(f"ERROR: {evals_path} not found", file=sys.stderr)
        sys.exit(1)
    with open(evals_path) as f:
        return json.load(f)


def collect_gradings(iteration_dir: Path) -> list[dict]:
    """Scan eval directories for grading.json files."""
    gradings = []
    eval_dirs = sorted(iteration_dir.glob("eval-*/"))
    for eval_dir in eval_dirs:
        for variant in ("without_skill", "with_skill"):
            grading_path = eval_dir / variant / "grading.json"
            if grading_path.exists():
                try:
                    with open(grading_path) as f:
                        data = json.load(f)
                    data["_source_dir"] = str(eval_dir)
                    gradings.append(data)
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"WARNING: Skipping {grading_path}: {e}", file=sys.stderr)
    return gradings


def aggregate(gradings: list[dict], evals: list[dict]) -> dict:
    """Build the patterns and summary structure."""
    evals_by_id = {e["id"]: e for e in evals}

    # Collect scores grouped by pattern -> framework -> variant
    patterns: dict[str, dict[str, dict[str, float]]] = {}

    for g in gradings:
        eval_id = g.get("eval_id")
        framework = g.get("framework", "")
        pattern = g.get("pattern", "")
        variant = g.get("variant", "")
        score = g.get("score", 0.0)

        # Fall back to evals.json for pattern/framework if not in grading
        if eval_id is not None and eval_id in evals_by_id:
            eval_def = evals_by_id[eval_id]
            if not framework:
                framework = eval_def.get("framework", "")
            if not pattern:
                pattern = eval_def.get("pattern", "")

        if not pattern or not framework or not variant:
            continue

        if pattern not in patterns:
            patterns[pattern] = {}
        if framework not in patterns[pattern]:
            patterns[pattern][framework] = {}

        patterns[pattern][framework][variant] = score

    # Calculate deltas for entries that have both variants
    for pattern_data in patterns.values():
        for fw_data in pattern_data.values():
            if "without_skill" in fw_data and "with_skill" in fw_data:
                fw_data["delta"] = round(fw_data["with_skill"] - fw_data["without_skill"], 4)

    # Build summary
    drupal_without_scores = []
    drupal_with_scores = []
    nestjs_scores = []
    strapi_scores = []

    for pattern_data in patterns.values():
        if "drupal" in pattern_data:
            d = pattern_data["drupal"]
            if "without_skill" in d:
                drupal_without_scores.append(d["without_skill"])
            if "with_skill" in d:
                drupal_with_scores.append(d["with_skill"])
        if "nestjs" in pattern_data:
            n = pattern_data["nestjs"]
            if "without_skill" in n:
                nestjs_scores.append(n["without_skill"])
        if "strapi" in pattern_data:
            s = pattern_data["strapi"]
            if "without_skill" in s:
                strapi_scores.append(s["without_skill"])

    drupal_avg_without = (
        round(sum(drupal_without_scores) / len(drupal_without_scores), 4)
        if drupal_without_scores
        else 0.0
    )
    drupal_avg_with = (
        round(sum(drupal_with_scores) / len(drupal_with_scores), 4)
        if drupal_with_scores
        else 0.0
    )
    nestjs_avg = (
        round(sum(nestjs_scores) / len(nestjs_scores), 4) if nestjs_scores else 0.0
    )
    strapi_avg = (
        round(sum(strapi_scores) / len(strapi_scores), 4) if strapi_scores else 0.0
    )

    delta_pp = round((drupal_avg_with - drupal_avg_without) * 100)

    js_min = min(nestjs_avg, strapi_avg) if (nestjs_avg and strapi_avg) else max(nestjs_avg, strapi_avg)
    gap_exists = drupal_avg_without < js_min if js_min > 0 else False
    gap_closed_by_context = (
        drupal_avg_with >= js_min * 0.9 if js_min > 0 else False
    )

    summary = {
        "drupal_avg_without": drupal_avg_without,
        "drupal_avg_with": drupal_avg_with,
        "delta_pp": delta_pp,
        "nestjs_avg": nestjs_avg,
        "strapi_avg": strapi_avg,
        "gap_exists": gap_exists,
        "gap_closed_by_context": gap_closed_by_context,
    }

    return {"patterns": patterns, "_summary": summary}


def print_summary_table(benchmark: dict) -> None:
    """Print a human-readable summary table to stdout."""
    patterns = benchmark["patterns"]
    summary = benchmark["_summary"]

    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)

    # Header
    print(f"\n{'Pattern':<25} {'Framework':<10} {'No Skill':<10} {'With Skill':<12} {'Delta':<8}")
    print("-" * 70)

    for pattern, frameworks in sorted(patterns.items()):
        for fw, scores in sorted(frameworks.items()):
            without = scores.get("without_skill", "—")
            with_s = scores.get("with_skill", "—")
            delta = scores.get("delta", "—")

            without_str = f"{without:.2f}" if isinstance(without, float) else without
            with_str = f"{with_s:.2f}" if isinstance(with_s, float) else with_s
            delta_str = f"+{delta:.2f}" if isinstance(delta, float) else delta

            print(f"{pattern:<25} {fw:<10} {without_str:<10} {with_str:<12} {delta_str:<8}")

    print("\n" + "-" * 70)
    print("AGGREGATE STATS:")
    print(f"  Drupal (no context):   {summary['drupal_avg_without']:.2f}")
    print(f"  Drupal (with context): {summary['drupal_avg_with']:.2f}")
    print(f"  Delta:                 +{summary['delta_pp']}pp")
    print(f"  NestJS baseline:       {summary['nestjs_avg']:.2f}")
    print(f"  Strapi baseline:       {summary['strapi_avg']:.2f}")
    print(f"  Gap exists:            {summary['gap_exists']}")
    print(f"  Gap closed by context: {summary['gap_closed_by_context']}")
    print("=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Aggregate eval grading results into benchmark.json")
    parser.add_argument("--iteration", type=int, default=1, help="Iteration number (default: 1)")
    args = parser.parse_args()

    evals_dir = Path(__file__).parent
    workspace_dir = evals_dir / "drupal-gap-workspace"
    iteration_dir = workspace_dir / f"iteration-{args.iteration}"

    if not iteration_dir.exists():
        print(f"ERROR: Iteration directory not found: {iteration_dir}", file=sys.stderr)
        sys.exit(1)

    evals_path = evals_dir / "evals.json"
    evals = load_evals_json(evals_path)

    gradings = collect_gradings(iteration_dir)
    if not gradings:
        print(f"WARNING: No grading.json files found in {iteration_dir}", file=sys.stderr)

    result = aggregate(gradings, evals)

    benchmark = {
        "iteration": args.iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **result,
    }

    output_path = iteration_dir / "benchmark.json"
    with open(output_path, "w") as f:
        json.dump(benchmark, f, indent=2)

    print(f"Benchmark saved to: {output_path}")
    print_summary_table(benchmark)


if __name__ == "__main__":
    main()
