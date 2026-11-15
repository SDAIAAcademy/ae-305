# %% [markdown]
# # Lab 1.4 · Champion, challenger and the regional gate
#
# Day 1 · Session 4 (Promotion gates) · 25 min.
#
# In October two challengers wait in the registry. Both were trained on February to August, after salt fog started
# causing faults on coastal lines in Al-Sahil. You score the champion and both challengers on the same holdout
# feeders, compare them overall and in each of the six regions, write the promotion rule, and promote only the
# challenger that passes it, by moving the registry alias.
#
# **Reference state.** The setup cell builds the October registry: `fault-risk` with `champion` (trained November
# to July) and the aliases `challenger-a` and `challenger-b`.
#
# **Tasks**
# - [ ] 1 · Score the champion and two challengers (6')
# - [ ] 2 · AUC overall and by region (6')
# - [ ] 3 · The gate rule (7')
# - [ ] 4 · Promote by moving the alias (6')
# - [ ] ✱ Stretch · A bootstrap interval for the regional gap

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
# The reference state: the October registry (about a minute)
import pandas as pd

client = K.seed_registry(K.lab_dir("D1_4/registry"), challengers=True, quiet=False)
for alias in ("champion", "challenger-a", "challenger-b"):
    mv = client.get_model_version_by_alias("fault-risk", alias)
    print(f"{alias:13} v{mv.version}  {mv.description}")

# %% [markdown]
# ## 1 · Score the champion and two challengers (6')
#
# The holdout is the quarter of feeders no model was trained on, in the newest month with complete labels:
# August, the drifted month.
#
# ✏️ **Exercise** · Inside the loop, load each model with `K.load_registered(client, alias)`, keep its version in
# `versions`, and add one column of predicted risk per alias to `scores`, on `hold`.

# %%
hold = K.holdout_frame("2026-08")
ALIASES = ["champion", "challenger-a", "challenger-b"]
scores = pd.DataFrame({"feeder_id": hold["feeder_id"], "region": hold["region"], "fault_30d": hold["fault_30d"]})
versions = {}
for alias in ALIASES:
    try:
        # BEGIN SOLUTION
        mv, model = K.load_registered(client, alias)
        versions[alias] = int(mv.version)
        scores[alias] = K.predict_risk(model, hold)
        # END SOLUTION
    except NotImplementedError:  # safety net
        mv, model = K.load_registered(client, alias)
        versions[alias] = int(mv.version)
        scores[alias] = K.predict_risk(model, hold)
print(len(scores), "holdout feeders |", scores.groupby("region").fault_30d.mean().round(2).to_dict())

# %% [markdown]
# ## 2 · AUC overall and by region (6')
#
# ✏️ **Exercise** · Build `table`: one row per alias, one column per region plus `all`, with
# `K.auc_by_region(y, p, regions)`.

# %%
try:
    # BEGIN SOLUTION
    table = pd.DataFrame({a: K.auc_by_region(scores["fault_30d"], scores[a], scores["region"]) for a in ALIASES}).T
    # END SOLUTION
except NotImplementedError:  # safety net
    table = pd.DataFrame({a: K.auc_by_region(scores["fault_30d"], scores[a], scores["region"]) for a in ALIASES}).T
print(table.to_string())

# %% [markdown]
# 🔍 Look at the `all` column alone. Which challenger would you promote? Now look at Al-Sahil (`SAH`) and
# Al-Jabal (`JAB`).

# %% [markdown]
# ## 3 · The gate rule (7')
#
# Wahaj's rule: a challenger is promoted only if it is **better than the champion overall** and **no more than
# 0.03 AUC worse in any region**. The tolerance is there because a region's AUC on 200 feeders moves by about
# that much between samples.
#
# ✏️ **Exercise** · Write `gate(table, challenger, tolerance=0.03)` returning `(passed, reasons)`, with one reason
# per rule that failed (or `"passed overall and in every region"`).

# %%
def gate(table: pd.DataFrame, challenger: str, tolerance: float = 0.03) -> tuple[bool, list[str]]:
    # BEGIN SOLUTION
    champ, ch = table.loc["champion"], table.loc[challenger]
    reasons = []
    if ch["all"] <= champ["all"]:
        reasons.append(f"overall AUC {ch['all']:.3f} is not above the champion's {champ['all']:.3f}")
    for r in K.REGIONS:
        if ch[r] < champ[r] - tolerance:
            reasons.append(f"{K.REGIONS[r]} AUC {ch[r]:.3f} is {champ[r] - ch[r]:.3f} below the champion's {champ[r]:.3f}")
    return (not reasons), (reasons or ["passed overall and in every region"])
    # END SOLUTION


# %%
try:
    decisions = {c: gate(table, c) for c in ("challenger-a", "challenger-b")}
except NotImplementedError:  # safety net: the reference decisions
    decisions = {c: tuple(v) for c, v in K.reference("D1_4_decisions").items()}
K.save_reference("D1_4_decisions", decisions)
for c, (ok, why) in decisions.items():
    print(f"{c}: {'PROMOTE' if ok else 'REJECT'}: " + "; ".join(why))
assert decisions["challenger-a"][0] is False and any("Al-Jabal" in w for w in decisions["challenger-a"][1])
assert decisions["challenger-b"][0] is True
K.check(True, "challenger-a is better overall but fails Al-Jabal; challenger-b passes both rules")

# %% [markdown]
# 🔍 Challenger A was trained on the first cut of the August batch, delivered before the inspections of the most
# wooded Al-Jabal feeders were entered (mountain access is slow). Its training data said those feeders had no
# faults. Day 3 comes back to delayed labels.

# %% [markdown]
# ## 4 · Promote by moving the alias (6')
#
# Promotion changes no file and no service: the serving code loads `models:/fault-risk@champion`, so moving the
# alias is the release. Keep the old champion reachable for a rollback.
#
# ✏️ **Exercise** · Write `promote(client, alias, reason)`: point `previous-champion` at the current champion's
# version, point `champion` at the challenger's version, and tag the new version with `promoted_reason` and
# `promoted_from` (the old version).

# %%
def promote(client, alias: str, reason: str) -> int:
    # BEGIN SOLUTION
    old = client.get_model_version_by_alias("fault-risk", "champion").version
    new = client.get_model_version_by_alias("fault-risk", alias).version
    client.set_registered_model_alias("fault-risk", "previous-champion", old)
    client.set_registered_model_alias("fault-risk", "champion", new)
    client.set_model_version_tag("fault-risk", new, "promoted_reason", reason)
    client.set_model_version_tag("fault-risk", new, "promoted_from", old)
    return int(new)
    # END SOLUTION


# %%
winner = next(c for c, (ok, _) in decisions.items() if ok)
try:
    new_version = promote(client, winner, "; ".join(decisions[winner][1]) + f" (holdout 2026-08, tolerance 0.03)")
except NotImplementedError:  # safety net: the reference promotion
    old = client.get_model_version_by_alias("fault-risk", "champion").version
    client.set_registered_model_alias("fault-risk", "previous-champion", old)
    client.set_registered_model_alias("fault-risk", "champion", versions[winner])
    new_version = versions[winner]
champ_now = client.get_model_version_by_alias("fault-risk", "champion")
aliases = client.get_registered_model("fault-risk").aliases
print("aliases now:", dict(sorted(aliases.items())))
K.check(int(champ_now.version) == versions[winner], f"the champion alias points at {winner}")

# %% [markdown]
# ## ✱ Stretch · A bootstrap interval for the regional gap
#
# Resample the holdout feeders of one region 500 times and compute the 95% interval of (challenger-b minus champion)
# AUC in Al-Wadi. Does the interval include 0?

# %%
import numpy as np
from sklearn.metrics import roc_auc_score

try:
    # BEGIN SOLUTION
    rng = np.random.default_rng(305)
    w = scores[scores.region == "WAD"].reset_index(drop=True)
    gaps = []
    for _ in range(K.pick(500, 100)):
        s = w.iloc[rng.integers(0, len(w), len(w))]
        if s.fault_30d.nunique() == 2:
            gaps.append(roc_auc_score(s.fault_30d, s["challenger-b"]) - roc_auc_score(s.fault_30d, s["champion"]))
    print("Al-Wadi gap, 95% interval:", np.round(np.percentile(gaps, [2.5, 97.5]), 3))
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. A challenger is 0.02 better overall and 0.09 worse in one region. What does the gate do, and what do you tell
#    the region's manager?
#    <details><summary>Answer</summary>It rejects the challenger: an overall gain paid for by one region's crews is
#    not an improvement for them. Say which data caused it.</details>
# 2. Why does the gate allow a small drop in a region at all?
#    <details><summary>Answer</summary>A region's AUC on a few hundred feeders varies by a few hundredths between
#    samples; a rule with no tolerance would reject every challenger on noise. The bootstrap shows the size.</details>
# 3. Why promote by moving an alias instead of copying the model file into the service?
#    <details><summary>Answer</summary>The alias is one recorded change, it is undone by moving it back, and the
#    registry keeps who promoted what and why.</details>
#
# ## Carry forward
#
# `gate` and `promote` come back in Lab 3.4, where a retraining trigger runs the whole pipeline and the gate decides.
