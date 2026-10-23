from app.research.generator import CONFIG, generate, validate


def test_full_generation_integrity():
    data = generate()
    report = validate(data)
    assert report["counts"]["variants"] == 576
    assert report["counts"]["profiles"] == 10000
    assert report["counts"]["synthetic_quotes"] == 10000
    assert all(q["monthly_pence"] > 0 for q in data["synthetic_quotes"])
    assert len({s["user_id"] for s in data["sessions"]}) == 3000
    assert len(data["personas"]) == 60
    assert len({p["name"] for p in data["insurers"]}) == 12


def test_seed_reproducible_and_no_future_revision_labels():
    config = {**CONFIG, "profiles": 30, "histories": 10}
    first = generate(config)
    assert first == generate(config)
    assert first != generate({**config, "seed": 1})
    for event in first["events"]:
        if event["type"] == "impression":
            assert "confirmed" not in event
            assert 0 < event["exposure_probability"] < 1


def test_richer_family_base_costs_more():
    data = generate({**CONFIG, "profiles": 0, "histories": 0})
    for insurer in data["insurers"]:
        group = [p for p in data["variants"] if p["insurer_id"] == insurer["id"] and p["excess_pence"] == 0 and p["network"] == 1]
        assert [p["base_pence"] for p in group] == sorted(p["base_pence"] for p in group)
