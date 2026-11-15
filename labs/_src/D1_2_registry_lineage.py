# %% [markdown]
# # Lab 1.2 · Reproduce a model from the registry
#
# Day 1 · Session 2 (Registries and lineage) · 25 min.
#
# Lamya Al-Muqbil trained the fault-risk model that has been the champion since August. She is on leave, and the
# asset team wants to know whether the champion can be rebuilt exactly. You start from the registry, follow the
# champion's lineage to its data snapshot and its training code, retrain, and prove that the result matches.
#
# **Reference state.** The setup cell builds the registry as it stood in October (MLflow, in a local folder):
# versions 1 to 3 of `fault-risk`, version 3 carrying the alias `champion`, and the content-addressed snapshot
# store the versions point to.
#
# **Tasks**
# - [ ] 1 · Find the champion and read its lineage (6')
# - [ ] 2 · Rebuild the data snapshot and check its hash (6')
# - [ ] 3 · Retrain with the recorded parameters (7')
# - [ ] 4 · Compare metric and predictions (6')
# - [ ] ✱ Stretch · Show why the latest training file does not reproduce the model

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
# The reference state: the registry as it stood in October (about a minute)
REG = K.lab_dir("D1_2/registry")
client = K.seed_registry(REG, quiet=False)

# %% [markdown]
# ## 1 · Find the champion and read its lineage (6')
#
# The alias `champion` points at one version. The version points at the run that trained it; the run holds the
# parameters, and the tags hold the lineage: the hash of the data snapshot and the hash of the training code.
#
# ✏️ **Exercise** · Write `lineage(client)` returning the champion's `version`, `run_id`, `months` (a list),
# `features` (a list), `params` (a dict) and the tags `data_snapshot` and `code_hash`. MLflow returns every
# parameter as a **string**: turn the training parameters back into numbers.

# %%
NUMERIC = {"max_iter": int, "max_leaf_nodes": int, "random_state": int, "learning_rate": float, "recent_weight": float}


def lineage(client) -> dict:
    # BEGIN SOLUTION
    mv = client.get_model_version_by_alias("fault-risk", "champion")
    run = client.get_run(mv.run_id)
    p = run.data.params
    return {"version": int(mv.version), "run_id": mv.run_id, "months": p["months"].split(","),
            "features": p["features"].split(","), "params": {k: f(p[k]) for k, f in NUMERIC.items()},
            "data_snapshot": run.data.tags["data_snapshot"], "code_hash": run.data.tags["code_hash"],
            "author": run.data.tags.get("author")}
    # END SOLUTION


# %%
try:
    lin = lineage(client)
except NotImplementedError:
    mv = client.get_model_version_by_alias("fault-risk", "champion")
    run = client.get_run(mv.run_id)
    p = run.data.params
    lin = {"version": int(mv.version), "run_id": mv.run_id, "months": p["months"].split(","), "features": p["features"].split(","),
           "params": {k: f(p[k]) for k, f in NUMERIC.items()}, "data_snapshot": run.data.tags["data_snapshot"],
           "code_hash": run.data.tags["code_hash"], "author": run.data.tags.get("author")}
print({k: v for k, v in lin.items() if k != "features"})
assert lin["version"] == 3 and lin["months"][0] == "2025-11" and lin["months"][-1] == "2026-07", lin
K.check(isinstance(lin["params"]["max_iter"], int), "parameters are numbers again, not strings")

# %% [markdown]
# ## 2 · Rebuild the data snapshot and check its hash (6')
#
# The snapshot store is content-addressed, as DVC or lakeFS keep data: the file's name is its hash. A colleague
# can rebuild the training frame from the monthly batches, or fetch it from the store, and either way the hash
# says whether it is the same data.
#
# ✏️ **Exercise** · Rebuild the training frame from the champion's months with `K.training_frame(months)`,
# snapshot it into a new store with `K.snapshot(df, store)`, and compare the hash with the tag.

# %%
STORE2 = K.lab_dir("D1_2/my_store")
try:
    # BEGIN SOLUTION
    df = K.training_frame(lin["months"])
    my_hash, my_path = K.snapshot(df, STORE2)
    # END SOLUTION
except NotImplementedError:  # safety net: the reference rebuild
    df = K.training_frame(lin["months"])
    my_hash, my_path = K.snapshot(df, STORE2)
print(len(df), "rows | rebuilt", K.short(my_hash), "| registry", K.short(lin["data_snapshot"]))
assert my_hash == lin["data_snapshot"], "the rebuilt data is not the data the champion was trained on"
K.check(True, "the data snapshot matches the registry")
K.check(K.code_hash() == lin["code_hash"], "the training code is the version the champion was trained with")

# %% [markdown]
# ## 3 · Retrain with the recorded parameters (7')
#
# ✏️ **Exercise** · Train `mine` with `K.train_fault_model(df, features, params)` using the champion's features and
# parameters.

# %%
try:
    # BEGIN SOLUTION
    mine = K.train_fault_model(df, lin["features"], lin["params"])
    # END SOLUTION
except NotImplementedError:  # safety net
    mine = K.train_fault_model(df, lin["features"], lin["params"])
print(type(mine).__name__, mine.get_params()["max_iter"], "iterations")

# %% [markdown]
# ## 4 · Compare metric and predictions (6')
#
# Same metric is not enough: two different models can share an AUC. Compare the predictions on the holdout feeders
# of July, row by row.
#
# ✏️ **Exercise** · The champion is loaded for you with `K.load_registered`. Predict with your model on the same
# holdout feeders of July, and compute the largest absolute difference of the two predictions and both AUCs.

# %%
hold = K.holdout_frame("2026-07")
mv, champ = K.load_registered(client, "champion")
p_champ = K.predict_risk(champ, hold)
try:
    # BEGIN SOLUTION
    p_mine = K.predict_risk(mine, hold)
    max_diff = float(abs(p_champ - p_mine).max())
    auc_champ = K.auc_by_region(hold["fault_30d"], p_champ, hold["region"])["all"]
    auc_mine = K.auc_by_region(hold["fault_30d"], p_mine, hold["region"])["all"]
    # END SOLUTION
except NotImplementedError:  # safety net
    p_mine = K.predict_risk(mine, hold)
    max_diff = float(abs(p_champ - p_mine).max())
    auc_champ = auc_mine = K.auc_by_region(hold["fault_30d"], p_champ, hold["region"])["all"]
print(f"largest difference {max_diff:.2e} | AUC champion {auc_champ} | AUC reproduced {auc_mine}")
assert max_diff < 1e-9 and auc_champ == auc_mine
K.check(True, "reproduced: same data hash, same code hash, same predictions")

# %% [markdown]
# ## ✱ Stretch · The latest training file
#
# The team's shared folder has "the training data": every batch up to August. Train on it with the same code and
# parameters and compare its hash and its predictions with the champion's.

# %%
try:
    # BEGIN SOLUTION
    latest = K.training_frame(K.MONTHS[:10])
    h_latest, _ = K.snapshot(latest, STORE2)
    other = K.train_fault_model(latest, lin["features"], lin["params"])
    print("hash", K.short(h_latest), "!= registry", K.short(lin["data_snapshot"]),
          f"| largest prediction difference {abs(K.predict_risk(other, hold) - p_champ).max():.3f}")
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. The rebuilt model has the same AUC but the hashes differ. Is it a reproduction?
#    <details><summary>Answer</summary>No. Equal metrics can come from different data; the hash of the snapshot and
#    the predictions row by row are the evidence.</details>
# 2. Why are the parameters strings when you read them back?
#    <details><summary>Answer</summary>The tracking store keeps parameters as text. Code that retrains from the
#    registry must convert them, or a learning rate of "0.05" breaks or silently changes the run.</details>
# 3. What would you add to the registry entry so that the next person needs nothing from Lamya?
#    <details><summary>Answer</summary>Everything that changes behaviour: the snapshot hash and store, the code
#    hash or commit, the parameters, the feature list, and the environment lock file.</details>
#
# ## Carry forward
#
# Labs 1.4 and 3.4 start from the same registry, rebuilt by `K.seed_registry`, and promote by moving the
# `champion` alias.
