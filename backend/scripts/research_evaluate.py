"""Offline fixture evaluation. Generated labels never validate real customer outcomes."""
import json
import math
import time
from pathlib import Path

from app.research.engine import filter_plan, quote, recommend
from app.research.generator import CONFIG, generate
from app.research.schemas import Profile


def evaluate():
    data = generate({**CONFIG, "profiles": 0, "histories": 0})
    plans = data["variants"]
    violations = 0
    faithfulness = 0
    hit, ndcg, durations = [], [], []
    cases = []
    for persona in data["personas"]:
        profile = Profile(**persona["profile"])
        started = time.perf_counter()
        result = recommend(plans, profile)
        durations.append((time.perf_counter()-started)*1000)
        oracle = {p["id"] for p in plans if p["id"] in persona["acceptable_cover_ids"]
                  and (not profile.strict_budget or quote(p, profile)["monthly_pence"] <= profile.budget_pence)}
        for item in result["items"]:
            violations += bool(filter_plan(item["plan"], profile))
            faithfulness += all(c in {clause["id"] for clause in data["clauses"]} for c in item["evidence_ids"])
        gains = [int(p["id"] in oracle) for p in result["items"]]
        if oracle:
            hit.append(int(any(gains)))
            ideal = sum(1/math.log2(i+2) for i in range(min(3, len(oracle))))
            ndcg.append(sum(g/math.log2(i+2) for i, g in enumerate(gains))/ideal)
        cases.append({"id": persona["id"], "acceptable_count": len(oracle), "returned": [p["id"] for p in result["items"]], "no_fit": result["no_fit"]})
    report = {"version": CONFIG["version"], "source": "synthetic", "personas": 60,
              "hard_filter_violations": violations, "clause_reference_passes": faithfulness,
              "fixture_hit_at_3": sum(hit)/len(hit), "fixture_ndcg_at_3": sum(ndcg)/len(ndcg),
              "latency_ms": {"mean": sum(durations)/len(durations), "p95": sorted(durations)[56]},
              "labels": "Generated clause/strict-price oracle, not independent human preference labels. Metrics establish fixture agreement only.",
              "fairness": "No gender, race, religion, commission or click features enter ranking. Age influences synthetic premium explicitly; this does not constitute a full disparate-impact audit.",
              "learning": "Disabled: no independent evidence of incremental value. Baseline retained.",
              "cases": cases}
    return report


if __name__ == "__main__":
    report = evaluate()
    target = Path(__file__).resolve().parents[2]/"docs/research/evaluation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))
