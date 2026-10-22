"""Inventory tracked historical market terms without rewriting archives or user data."""
import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"\b(?:UAE|AED|Dubai|DHA|DOH|HAAD|emirates?|razorpay|fils)\b|PD-05-2025|\+971", re.I)

def inventory():
    rows = []
    for name in subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines():
        path = ROOT / name
        if name.startswith("docs/uk/") or name == "scripts/uk_inventory.py":
            continue
        try:
            content = path.read_text(encoding="utf-8-sig")
        except (UnicodeError, OSError):
            continue
        for number, line in enumerate(content.splitlines(), 1):
            for match in PATTERN.finditer(line):
                rows.append((name, number, match.group(), "Preserve historical archive; migrate active contracts with tested conversion"))
    target = ROOT / "docs/uk/uae_leftovers.csv"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["path", "line", "term", "replacement_plan"])
        writer.writerows(rows)
    print(f"Historical tracked-source matches: {len(rows)}; see {target}")

if __name__ == "__main__":
    inventory()
