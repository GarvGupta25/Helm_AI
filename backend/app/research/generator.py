"""Reproducible fictional catalogue and dependency-aware experimental histories."""
import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

CONFIG = json.loads(Path(__file__).with_name("config.json").read_text())
CARE = ("inpatient", "diagnostics", "outpatient", "mental_health", "physio", "cancer",
        "dental", "maternity", "emergency", "chronic", "pre_existing")


def generate(config=None):
    cfg = config or CONFIG
    rng = random.Random(cfg["seed"])
    insurers, families, variants, clauses, profiles, sessions, events, personas = ([] for _ in range(8))
    for i in range(cfg["insurers"]):
        insurer = f"ins-{i:02}"
        insurers.append({"id": insurer, "name": f"Fictional {['Alder', 'Bracken', 'Cairn', 'Dapple', 'Elm', 'Fern', 'Grove', 'Hearth', 'Iris', 'Juniper', 'Kestrel', 'Larch'][i % 12]} Research {i+1}",
                         "strategy": ["basic", "outpatient", "access", "predictability"][i % 4], "source": "synthetic"})
        for f in range(cfg["families"]):
            family = f"{insurer}-f{f}"
            families.append({"id": family, "insurer_id": insurer, "tier": f, "renewal": "annual"})
            for excess in (0, 25000, 50000):
                for network in (1, 2):
                    key = f"{family}-e{excess}-n{network}"
                    base = 3200 + f * 1100 + i * 75 + network * 450
                    limits = {"inpatient": 10000000, "diagnostics": 100000 + f * 50000,
                              "outpatient": [0, 50000, 100000, 150000, 200000, 300000, 400000, 500000][f % 8],
                              "mental_health": 150000 if (f + i) % 3 else 0,
                              "physio": 50000 if f >= 2 else 0, "cancer": 10000000,
                              "dental": 20000 if f == 7 else 0, "maternity": 0, "emergency": 0,
                              "chronic": 0, "pre_existing": 0}
                    plan = {"id": key, "family_id": family, "insurer_id": insurer,
                            "name": f"Research {i+1} / Tier {f+1} / List {network} / Excess £{excess//100}",
                            "version": cfg["version"], "source": "synthetic", "base_pence": base,
                            "excess_pence": excess, "excess_application": "per_person_per_year",
                            "network": network, "regions": cfg["regions"], "age_min": 18, "age_max": 85,
                            "limits": limits, "copay": 0 if f % 2 else .1,
                            "underwriting": "moratorium" if f % 2 else "full_medical",
                            "pre_existing": "excluded" if f % 3 == 0 else "unknown",
                            "referral": "GP referral and preauthorisation required",
                            "service_simulated": 65 + (i * 7 + f * 3) % 31,
                            "valid_from": cfg["generated_at"], "valid_until": "2027-10-23T00:00:00Z"}
                    variants.append(plan)
                    for category, limit in limits.items():
                        status = "covered" if limit else "excluded"
                        if category == "pre_existing":
                            status = plan["pre_existing"]
                        clauses.append({"id": f"{key}:{category}", "variant_id": key, "category": category,
                                        "status": status, "limit_pence": limit, "preauthorisation": bool(limit),
                                        "text": f"Synthetic {category}: {status}; annual eligible benefit cap £{limit/100:.0f}. GP referral and authorisation required. Existing conditions assessed separately.",
                                        "source": "synthetic", "version": cfg["version"]})
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for u in range(cfg["profiles"]):
        latent = rng.choice(["basic", "mental_health", "physio", "access", "low_excess"])
        profile = {"id": f"generated-{u:05}", "age": rng.randint(18, 80),
                   "region": rng.choice(cfg["regions"]), "adults": rng.choice([1, 1, 2]),
                   "children": rng.choice([0, 0, 1, 2]), "budget_pence": rng.randrange(4500, 40001, 500),
                   "priority": latent, "privacy": "synthetic_experiment", "source": "synthetic"}
        profiles.append(profile)
        if u >= cfg["histories"]:
            continue
        for visit in range(3):
            sid = f"{profile['id']}-s{visit}"
            when = start + timedelta(days=u % 150 + visit * 30)
            sessions.append({"id": sid, "user_id": profile["id"], "at": when.isoformat()})
            shown = rng.sample(variants, 5)  # randomized eligible exposure, not labels
            for pos, plan in enumerate(shown):
                utility = (plan["limits"].get(latent, 0) > 0) * 2 + rng.random()
                clicked = rng.random() < min(.9, (.15 + utility * .15) / (1 + pos * .2))
                events.append({"session_id": sid, "user_id": profile["id"], "at": (when + timedelta(seconds=pos)).isoformat(),
                               "type": "impression", "plan_id": plan["id"], "position": pos+1,
                               "exposure_probability": 5/len(variants), "clicked": clicked,
                               "explicit_feedback": rng.choice(["save", "dislike", "compare", None]) if clicked else None})
            value = "mental_health" if visit == 2 and u % 4 == 0 else latent
            events.append({"session_id": sid, "user_id": profile["id"], "at": (when + timedelta(seconds=10)).isoformat(),
                           "type": "confirmed_revision", "utterance": f"My priority is {value}. Please update it.",
                           "assistant_reply": f"Confirm {value} as your current preference?", "confirmed": True,
                           "field": "priority", "value": value, "retracts": latent if value != latent else None})
    for i in range(60):
        must = ["mental_health", "physio", "maternity", "pre_existing", "diagnostics", "chronic"][i % 6]
        acceptable = [p["id"] for p in variants if p["limits"][must] > 0]
        personas.append({"id": f"persona-{i:02}", "description": f"Generated age {18+i}, requires {must}; test exact clause eligibility.",
                         "profile": {"age": 18+i, "region": cfg["regions"][i % 5], "required": [must],
                                     "budget_pence": 10000+i*200, "strict_budget": i % 2 == 0},
                         "acceptable_cover_ids": acceptable, "unsafe_cover_ids": [p["id"] for p in variants if p["id"] not in acceptable],
                         "label_basis": "template clause oracle; requires independent human review"})
    hospitals = [{"id": f"hospital-{i}", "name": f"Fictional Research Hospital {i+1}", "region": region,
                  "network": network, "source": "synthetic"}
                 for i, (region, network) in enumerate((r, n) for r in cfg["regions"] for n in (1, 2))]
    return {"lineage": cfg, "insurers": insurers, "families": families, "variants": variants,
            "clauses": clauses, "hospitals": hospitals, "profiles": profiles, "sessions": sessions,
            "events": events, "personas": personas}


def validate(data):
    plans = data["variants"]
    ids = {p["id"] for p in plans}
    assert len(ids) == len(plans)
    assert all(c["variant_id"] in ids and c["status"] in {"covered", "excluded", "unknown", "conditional"} for c in data["clauses"])
    assert all(e.get("plan_id", next(iter(ids))) in ids for e in data["events"])
    assert all(p["base_pence"] > 0 and p["limits"]["maternity"] == 0 for p in plans)
    chronology = defaultdict(list)
    for event in data["events"]:
        chronology[event["session_id"]].append(event["at"])
    assert all(dates == sorted(dates) for dates in chronology.values())
    return {"source": "synthetic", "version": data["lineage"]["version"],
            "counts": {k: len(v) for k, v in data.items() if isinstance(v, list)},
            "age_distribution": dict(Counter((p["age"]//10)*10 for p in data["profiles"])),
            "region_distribution": dict(Counter(p["region"] for p in data["profiles"])),
            "checks": ["unique variants", "clause references", "coverage status", "positive base prices", "chronology"],
            "limitations": "Template-generated labels and prices are not human validation or real market calibration."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = generate()
    report = validate(data)
    args.output.mkdir(parents=True, exist_ok=True)
    for key, value in data.items():
        (args.output / f"{key}.json").write_text(json.dumps(value, indent=2), encoding="utf-8")
    (args.output / "quality.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with (args.output / "profiles.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=data["profiles"][0].keys())
        writer.writeheader()
        writer.writerows(data["profiles"])
    print(json.dumps(report))


if __name__ == "__main__":
    main()
