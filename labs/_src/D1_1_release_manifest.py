# %% [markdown]
# # Lab 1.1 · A release manifest and the unrecorded change
#
# Day 1 · Session 1 (What changes behaviour) · 25 min.
#
# Two recorded runs of Wahaj's three systems, two weeks apart, behave differently: the fault-risk classifier
# flags more feeders and three of Nabd's weekly probe answers changed. You hash every part that changes
# behaviour into one release manifest per run, diff the two, and check each difference against the change log.
#
# **Reference state.** `data/runs/run_A/` and `data/runs/run_B/` (what was deployed and what each run logged),
# `data/runs/CHANGELOG.md`, and the manuals index and tool schemas they point to.
#
# **Tasks**
# - [ ] 1 · Read the two run folders (4')
# - [ ] 2 · Hash every part that changes behaviour (7')
# - [ ] 3 · Build the manifest for each run (6')
# - [ ] 4 · Diff the manifests against the change log (8')
# - [ ] ✱ Stretch · A check that refuses a manifest whose model is a moving alias

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ae-305.git"
    if not Path("/content/ae-305").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/ae-305"], check=True)
    os.chdir("/content/ae-305/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("_tools").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import opskit as K
print("quick mode:", K.QUICK)

# %% [markdown]
# ## 1 · Read the two run folders (4')
#
# Each folder holds what was deployed for the three systems, and `run.json`, what the run logged.

# %%
import json

RUNS = K.DATA / "runs"
for run in ("run_A", "run_B"):
    files = sorted(p.relative_to(RUNS / run).as_posix() for p in (RUNS / run).rglob("*") if p.is_file())
    log = K.read_json(RUNS / run / "run.json")
    print(run, log["date"], "| files:", files)
    print("   classifier flagged", log["classifier"]["flagged_feeders"], "feeders | Nabd probe answers changed:",
          log["nabd"]["probe_answers_changed_vs_last_week"])
print((RUNS / "CHANGELOG.md").read_text(encoding="utf-8"))

# %% [markdown]
# 🔍 Two behaviours changed. Before hashing anything, write down what you think changed, and where you would look.

# %% [markdown]
# ## 2 · Hash every part that changes behaviour (7')
#
# A release unit is everything that changes behaviour: data, code, configuration, model, prompt, retrieval index
# and tool schemas. For files, the content hash is the version. For things a file only names, record what the
# name resolved to: the index's fingerprint, and the model **the provider answered with**, not the alias the
# release asked for.
#
# ✏️ **Exercise** · Write `system_parts(run_dir)` returning one dict per system:
# - `classifier`: the registry alias and version, the threshold, and a hash of the feature list
# - `nabd`: hashes of `nabd/prompt.txt` and `data/nabd/tools.json`, the index version and its fingerprint
#   (`nabd.Index(version).fingerprint()`), `model_requested` from `release.json` and `model_resolved` from the
#   run log's `response_model`
# - `mubadir`: the hash of each of its four files

# %%
import nabd


def system_parts(run_dir: Path) -> dict:
    # BEGIN SOLUTION
    log = K.read_json(run_dir / "run.json")
    cfg = K.read_json(run_dir / "classifier" / "config.json")
    rel = K.read_json(run_dir / "nabd" / "release.json")
    return {
        "classifier": {"registry": f"fault-risk@{cfg['registry_alias']} v{cfg['registry_version']}",
                       "threshold": cfg["threshold"], "features": K.short(K.sha256_json(cfg["features"]))},
        "nabd": {"prompt": K.short(K.sha256_file(run_dir / "nabd" / "prompt.txt")),
                 "tools": K.short(K.sha256_file(K.DATA / "nabd" / "tools.json")),
                 "index": rel["index"], "index_fingerprint": nabd.Index(rel["index"]).fingerprint(),
                 "retrieval": rel["retrieval"], "temperature": rel["temperature"],
                 "model_requested": rel["model"], "model_resolved": log["nabd"]["response_model"]},
        "mubadir": {f: K.short(K.sha256_file(run_dir / "mubadir" / f)) for f in ("prompt.md", "tools.json", "harness.yaml", "sandbox.yaml")},
    }
    # END SOLUTION


# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    parts_A = system_parts(RUNS / "run_A")
except NotImplementedError:
    parts_A = K.reference("D1_1_parts")["run_A"]
K.save_reference("D1_1_parts", {"run_A": parts_A})
print(json.dumps(parts_A, indent=1))
K.check(parts_A["nabd"]["model_resolved"] != parts_A["nabd"]["model_requested"], "the resolved model is recorded, not only the alias")

# %% [markdown]
# ## 3 · Build the manifest for each run (6')
#
# ✏️ **Exercise** · Write `build_manifest(run_dir)`: the parts of step 2, plus a `release` id that is the hash
# of all the parts (`K.sha256_json`), so any change anywhere gives a new release id. Write both manifests to
# `artifacts/D1_1/`.

# %%
OUT = K.lab_dir("D1_1")


def build_manifest(run_dir: Path) -> dict:
    # BEGIN SOLUTION
    parts = system_parts(run_dir)
    return {"run": run_dir.name, "date": K.read_json(run_dir / "run.json")["date"],
            "release": "wahaj-" + K.short(K.sha256_json(parts)), "systems": parts}
    # END SOLUTION


# %%
try:
    manifests = {r: build_manifest(RUNS / r) for r in ("run_A", "run_B")}
except NotImplementedError:
    manifests = K.reference("D1_1_manifests")
K.save_reference("D1_1_manifests", manifests)
for r, m in manifests.items():
    K.write_json(OUT / f"manifest_{r}.json", m)
    print(r, m["release"])
K.check(manifests["run_A"]["release"] != manifests["run_B"]["release"], "the two runs are two different releases")

# %% [markdown]
# ## 4 · Diff the manifests against the change log (8')
#
# ✏️ **Exercise** · Write `diff(a, b)` returning `(path, old, new)` for every leaf that differs, with paths like
# `classifier.threshold`. Then mark each difference as recorded when the change log mentions its last path part
# (for `classifier.threshold`, the word "threshold"), and print the unrecorded ones.

# %%
def diff(a: dict, b: dict, prefix: str = "") -> list[tuple]:
    # BEGIN SOLUTION
    out = []
    for k in sorted(set(a) | set(b)):
        p = f"{prefix}{k}"
        va, vb = a.get(k), b.get(k)
        if isinstance(va, dict) and isinstance(vb, dict):
            out += diff(va, vb, p + ".")
        elif va != vb:
            out.append((p, va, vb))
    return out
    # END SOLUTION


# %%
try:
    changes = diff(manifests["run_A"]["systems"], manifests["run_B"]["systems"])
except NotImplementedError:
    changes = [tuple(c) for c in K.reference("D1_1_changes")]
K.save_reference("D1_1_changes", changes)
log_text = (RUNS / "CHANGELOG.md").read_text(encoding="utf-8").lower()
unrecorded = []
for path, old, new in changes:
    recorded = path.split(".")[-1].replace("_", " ") in log_text
    print(f"{'recorded  ' if recorded else 'UNRECORDED'} {path}: {old} -> {new}")
    if not recorded:
        unrecorded.append(path)
assert {c[0] for c in changes} == {"classifier.threshold", "nabd.model_resolved"}, changes
assert unrecorded == ["nabd.model_resolved"], unrecorded
K.check(True, "found the unrecorded change: the alias hosted/steady-latest moved to a new snapshot")

# %% [markdown]
# 🔍 Nobody at Wahaj changed Nabd. The provider moved the alias `steady-latest` to a new snapshot between the two
# runs, and the release file could not show it because it only names the alias. Which of the two behaviour changes
# of step 1 does each difference explain?

# %% [markdown]
# ## ✱ Stretch · Refuse a moving alias
#
# Write `pinned(manifest)` that fails when a model identifier is a moving alias (it ends in `latest`, or the
# resolved model differs from the requested one), and run it on both manifests.

# %%
def pinned(manifest: dict) -> list[str]:
    # BEGIN SOLUTION
    n = manifest["systems"]["nabd"]
    problems = []
    if n["model_requested"].endswith("latest"):
        problems.append(f"nabd asks for the moving alias {n['model_requested']}; pin {n['model_resolved']}")
    return problems
    # END SOLUTION


try:
    for r, m in manifests.items():
        print(r, pinned(m) or "pinned")
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. Two runs requested the same model name and answered differently. What do you record so this cannot hide again?
#    <details><summary>Answer</summary>The identifier the provider answered with (the response's model field),
#    and a pinned identifier in the release; an alias is a pointer that can move.</details>
# 2. Why is the manifest's release id a hash of all its parts rather than a number someone increments?
#    <details><summary>Answer</summary>A hash changes whenever any part changes, including parts nobody thought to
#    bump; a hand-kept number only changes when someone remembers.</details>
# 3. The change log recorded the threshold change. Is the manifest still needed?
#    <details><summary>Answer</summary>Yes: the log records what people meant to change; the manifest records what
#    was running. The diff between the two is how you found the provider's change.</details>
#
# ## Carry forward
#
# `artifacts/D1_1/manifest_run_B.json` is the shape of the release manifest the capstone repository keeps for
# every release of the week.
