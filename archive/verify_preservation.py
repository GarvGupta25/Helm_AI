"""Read-only preservation and route checks for the approved site split."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parent.parent
TAG = "backup-before-split-20261022"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def blob(path: str, original: str) -> str:
    return git("hash-object", f"--path={original}", "--", path)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    tree = git("ls-tree", "-r", TAG)
    baseline = {line.split("\t", 1)[1]: line.split("\t", 1)[0].split()[2] for line in tree.splitlines()}
    records = [json.loads(line) for line in (ROOT / "archive/MANIFEST.jsonl").read_text(encoding="utf-8").splitlines()]
    check(len(baseline) == 187, "Unexpected safety-tag inventory")
    check(len({row["archive_path"] for row in records}) == len(records), "Duplicate archive destination")
    moves = {row["original_path"]: row for row in records if row["operation"] == "MOVE"}
    snapshots = {row["original_path"]: row for row in records if row["operation"] == "ORIGINAL-SNAPSHOT"}
    check(len(moves) == 17, "Expected exactly 17 approved moves")
    check(sum(row["operation"] == "COPY" for row in records) == 45, "Expected 45 shared dependency copies")
    exact_bytes = 0
    for row in records:
        source, destination = row["original_path"], row["archive_path"]
        check(source in baseline, f"Archive source is not in safety tag: {source}")
        check(row["baseline_git_blob"] == baseline[source], f"Ledger baseline mismatch: {source}")
        path = ROOT / destination
        check(path.is_file(), f"Missing archived file: {destination}")
        check(blob(destination, source) == baseline[source], f"Changed archived content: {destination}")
        exact_bytes += hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]
        if row["operation"] == "MOVE":
            check(not (ROOT / source).exists(), f"Moved original unexpectedly still exists: {source}")
        else:
            check((ROOT / source).is_file(), f"Copy/snapshot source missing: {source}")

    missing = []
    edited = []
    for source, original_blob in baseline.items():
        if source in moves:
            continue
        if not (ROOT / source).is_file():
            missing.append(source)
            continue
        if blob(source, source) != original_blob:
            edited.append(source)
            check(source in snapshots, f"Edited baseline file lacks a whole original snapshot: {source}")
    check(not missing, f"Missing baseline files: {missing}")

    protected = ["backend", "supabase", "frontend/src/api.ts", "frontend/package.json", "frontend/package-lock.json", "package.json", "package-lock.json", "docs", "scripts/start-prototype.ps1"]
    check(not git("diff", "--name-only", TAG, "--", *protected), "Protected backend/database/auth/packages/uncertain paths changed")
    # The only allowed environment change is the explicitly requested names-only example-template addition.
    template = ROOT / "frontend/.env.example"
    original_template = ROOT / snapshots["frontend/.env.example"]["archive_path"]
    added_template = template.read_text(encoding="utf-8")[len(original_template.read_text(encoding="utf-8").rstrip()):]
    added_names = re.findall(r"^(VITE_[A-Z_]+)=(.*)$", added_template, re.M)
    check(added_names == [("VITE_BROKER_PORTAL_URL", ""), ("VITE_PROVIDER_PORTAL_URL", ""), ("VITE_STAFF_PORTAL_URL", "")], "Unexpected example variable names or values")
    check(template.read_text(encoding="utf-8").startswith(original_template.read_text(encoding="utf-8").rstrip()), "Existing example variables changed")

    current = (ROOT / "frontend/src/main.tsx").read_text(encoding="utf-8")
    original = (ROOT / snapshots["frontend/src/main.tsx"]["archive_path"]).read_text(encoding="utf-8")
    def login_section(text: str) -> str:
        return text[text.index("function Login("):text.index("function PoliciesLink(")]
    check(login_section(current) == login_section(original), "Login auth implementation changed")
    original_routes = re.findall(r'<Route\s+path="([^"]+)"', original)
    current_routes = re.findall(r'<Route\s+path="([^"]+)"', current)
    removed = {"broker", "broker/claims", "/broker/claims", "/provider"}
    check(current_routes == [route for route in original_routes if route not in removed], "Customer route registration changed unexpectedly")
    check(not any(name in current for name in ["BrokerWorkspace", "ClaimReview", "ProviderWorkspace"]), "Archived dashboard remains imported")
    routes = [route if route.startswith("/") else "/app/" + route for route in current_routes if route != "*"]
    route_patterns = [re.compile("^" + re.sub(r":[A-Za-z]+", "[^/]+", route) + "$" ) for route in routes]
    unresolved = []
    broken_links = []
    imports = re.compile(r"""(?:\bfrom\s*|\bimport\s*\(|^\s*import\s*)['"]([^'"\n]+)['"]""", re.M)
    targets = re.compile(r"""(?:\bto\s*=\s*(?:\{\s*)?|\bto\s*:\s*|\bnavigate\(\s*|\bhref\s*=\s*(?:\{\s*)?)['"`](/[^'"`\s]*)""")
    for path in (ROOT / "frontend/src").rglob("*"):
        if path.suffix not in {".ts", ".tsx"}:
            continue
        text = path.read_text(encoding="utf-8")
        for spec in imports.findall(text):
            if not spec.startswith("."):
                continue
            base = path.parent / spec
            candidates = [base, *[Path(str(base) + ext) for ext in [".ts", ".tsx", ".css"]], base / "index.ts", base / "index.tsx"]
            found = next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)
            if found is None or ROOT / "archive" in found.parents:
                unresolved.append((path.relative_to(ROOT).as_posix(), spec))
        for target in targets.findall(text):
            target = re.sub(r"\$\{[^}]+\}", "sample", target).split("?")[0].split("#")[0]
            if target and not any(pattern.fullmatch(target) for pattern in route_patterns):
                broken_links.append((path.relative_to(ROOT).as_posix(), target))
    check(not unresolved, f"Unresolved/archived active imports: {unresolved}")
    check(not broken_links, f"Links without a registered customer route: {broken_links}")

    restore = (ROOT / "archive/restore.sh").read_text(encoding="utf-8")
    commands = [shlex.split(line) for line in restore.splitlines() if line.startswith("git mv -- ")]
    expected = [["git", "mv", "--", row["archive_path"], row["original_path"]] for row in records if row["operation"] == "MOVE"]
    check(commands == expected, "Restore commands do not exactly reverse manifest moves")
    check("# Preflight every move" in restore, "Missing restoration preflight")
    print(f"Safety tag: {TAG}")
    print(f"Baseline files: {len(baseline)}; kept paths: {len(baseline) - len(moves)}; archive moves: {len(moves)}")
    print(f"Missing baseline files: {len(missing)}")
    print(f"Verified archive records: {len(records)}; exact on-disk byte digests: {exact_bytes}/{len(records)} (Git blobs all match)")
    print(f"Edited originals preserved: {len(edited)}; shared copies: 45")
    print(f"Protected backend/database/auth/packages/uncertain paths: zero diff")
    print(f"Kept route declarations: {len(current_routes)}; active imports and navigation targets: valid")
    print("restore.sh exactly reverses 17 moves; verification did not execute it")


if __name__ == "__main__":
    main()
