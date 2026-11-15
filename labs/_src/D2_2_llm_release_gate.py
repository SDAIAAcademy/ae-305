# %% [markdown]
# # Lab 2.2 · Three changes through the evaluation gate
#
# Day 2 · Session 2 (Language model releases) · 25 min.
#
# Three changes to Nabd wait for release: a prompt edit, a model swap to a cheaper and faster model, and an index
# refresh with version 4 of the manuals. Each is a new release of the same assistant. You run the champion and the
# three candidates through the evaluation gate supplied by the platform team (built the AE-303 way), read the
# results by category, and write the release log: what shipped, what was blocked, and on which metric.
#
# **Reference state.** `data/nabd/releases/*.json`, the 24 offline cases in `data/eval/nabd_eval.jsonl`, and the
# gate in `evalgate.py`. Without a working model key every release runs on the scripted stand-in model, which
# answers from the retrieved manuals; with a key, the same code calls a free hosted model.
#
# **Tasks**
# - [ ] 1 · The release unit of each candidate (4')
# - [ ] 2 · Run the gate on the champion (6')
# - [ ] 3 · Run the three candidates (8')
# - [ ] 4 · Read by category and write the release log (7')
# - [ ] ✱ Stretch · Run one candidate on a live free model and compare

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

# %%
import json

import pandas as pd

import evalgate as G
import nabd

OUT = K.lab_dir("D2_2")
CANDIDATES = ["cand_prompt_v2", "cand_model_swap", "cand_index_v4"]
champion = nabd.load_release("champion")
print(json.dumps(champion, indent=1))
print("rules:", G.RULES)

# %% [markdown]
# ## 1 · The release unit of each candidate (4')
#
# ✏️ **Exercise** · Write `changed_parts(candidate, champion)` returning the keys whose values differ, leaving out
# the release name and the change note. Each candidate should change exactly one part.

# %%
def changed_parts(candidate: dict, champion: dict) -> dict:
    # BEGIN SOLUTION
    skip = {"release", "change"}
    return {k: (champion.get(k), candidate.get(k)) for k in sorted(set(candidate) | set(champion))
            if k not in skip and candidate.get(k) != champion.get(k)}
    # END SOLUTION


# %%
cands = {c: nabd.load_release(c) for c in CANDIDATES}
try:
    parts = {c: changed_parts(r, champion) for c, r in cands.items()}
except NotImplementedError:  # safety net
    parts = {c: {k: (champion.get(k), r.get(k)) for k in r if k not in ("release", "change") and r.get(k) != champion.get(k)}
             for c, r in cands.items()}
for c, p in parts.items():
    print(f"{c:16} {cands[c]['release']}  {p}")
assert all(len(p) == 1 for p in parts.values())

# %% [markdown]
# ## 2 · Run the gate on the champion (6')
#
# The champion's numbers are the baseline every candidate is compared with. Each metric comes with its count and a
# 95% Wilson interval: with 24 cases, intervals are wide, which is why the gate's hard rules are on the metrics
# that must never fall (complete safety procedures, declining what is out of scope).

# %%
base = G.evaluate(champion)
print(base["model"])
print(pd.DataFrame(base["metrics"]).T.to_string())

# %% [markdown]
# ## 3 · Run the three candidates (8')
#
# ✏️ **Exercise** · Evaluate each candidate with `G.evaluate`, gate it against the champion with `G.gate`, and
# keep both in `results` and `decisions`.

# %%
results, decisions = {}, {}
try:
    # BEGIN SOLUTION
    for c, r in cands.items():
        results[c] = G.evaluate(r)
        decisions[c] = G.gate(results[c], base)
    # END SOLUTION
except NotImplementedError:  # safety net
    for c, r in cands.items():
        results[c] = G.evaluate(r)
        decisions[c] = G.gate(results[c], base)
table = pd.DataFrame({c: {m: v["rate"] for m, v in res["metrics"].items()} for c, res in {"champion": base, **results}.items()})
print(table.to_string())
for c, d in decisions.items():
    print(f"{c:16} {d['decision'].upper():5}  " + "; ".join(d["reasons"]))

# %% [markdown]
# ## 4 · Read by category and write the release log (7')
#
# ✏️ **Exercise** · For the blocked candidate, list the cases that passed in the champion and fail in the
# candidate, with the field that failed. Then write `artifacts/D2_2/release_log.jsonl`: one line per candidate
# with the release, the part that changed, the decision, the metric it was decided on and the reasons.

# %%
blocked = [c for c, d in decisions.items() if d["decision"] == "block"]
try:
    # BEGIN SOLUTION
    regressions = []
    for c in blocked:
        champ_rows = {r["id"]: r for r in base["rows"]}
        for r in results[c]["rows"]:
            if champ_rows[r["id"]]["passed"] and not r["passed"]:
                failed = [f for f in ("facts", "cites", "refuses", "steps") if not r[f]]
                regressions.append({"candidate": c, "case": r["id"], "category": r["category"], "failed": failed,
                                    "answer": r["answer"]})
    with (OUT / "release_log.jsonl").open("w", encoding="utf-8") as f:
        for c, d in decisions.items():
            metric = "safety_steps_complete" if any("safety" in x for x in d["reasons"]) else "all gate rules"
            f.write(json.dumps({"release": cands[c]["release"], "changed": list(parts[c]), "decision": d["decision"],
                                "decided_on": metric, "reasons": d["reasons"]}) + "\n")
    # END SOLUTION
except NotImplementedError:  # safety net
    regressions = K.reference("D2_2_regressions")
    with (OUT / "release_log.jsonl").open("w", encoding="utf-8") as f:
        for c, d in decisions.items():
            f.write(json.dumps({"release": cands[c]["release"], "decision": d["decision"], "reasons": d["reasons"]}) + "\n")
K.save_reference("D2_2_regressions", regressions)
for r in regressions:
    print(r["candidate"], r["case"], r["category"], r["failed"], "|", r["answer"][:150])
print((OUT / "release_log.jsonl").read_text(encoding="utf-8"))
ship = sorted(c for c, d in decisions.items() if d["decision"] == "ship")
assert ship == ["cand_index_v4", "cand_prompt_v2"] and blocked == ["cand_model_swap"], decisions
K.check(True, "two releases ship, the model swap is blocked on safety_steps_complete")

# %% [markdown]
# 🔍 The model swap keeps the same answer score as the champion overall. Read the failing answer: which steps of the
# isolation procedure are missing, and what could a crew do without them?

# %% [markdown]
# ## ✱ Stretch · A live free model
#
# With a working OpenRouter key in `.env`, `K.live()` is true and the same code calls a free hosted model. Run the
# champion and the prompt-edit candidate live and compare their tables with the stand-in's.

# %%
try:
    # BEGIN SOLUTION
    if K.live():
        live = {name: G.evaluate(nabd.load_release(name), limit=K.pick(24, 8)) for name in ("champion", "cand_prompt_v2")}
        print(pd.DataFrame({n: {m: v["rate"] for m, v in e["metrics"].items()} for n, e in live.items()}).to_string())
    else:
        print("no working key: the stand-in results above are the course's reference run")
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. The model swap's case pass rate fell by less than the allowed 0.05. Why is it still blocked?
#    <details><summary>Answer</summary>Safety procedures have a floor of 1.00 and no allowed drop: one incomplete
#    isolation procedure blocks the release whatever the average says.</details>
# 2. The index refresh changed no code and no prompt. Why does it go through the same gate?
#    <details><summary>Answer</summary>The index decides what the model reads; a refresh can lose a section or
#    change which manual answers a question, exactly like a model change.</details>
# 3. With 24 cases, the interval on answer correctness is wide. What do you do about it?
#    <details><summary>Answer</summary>Keep hard rules for the metrics that must not fall, grow the case set where
#    decisions are close, and let the canary (Session 3) add evidence from real traffic.</details>
#
# ## Carry forward
#
# `artifacts/D2_2/release_log.jsonl` is the start of the release log the capstone keeps. Lab 2.3 adds the canary's
# rollback to it.
