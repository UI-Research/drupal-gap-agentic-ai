#!/usr/bin/env python3
"""Generate an HTML report from benchmark.json and individual grading files."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def generate_html(benchmark: dict, details: dict, iteration: int) -> str:
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

    <h2>Summary Statistics</h2>
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

    html = generate_html(benchmark, details, args.iteration)

    output_path = Path(__file__).parent / "report.html"
    with open(output_path, "w") as f:
        f.write(html)

    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    main()
