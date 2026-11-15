# %% [markdown]
# # Lab 3.4 · A retraining trigger with a cost and an approval
#
# Day 3 · Session 4 (Retraining and refresh policies) · 25 min.
#
# The fault-risk classifier was retrained by a script on a fixed day each month, whatever the data said, and once
# on labels that were not complete (Lab 1.4's challenger A). You write the policy that replaces it: retrain on a
# drift alert or the monthly schedule, but only once the batch's labels are complete; state the cost; ask a person
# to approve; then run the whole pipeline on the drifted August batch (it promotes) and on the corrupt September
# batch (it stops), with the lineage in the registry.
#
# **Reference state.** The registry of Lab 1.4 before the challengers (champion v3), the label calendar below,
# Lab 3.2's alerts, October's cost log, and the contract in `contracts.py`. The registry takes about a minute to
# build.
#
# **Tasks**
# - [ ] 1 · Drift or schedule, and labels ready (6')
# - [ ] 2 · The cost estimate (5')
# - [ ] 3 · Human approval (5')
# - [ ] 4 · Test on the drifted and the corrupt batch (9')
# - [ ] ✱ Stretch · Treat the manuals index refresh as a release under the same policy

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
# The reference state: the registry with the champion v3 (about a minute)
import json

import pandas as pd

import contracts

OUT = K.lab_dir("D3_4")
client = K.seed_registry(OUT / "registry")
print("champion:", client.get_model_version_by_alias("fault-risk", "champion").version)

# When each month's labels are complete: 30 days after the month for most feeders, about a month more for the
# Al-Jabal inspections. Months before August are complete.
LABELS_COMPLETE = {"2026-08": "2026-10-02", "2026-09": "2026-11-01", "2026-10": "2026-12-02"}
FIRST_CUT = {"2026-08": "2026-09-12"}  # the early delivery that challenger A was trained on

# %% [markdown]
# ## 1 · Drift or schedule, and labels ready (6')
#
# A trigger says **when** to consider retraining; a condition says whether the data is ready. A signal is either
# the monthly schedule or a drift alert that Lamya has triaged as a change in the world (`"drift"`) or as a
# measurement problem (`"skew"`, Lab 3.2's load step).
#
# ✏️ **Exercise** · Write `decide(signal, as_of)` returning `{"action", "batch", "why"}`:
# - `skew`: action `"no"`, fix the data with its owner instead;
# - otherwise the batch is the newest month whose labels are complete on `as_of` (a month not in
#   `LABELS_COMPLETE` is complete);
# - a drift alert whose month's labels are not complete yet: action `"wait"`, with the date they will be;
# - a batch already trained on (in `trained`): action `"no"`;
# - otherwise `"retrain"`.

# %%
trained = {"2026-07"}  # the newest month in the champion's training data


def decide(signal: dict, as_of: str) -> dict:
    # BEGIN SOLUTION
    if signal.get("triage") == "skew":
        return {"action": "no", "batch": None, "why": f"{signal['feature']} is skew: fix the data with its owner, do not retrain"}
    ready = [m for m in K.MONTHS if LABELS_COMPLETE.get(m, "0000") <= as_of]
    batch = ready[-1]
    if signal["kind"] == "drift" and signal["month"] not in ready:
        return {"action": "wait", "batch": signal["month"],
                "why": f"labels of {signal['month']} complete on {LABELS_COMPLETE[signal['month']]}; a first cut is not enough"}
    if batch in trained:
        return {"action": "no", "batch": batch, "why": f"{batch} is already in the champion's training data"}
    return {"action": "retrain", "batch": batch, "why": f"{signal['kind']} signal; labels of {batch} complete"}
    # END SOLUTION


def reference_decide(signal, as_of):
    if signal.get("triage") == "skew":
        return {"action": "no", "batch": None, "why": "skew: fix the data"}
    ready = [m for m in K.MONTHS if LABELS_COMPLETE.get(m, "0000") <= as_of]
    if signal["kind"] == "drift" and signal["month"] not in ready:
        return {"action": "wait", "batch": signal["month"], "why": f"labels complete on {LABELS_COMPLETE[signal['month']]}"}
    if ready[-1] in trained:
        return {"action": "no", "batch": ready[-1], "why": "already trained on"}
    return {"action": "retrain", "batch": ready[-1], "why": f"{signal['kind']}; labels of {ready[-1]} complete"}


SIGNALS = [
    ({"kind": "drift", "feature": "dust_index", "month": "2026-08", "triage": "drift"}, "2026-09-20"),
    ({"kind": "drift", "feature": "load_peak_pct", "month": "2026-10", "triage": "skew"}, "2026-10-14"),
    ({"kind": "schedule", "month": "2026-10"}, "2026-10-03"),
    ({"kind": "schedule", "month": "2026-11"}, "2026-11-03"),
]
try:
    decisions = [decide(s, d) for s, d in SIGNALS]
except NotImplementedError:  # safety net
    decide = reference_decide
    decisions = [decide(s, d) for s, d in SIGNALS]
for (s, d), dec in zip(SIGNALS, decisions):
    print(f"{d} {s['kind']:8} {s.get('feature', ''):14} -> {dec['action']:7} {dec['batch']}  {dec['why']}")
assert [d["action"] for d in decisions] == ["wait", "no", "retrain", "retrain"]
assert [d["batch"] for d in decisions[2:]] == ["2026-08", "2026-09"]

# %% [markdown]
# 🔍 On 20 September the August drift alert waits twelve days. What happened when a script did not wait? (Lab 1.4:
# challenger A learned that the most wooded Al-Jabal feeders never fault.)

# %% [markdown]
# ## 2 · The cost estimate (5')
#
# October's cost log (Lab 2.4) shows what one retraining run costs in production: the extra processor hours on
# the day it ran.
#
# ✏️ **Exercise** · Compute `run_cost`: the classifier's node-hours on 3 October minus the median of the other
# days, at the node-hour price. Then `budget_left`: October's classifier budget minus its spend without that run.
# A retrain is within policy if it costs less than what is left.

# %%
logs = pd.read_csv(K.DATA / "reference" / "cost_month.csv")
clf = logs[logs.system == "classifier"].set_index("date")
P = K.prices()
BUDGET = K.read_json(K.DATA / "budgets.json")["classifier"]
try:
    # BEGIN SOLUTION
    extra_hours = clf.loc["2026-10-03", "cpu_node_hours_used"] - clf.drop(index="2026-10-03").cpu_node_hours_used.median()
    run_cost = round(extra_hours * P["cpu_node_hour"], 2)
    month_spend = clf.cpu_node_hours_used.sum() * P["cpu_node_hour"]
    budget_left = round(BUDGET - (month_spend - run_cost), 2)
    # END SOLUTION
except NotImplementedError:  # safety net
    extra_hours = clf.loc["2026-10-03", "cpu_node_hours_used"] - clf.drop(index="2026-10-03").cpu_node_hours_used.median()
    run_cost = round(extra_hours * P["cpu_node_hour"], 2)
    budget_left = round(BUDGET - (clf.cpu_node_hours_used.sum() * P["cpu_node_hour"] - run_cost), 2)
cost = {"node_hours": round(float(extra_hours), 2), "run_cost_sar": float(run_cost), "budget_left_sar": float(budget_left),
        "within_policy": bool(run_cost < budget_left)}
print(cost)

# %% [markdown]
# 🔍 The compute is a few riyals. What does a retrain really cost Wahaj? (The reviewer's hour, the risk of a worse
# model in one region, and a release to roll back if it goes wrong.)

# %% [markdown]
# ## 3 · Human approval (5')
#
# The pipeline may train and gate on its own; it may not promote on its own. The model owner approves, and the
# approval is recorded on the registry version with the evidence it was given.
#
# ✏️ **Exercise** · Write `approve(request, approver)`: refuse an approver who is not in `APPROVERS` or who is the
# requester; otherwise return the request with `approved_by` and `approved_at`.

# %%
APPROVERS = {"Lamya Al-Muqbil", "Dhafer Al-Hazzani"}


def approve(request: dict, approver: str) -> dict:
    # BEGIN SOLUTION
    if approver not in APPROVERS:
        raise PermissionError(f"{approver} may not approve a promotion of fault-risk")
    if approver == request["requested_by"]:
        raise PermissionError("the requester cannot approve its own request")
    return dict(request, approved_by=approver, approved_at=request["as_of"])
    # END SOLUTION


try:
    approve({"requested_by": "retrain pipeline", "as_of": "2026-10-03"}, "Lamya Al-Muqbil")
except NotImplementedError:  # safety net
    def approve(request, approver):
        if approver not in APPROVERS or approver == request["requested_by"]:
            raise PermissionError(f"{approver} may not approve this request")
        return dict(request, approved_by=approver, approved_at=request["as_of"])
for who in ("retrain pipeline", "Saqer Al-Dossary", "Lamya Al-Muqbil"):
    try:
        print(who, "->", approve({"requested_by": "retrain pipeline", "as_of": "2026-10-03"}, who)["approved_by"])
    except PermissionError as e:
        print(who, "-> refused:", e)

# %% [markdown]
# ## 4 · Test on the drifted and the corrupt batch (9')
#
# The pipeline: load the batch, validate it against the contract, train on the seven months ending with it,
# register the challenger with its lineage, gate it against the champion (Lab 1.4's rule), ask for approval, and
# promote by moving the alias. Every step but the approval is written for you.
#
# ✏️ **Exercise** · Run the pipeline for the two `retrain` decisions of step 1, with Lamya approving, and print
# both run logs. Then read the champion's lineage from the registry.

# %%
def gate(table, tolerance=0.03):
    champ, ch = table.loc["champion"], table.loc["challenger"]
    reasons = [f"overall AUC {ch['all']:.3f} is not above {champ['all']:.3f}"] if ch["all"] <= champ["all"] else []
    reasons += [f"{K.REGIONS[r]} AUC {ch[r]:.3f} is more than {tolerance} below {champ[r]:.3f}"
                for r in K.REGIONS if ch[r] < champ[r] - tolerance]
    return not reasons, reasons or ["passed overall and in every region"]


def s_load(ctx):
    return {"df": K.load_batch(ctx["batch"])}


def s_train(ctx):
    i = K.MONTHS.index(ctx["batch"])
    months = K.MONTHS[i - 6: i + 1]
    df = K.training_frame(months)
    h, _ = K.snapshot(df, OUT / "registry" / "snapshots")
    model = K.train_fault_model(df, K.FEATURES, K.TRAIN_PARAMS)
    v = K.register_fault_model(client, model, months=months, features=K.FEATURES, params=K.TRAIN_PARAMS, snapshot_hash=h,
                               metrics={}, author="retrain pipeline", note=f"{ctx['trigger']} retrain on {ctx['batch']}")
    client.set_registered_model_alias("fault-risk", "challenger", str(v))
    return {"version": v, "months": months}


def s_gate(ctx):
    hold = K.holdout_frame(ctx["batch"])
    table = pd.DataFrame({a: K.auc_by_region(hold["fault_30d"], K.predict_risk(K.load_registered(client, a)[1], hold), hold["region"])
                          for a in ("champion", "challenger")}).T
    ok, reasons = gate(table)
    if not ok:
        raise K.StopRun("gate: " + "; ".join(reasons))
    return {"gate": reasons[0], "auc": table.to_dict("index")}


def s_approve(ctx):
    request = {"model": "fault-risk", "version": ctx["version"], "batch": ctx["batch"], "trigger": ctx["trigger"],
               "cost_sar": cost["run_cost_sar"], "gate": ctx["gate"], "requested_by": "retrain pipeline", "as_of": ctx["as_of"]}
    return {"approval": approve(request, ctx["approver"])}


def s_promote(ctx):
    old = client.get_model_version_by_alias("fault-risk", "champion").version
    client.set_registered_model_alias("fault-risk", "previous-champion", old)
    client.set_registered_model_alias("fault-risk", "champion", str(ctx["version"]))
    for k in ("approved_by", "approved_at", "trigger", "cost_sar", "gate"):
        client.set_model_version_tag("fault-risk", str(ctx["version"]), k, str(ctx["approval"][k]))
    client.set_model_version_tag("fault-risk", str(ctx["version"]), "promoted_from", str(old))
    trained.add(ctx["batch"])
    return {"promoted": f"v{old} -> v{ctx['version']}"}


STEPS = [("load", s_load), ("validate", contracts.validate_step(OUT)), ("train", s_train), ("gate", s_gate),
         ("approve", s_approve), ("promote", s_promote)]

runs = {}
try:
    # BEGIN SOLUTION
    for (signal, as_of), dec in zip(SIGNALS, decisions):
        if dec["action"] == "retrain":
            ctx = {"batch": dec["batch"], "trigger": signal["kind"], "as_of": as_of, "approver": "Lamya Al-Muqbil"}
            runs[dec["batch"]] = K.run_flow("retrain", STEPS, ctx, trigger=signal["kind"], log_dir=OUT / "runs")
    # END SOLUTION
except NotImplementedError:  # safety net
    for (signal, as_of), dec in zip(SIGNALS, decisions):
        if dec["action"] == "retrain":
            ctx = {"batch": dec["batch"], "trigger": signal["kind"], "as_of": as_of, "approver": "Lamya Al-Muqbil"}
            runs[dec["batch"]] = K.run_flow("retrain", STEPS, ctx, trigger=signal["kind"], log_dir=OUT / "runs")
for log in runs.values():
    K.print_run(log)
gate_step = next((s for s in runs["2026-08"].steps if s["step"] == "gate" and s["status"] == "ok"), None)
if gate_step:
    print(pd.DataFrame(gate_step["output"]["auc"]).T.round(3).to_string())

champ = client.get_model_version_by_alias("fault-risk", "champion")
lineage = {"version": champ.version, **{k: champ.tags.get(k) for k in ("months", "data_snapshot", "code_hash", "trigger",
                                                                        "cost_sar", "approved_by", "approved_at", "promoted_from")}}
K.write_json(OUT / "champion_lineage.json", lineage)
print(json.dumps(lineage, indent=1))
assert runs["2026-08"].status == "succeeded" and runs["2026-09"].status == "stopped"
assert runs["2026-09"].steps[-1]["step"] == "validate" and lineage["approved_by"] == "Lamya Al-Muqbil"
K.check(True, f"August promoted v{champ.version} with its lineage; September stopped at validation")

# %% [markdown]
# 🔍 The September run stopped before training, so nothing reached the registry. Where would you look to know
# that it ran at all? (The run log in `artifacts/D3_4/runs/`, and an alert to the data owner.)

# %% [markdown]
# ## ✱ Stretch · The index refresh under the same policy
#
# Nabd's index has the same questions: when to refresh, whether the evaluation is ready, what it costs, who
# approves. Compare the fingerprints of manuals v3 and v4, list the manuals whose sections changed, and check that
# the offline evaluation set has at least one case citing each changed manual before the refresh may go to the
# gate (Lab 2.2).

# %%
try:
    # BEGIN SOLUTION
    import nabd

    old, new = nabd.Index("v3"), nabd.Index("v4")
    print("fingerprints:", old.fingerprint(), "->", new.fingerprint())
    before = {s["ref"]: s["text"] for s in old.sections}
    changed_docs = sorted({s["doc"] for s in new.sections if before.get(s["ref"]) != s["text"]})
    cited = {json.loads(l).get("must_cite") for l in (K.DATA / "eval" / "nabd_eval.jsonl").read_text(encoding="utf-8").splitlines()}
    missing = [d for d in changed_docs if d not in cited]
    print("changed manuals:", changed_docs, "| without an eval case:", missing or "none")
    print("refresh decision:", "to the gate, approver Saqer Al-Dossary" if not missing else "write cases first")
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. A drift alert fires on a feature on the 20th. Why might the right action be to wait?
#    <details><summary>Answer</summary>The labels that would show whether the model is wrong are not complete;
#    retraining on a first cut teaches the gaps. Wait for them, or act on the input (a data fix) if it is skew.</details>
# 2. The gate passed. Why does a person still approve?
#    <details><summary>Answer</summary>The gate checks what it was written to check. The owner answers for the model
#    and reads the evidence: data, cost, regional results.</details>
# 3. Where is the evidence that the new champion was approved, by whom, on which data?
#    <details><summary>Answer</summary>On its registry version: the tags for months, data snapshot, code hash,
#    trigger, cost and approval, and the run log.</details>
#
# ## Carry forward
#
# This pipeline is the capstone's retraining pipeline: it runs on a new batch during the release week.
