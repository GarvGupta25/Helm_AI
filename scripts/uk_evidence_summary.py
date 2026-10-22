"""Summarise actual machine-readable results without inventing missing evidence."""
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "docs/uk/evidence"
rows = ["# Measured browser evidence", "", "Local lab measurements, not production field data. Missing runs are not passes.", "", "| Report | Performance | Accessibility | Best practices | SEO | LCP (ms) | CLS |", "|---|---:|---:|---:|---:|---:|---:|"]
for path in sorted(root.glob("lighthouse-*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    categories = data.get("categories", {})
    scores = [str(round(categories[key]["score"] * 100)) if categories.get(key, {}).get("score") is not None else "unavailable" for key in ["performance", "accessibility", "best-practices", "seo"]]
    audits = data.get("audits", {})
    lcp = audits.get("largest-contentful-paint", {}).get("numericValue")
    cls = audits.get("cumulative-layout-shift", {}).get("numericValue")
    rows.append(f"| {path.name} | {' | '.join(scores)} | {round(lcp) if lcp is not None else 'unavailable'} | {round(cls, 3) if cls is not None else 'unavailable'} |")
rows += ["", "## Accessibility runs", ""]
for path in sorted(root.glob("axe-*.json")):
    violations = json.loads(path.read_text(encoding="utf-8"))
    rows.append(f"- {path.name}: {len(violations)} rule violations; {sum(value.get('impact') in {'critical', 'serious'} for value in violations)} critical/serious rules.")
report = root / "playwright.json"
if report.exists():
    data = json.loads(report.read_text(encoding="utf-8"))
    rows += ["", "## Browser suite", "", f"Actual recorded stats: `{json.dumps(data.get('stats', {}), ensure_ascii=False)}`."]
(root.parent / "PERFORMANCE_ACCESSIBILITY_REPORT.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
print("\n".join(rows[:12]))
