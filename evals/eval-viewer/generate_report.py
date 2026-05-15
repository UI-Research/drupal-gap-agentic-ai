#!/usr/bin/env python3
"""Generate an HTML report from benchmark.json and individual grading files."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_all_benchmarks(workspace_dir: Path) -> list[dict]:
    """Load benchmark.json from every iteration directory, sorted by iteration."""
    results = []
    for p in sorted(workspace_dir.glob("iteration-*/benchmark.json")):
        try:
            with open(p) as f:
                data = json.load(f)
            results.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return results


def score_color(score: float) -> str:
    """Return CSS color class based on score threshold."""
    if score >= 0.8:
        return "#2d8a4e"  # green
    elif score >= 0.5:
        return "#b08800"  # yellow/amber
    else:
        return "#cf222e"  # red


def score_bg(score: float) -> str:
    """Return CSS background color based on score threshold."""
    if score >= 0.8:
        return "#dafbe1"
    elif score >= 0.5:
        return "#fff8c5"
    else:
        return "#ffebe9"


def generate_findings_summary(benchmarks: list[dict]) -> str:
    """Generate the Findings Summary section from all available iterations."""
    if not benchmarks:
        return ""

    latest = benchmarks[-1]
    s = latest.get("_summary", {})
    iteration = latest.get("iteration", len(benchmarks))
    n_patterns = len(latest.get("patterns", {}))

    gap_exists = s.get("gap_exists", False)
    gap_closed = s.get("gap_closed_by_context", False)
    drupal_without = s.get("drupal_avg_without", 0)
    drupal_with = s.get("drupal_avg_with", 0)
    nestjs_avg = s.get("nestjs_avg", 0)
    strapi_avg = s.get("strapi_avg", 0)
    delta_pp = s.get("delta_pp", 0)

    # Cross-iteration trend
    if len(benchmarks) >= 2:
        prev = benchmarks[-2].get("_summary", {})
        prev_drupal_without = prev.get("drupal_avg_without", 0)
        prev_gap = prev.get("gap_exists", False)
        drupal_trend = drupal_without - prev_drupal_without
        trend_text = f"Drupal baseline moved {drupal_trend:+.2f} from iteration {benchmarks[-2]['iteration']} to {iteration}."
        if prev_gap and not gap_exists:
            trend_text += " The Drupal gap that appeared in earlier iterations has been eliminated."
        elif not prev_gap and not gap_exists:
            trend_text += " No gap has been detected in either run."
        elif prev_gap and gap_exists:
            trend_text += " The gap persists across iterations."
    else:
        trend_text = "This is the first iteration; no cross-iteration trend available."

    # Determine headline verdict
    if not gap_exists:
        verdict_color = "#2d8a4e"
        verdict_bg = "#dafbe1"
        verdict_icon = "✅"
        verdict_text = "No Drupal gap detected"
        verdict_detail = (
            f"Copilot's Drupal output quality ({drupal_without:.2f}) is competitive with "
            f"NestJS ({nestjs_avg:.2f}) and Strapi ({strapi_avg:.2f}) across all {n_patterns} patterns tested."
        )
    elif gap_closed:
        verdict_color = "#b08800"
        verdict_bg = "#fff8c5"
        verdict_icon = "⚠️"
        verdict_text = "Gap exists but closes with context"
        verdict_detail = (
            f"Drupal baseline ({drupal_without:.2f}) is below JS frameworks, but loading "
            f"drupal-skill.md raises it to {drupal_with:.2f} (+{delta_pp}pp), closing the gap."
        )
    else:
        verdict_color = "#cf222e"
        verdict_bg = "#ffebe9"
        verdict_icon = "❌"
        verdict_text = "Gap exists and is not closed by context"
        verdict_detail = (
            f"Drupal baseline ({drupal_without:.2f}) is below JS frameworks and context only adds +{delta_pp}pp, "
            "suggesting a deeper model training gap beyond what skill context can address."
        )

    # Notable findings bullets
    findings = []
    # Check if any pattern had a gap
    patterns_with_gap = []
    for pname, pdata in latest.get("patterns", {}).items():
        d_without = pdata.get("drupal", {}).get("without_skill")
        n = pdata.get("nestjs", {}).get("without_skill")
        st = pdata.get("strapi", {}).get("without_skill")
        if d_without is not None and n is not None and st is not None:
            if d_without < min(n, st):
                patterns_with_gap.append((pname, d_without, n, st))

    if patterns_with_gap:
        for pname, dw, n, st in patterns_with_gap:
            findings.append(f"Pattern <strong>{pname}</strong>: Drupal without_skill={dw:.2f}, NestJS={n:.2f}, Strapi={st:.2f}.")
    else:
        findings.append("All patterns: Drupal performed equal to or better than both JS frameworks without context.")

    # Assertion fix impact
    if len(benchmarks) >= 2:
        prev_patterns = benchmarks[-2].get("patterns", {})
        improved = []
        for pname in latest.get("patterns", {}):
            if pname in prev_patterns:
                prev_d = prev_patterns[pname].get("drupal", {}).get("without_skill", 1.0)
                curr_d = latest["patterns"][pname].get("drupal", {}).get("without_skill", 1.0)
                if curr_d > prev_d + 0.05:
                    improved.append(f"{pname}: {prev_d:.2f} → {curr_d:.2f}")
        if improved:
            findings.append(
                f"Patterns that improved Drupal score between iterations: {', '.join(improved)}. "
                "These improvements followed assertion fixes (e.g., removing phantom class checks)."
            )

    findings_html = "".join(f"<li>{f}</li>" for f in findings)

    return f"""
    <div style="background:{verdict_bg};border:2px solid {verdict_color};border-radius:8px;padding:1.5em;margin-bottom:1.5em;">
        <h2 style="border:none;margin-top:0;color:{verdict_color}">{verdict_icon} Findings Summary</h2>
        <p style="font-size:1.1em;font-weight:600;color:{verdict_color};margin-bottom:0.5em">{verdict_text}</p>
        <p style="margin-bottom:1em">{verdict_detail}</p>
        <p style="color:#656d76;font-size:0.9em;margin-bottom:1em">{trend_text}</p>
        <ul style="padding-left:1.5em;font-size:0.95em">
            {findings_html}
        </ul>
    </div>
    """


def generate_iteration_comparison(benchmarks: list[dict]) -> str:
    """Generate an iteration-by-iteration comparison table and changelog."""
    if len(benchmarks) < 2:
        return ""

    # Build comparison table rows
    rows = []
    for b in benchmarks:
        s = b.get("_summary", {})
        it = b.get("iteration", "?")
        ts = b.get("timestamp", "")[:10]
        n_patterns = len(b.get("patterns", {}))
        d_without = s.get("drupal_avg_without", 0)
        d_with = s.get("drupal_avg_with", 0)
        delta = s.get("delta_pp", 0)
        nestjs = s.get("nestjs_avg", 0)
        strapi = s.get("strapi_avg", 0)
        gap = "Yes ⚠️" if s.get("gap_exists") else "No ✅"
        closed = "Yes ✅" if s.get("gap_closed_by_context") else "No ❌"
        rows.append(
            f"<tr><td style='font-weight:600'>Iter {it}</td><td>{ts}</td><td>{n_patterns}</td>"
            f"<td style='font-weight:bold;color:{score_color(d_without)}'>{d_without:.2f}</td>"
            f"<td style='font-weight:bold;color:{score_color(d_with)}'>{d_with:.2f}</td>"
            f"<td style='color:{'#2d8a4e' if delta > 0 else '#666'}'>{delta:+d}pp</td>"
            f"<td style='font-weight:bold;color:{score_color(nestjs)}'>{nestjs:.2f}</td>"
            f"<td style='font-weight:bold;color:{score_color(strapi)}'>{strapi:.2f}</td>"
            f"<td>{gap}</td><td>{closed}</td></tr>"
        )

    table_rows = "\n".join(rows)

    # Changelog entries (hard-coded per-iteration annotations)
    changelogs = {
        1: [
            "Initial benchmark: 3 patterns × 3 frameworks = 9 evals (18 variants incl. with_skill).",
            "Assertion types: mix of <code>content_check</code> (semantic) and deterministic checks.",
            "Drupal auto-populate-on-save scored 0.60 without_skill — <code>hook-or-subscriber</code> assertion "
            "checked for <code>EntityEvents</code>, a class that does not exist in Drupal 10 core.",
            "Critique report written; 7 methodology issues identified vs HumanEval/SWE-bench standards.",
        ],
        2: [
            "Benchmark overhauled: 6 patterns × 3 frameworks = 18 evals (24 variants). "
            "3 held-out patterns added (config-settings-form, block-plugin, rest-resource).",
            "All <code>content_check</code> assertions replaced with deterministic <code>file_contains</code> / "
            "<code>file_not_contains</code> / <code>command</code> checks.",
            "4 broken assertions fixed: <code>EntityEvents</code> → <code>EventSubscriberInterface</code>; "
            "<code>@Block</code> → <code>Block(</code>; <code>@RestResource</code> → <code>RestResource(</code>; "
            "<code>strapi.cron.add(</code> → <code>tasks:</code>.",
            "Drupal gap eliminated: Drupal baseline rose from 0.87 → 1.00 after assertion fixes. "
            "The previous gap in auto-populate-on-save was caused by a phantom class assertion, not model behavior.",
            "<code>drush-en-simulate</code> added to all Drupal evals; <code>tsc --noEmit</code> added to all "
            "NestJS and Strapi evals. DDEV live during this run — 0 assertions skipped.",
        ],
    }

    changelog_html = ""
    for b in benchmarks:
        it = b.get("iteration", 0)
        entries = changelogs.get(it, [])
        if entries:
            items = "".join(f"<li style='margin-bottom:0.4em'>{e}</li>" for e in entries)
            changelog_html += f"""
            <div style="margin-bottom:1.2em">
                <h3 style="margin-bottom:0.4em">Iteration {it}</h3>
                <ul style="padding-left:1.5em;font-size:0.9em;color:#1f2328">{items}</ul>
            </div>"""

    return f"""
    <h2>Iteration History</h2>
    <div class="card">
        <table>
            <thead>
                <tr>
                    <th>Iteration</th><th>Date</th><th>Patterns</th>
                    <th>Drupal (no ctx)</th><th>Drupal (ctx)</th><th>Δ</th>
                    <th>NestJS</th><th>Strapi</th><th>Gap?</th><th>Closed?</th>
                </tr>
            </thead>
            <tbody>{table_rows}</tbody>
        </table>
    </div>
    <h2>What Changed Between Iterations</h2>
    <div class="card">
        {changelog_html}
    </div>
    """


def load_grading_details(iteration_dir: Path) -> dict:
    """Load all grading.json files for per-assertion breakdown."""
    details = {}
    for grading_path in sorted(iteration_dir.glob("eval-*/*/grading.json")):
        try:
            with open(grading_path) as f:
                data = json.load(f)
            eval_id = data.get("eval_id", "unknown")
            variant = data.get("variant", grading_path.parent.name)
            key = f"{eval_id}-{variant}"
            details[key] = data
        except (json.JSONDecodeError, KeyError):
            continue
    return details


def generate_html(benchmark: dict, details: dict, iteration: int, all_benchmarks: list[dict]) -> str:
    """Generate the full HTML report."""
    patterns = benchmark.get("patterns", {})
    summary = benchmark.get("_summary", {})
    timestamp = benchmark.get("timestamp", datetime.now(timezone.utc).isoformat())

    # Build score table rows
    table_rows = []
    all_frameworks = set()
    for fw_data in patterns.values():
        all_frameworks.update(fw_data.keys())
    frameworks = sorted(all_frameworks)

    for pattern in sorted(patterns.keys()):
        fw_data = patterns[pattern]
        for fw in frameworks:
            if fw not in fw_data:
                continue
            scores = fw_data[fw]
            without = scores.get("without_skill")
            with_s = scores.get("with_skill")
            delta = scores.get("delta")

            without_cell = ""
            if without is not None:
                color = score_color(without)
                bg = score_bg(without)
                without_cell = f'<td style="background:{bg};color:{color};font-weight:bold;text-align:center">{without:.2f}</td>'
            else:
                without_cell = '<td style="text-align:center;color:#666">—</td>'

            with_cell = ""
            if with_s is not None:
                color = score_color(with_s)
                bg = score_bg(with_s)
                with_cell = f'<td style="background:{bg};color:{color};font-weight:bold;text-align:center">{with_s:.2f}</td>'
            else:
                with_cell = '<td style="text-align:center;color:#666">—</td>'

            delta_cell = ""
            if delta is not None:
                delta_color = "#2d8a4e" if delta > 0 else "#cf222e" if delta < 0 else "#666"
                delta_cell = f'<td style="text-align:center;color:{delta_color};font-weight:bold">+{delta*100:.0f}pp</td>'
            else:
                delta_cell = '<td style="text-align:center;color:#666">—</td>'

            table_rows.append(
                f"<tr><td>{pattern}</td><td>{fw}</td>{without_cell}{with_cell}{delta_cell}</tr>"
            )

    score_table = "\n".join(table_rows)

    # Per-assertion breakdown
    assertion_sections = []
    for key in sorted(details.keys()):
        data = details[key]
        eval_id = data.get("eval_id", "?")
        framework = data.get("framework", "?")
        pattern = data.get("pattern", "?")
        variant = data.get("variant", "?")
        score = data.get("score", 0)
        expectations = data.get("expectations", [])

        rows = []
        for exp in expectations:
            text = exp.get("text", "")
            passed = exp.get("passed", False)
            evidence = exp.get("evidence", "")
            icon = "✅" if passed else "❌"
            evidence_escaped = evidence.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            rows.append(
                f'<tr><td>{icon}</td><td>{text}</td><td style="font-size:0.85em;color:#555">{evidence_escaped}</td></tr>'
            )

        assertion_table = "\n".join(rows)
        color = score_color(score)
        bg = score_bg(score)

        assertion_sections.append(f"""
        <div style="margin-bottom:1.5em;border:1px solid #d0d7de;border-radius:6px;padding:1em;">
            <h4 style="margin:0 0 0.5em 0;">
                Eval {eval_id}: {pattern} / {framework}
                <span style="background:{bg};color:{color};padding:2px 8px;border-radius:4px;font-size:0.85em;margin-left:0.5em">
                    {variant} — {score:.2f}
                </span>
            </h4>
            <table style="width:100%;border-collapse:collapse;font-size:0.9em;">
                <tr style="border-bottom:1px solid #eee"><th style="width:30px"></th><th style="text-align:left">Assertion</th><th style="text-align:left">Evidence</th></tr>
                {assertion_table}
            </table>
        </div>
        """)

    assertions_html = "\n".join(assertion_sections) if assertion_sections else "<p>No grading data available yet.</p>"

    # Gap analysis
    drupal_without = summary.get("drupal_avg_without", 0)
    nestjs_avg = summary.get("nestjs_avg", 0)
    strapi_avg = summary.get("strapi_avg", 0)
    gap_exists = summary.get("gap_exists", False)

    gap_icon = "⚠️" if gap_exists else "✅"
    gap_text = "Yes — Drupal scores below both JS frameworks" if gap_exists else "No — Drupal is competitive with JS frameworks"

    # Context delta
    drupal_with = summary.get("drupal_avg_with", 0)
    delta_pp = summary.get("delta_pp", 0)
    gap_closed = summary.get("gap_closed_by_context", False)
    closed_icon = "✅" if gap_closed else "⚠️"
    closed_text = "Yes — context brings Drupal within 90% of JS baseline" if gap_closed else "No — context helps but doesn't fully close the gap"

    findings_section = generate_findings_summary(all_benchmarks)
    iteration_comparison = generate_iteration_comparison(all_benchmarks)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Drupal Gap Benchmark — Iteration {iteration}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #1f2328;
            max-width: 1100px;
            margin: 0 auto;
            padding: 2em;
            background: #f6f8fa;
        }}
        h1 {{
            font-size: 1.8em;
            margin-bottom: 0.2em;
            color: #0969da;
        }}
        h2 {{
            font-size: 1.3em;
            margin: 1.5em 0 0.5em 0;
            padding-bottom: 0.3em;
            border-bottom: 1px solid #d0d7de;
        }}
        h3 {{ font-size: 1.1em; margin: 1em 0 0.5em 0; }}
        .timestamp {{ color: #656d76; font-size: 0.85em; margin-bottom: 1.5em; }}
        .card {{
            background: white;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 1.5em;
            margin-bottom: 1.5em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0.5em 0;
        }}
        th, td {{
            padding: 8px 12px;
            border: 1px solid #d0d7de;
            text-align: left;
        }}
        th {{ background: #f6f8fa; font-weight: 600; }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1em;
            margin: 1em 0;
        }}
        .stat-box {{
            background: white;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 1em;
            text-align: center;
        }}
        .stat-value {{ font-size: 1.8em; font-weight: bold; }}
        .stat-label {{ font-size: 0.85em; color: #656d76; }}
    </style>
</head>
<body>
    <h1>Drupal Gap Benchmark</h1>
    <p class="timestamp">Iteration {iteration} &mdash; Generated {timestamp}</p>

    {findings_section}

    {iteration_comparison}

    <h2>Summary Statistics (Iteration {iteration})</h2>
    <div class="stat-grid">
        <div class="stat-box">
            <div class="stat-value" style="color:{score_color(drupal_without)}">{drupal_without:.2f}</div>
            <div class="stat-label">Drupal (no context)</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color:{score_color(drupal_with)}">{drupal_with:.2f}</div>
            <div class="stat-label">Drupal (with context)</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color:{score_color(nestjs_avg)}">{nestjs_avg:.2f}</div>
            <div class="stat-label">NestJS baseline</div>
        </div>
        <div class="stat-box">
            <div class="stat-value" style="color:{score_color(strapi_avg)}">{strapi_avg:.2f}</div>
            <div class="stat-label">Strapi baseline</div>
        </div>
    </div>

    <h2>Score Table</h2>
    <div class="card">
        <table>
            <thead>
                <tr><th>Pattern</th><th>Framework</th><th>Without Skill</th><th>With Skill</th><th>Delta</th></tr>
            </thead>
            <tbody>
                {score_table}
            </tbody>
        </table>
    </div>

    <h2>Gap Analysis</h2>
    <div class="card">
        <h3>{gap_icon} Gap Exists: {gap_text}</h3>
        <table>
            <tr><th>Metric</th><th>Score</th></tr>
            <tr><td>Drupal baseline (no context)</td><td style="font-weight:bold;color:{score_color(drupal_without)}">{drupal_without:.2f}</td></tr>
            <tr><td>NestJS baseline</td><td style="font-weight:bold;color:{score_color(nestjs_avg)}">{nestjs_avg:.2f}</td></tr>
            <tr><td>Strapi baseline</td><td style="font-weight:bold;color:{score_color(strapi_avg)}">{strapi_avg:.2f}</td></tr>
        </table>
        <p style="margin-top:0.5em;font-size:0.9em;color:#656d76">
            Gap defined as: Drupal baseline &lt; min(NestJS, Strapi)
        </p>
    </div>

    <h2>Context Delta</h2>
    <div class="card">
        <h3>{closed_icon} Gap Closed by Context: {closed_text}</h3>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Drupal without context</td><td>{drupal_without:.2f}</td></tr>
            <tr><td>Drupal with context</td><td style="font-weight:bold;color:{score_color(drupal_with)}">{drupal_with:.2f}</td></tr>
            <tr><td>Delta</td><td style="font-weight:bold;color:#2d8a4e">+{delta_pp}pp</td></tr>
            <tr><td>JS baseline min</td><td>{min(nestjs_avg, strapi_avg) if nestjs_avg and strapi_avg else max(nestjs_avg, strapi_avg):.2f}</td></tr>
        </table>
        <p style="margin-top:0.5em;font-size:0.9em;color:#656d76">
            Closed defined as: Drupal+context &ge; 90% of min(NestJS, Strapi)
        </p>
    </div>

    <h2>Per-Assertion Breakdown</h2>
    <div class="card">
        {assertions_html}
    </div>

    <footer style="margin-top:2em;padding-top:1em;border-top:1px solid #d0d7de;color:#656d76;font-size:0.85em;">
        Drupal Gap Agentic AI Benchmark &mdash; UI Research
    </footer>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(description="Generate HTML report from benchmark.json")
    parser.add_argument("--iteration", type=int, default=1, help="Iteration number (default: 1)")
    args = parser.parse_args()

    evals_dir = Path(__file__).parent.parent
    workspace_dir = evals_dir / "drupal-gap-workspace"
    iteration_dir = workspace_dir / f"iteration-{args.iteration}"

    benchmark_path = iteration_dir / "benchmark.json"
    if not benchmark_path.exists():
        print(f"ERROR: {benchmark_path} not found. Run aggregate.py first.", file=sys.stderr)
        sys.exit(1)

    with open(benchmark_path) as f:
        benchmark = json.load(f)

    details = load_grading_details(iteration_dir)
    all_benchmarks = load_all_benchmarks(workspace_dir)

    html = generate_html(benchmark, details, args.iteration, all_benchmarks)

    output_path = Path(__file__).parent / "report.html"
    with open(output_path, "w") as f:
        f.write(html)
    print(f"Report generated: {output_path}")

    # Also publish to docs/ for GitHub Pages
    docs_path = Path(__file__).resolve().parent.parent.parent / "docs" / "index.html"
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    with open(docs_path, "w") as f:
        f.write(html)
    print(f"GitHub Pages copy: {docs_path}")


if __name__ == "__main__":
    main()
