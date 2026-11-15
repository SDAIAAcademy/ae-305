# %% [markdown]
# # Lab 4.3 · Replay incident INC-0412
#
# Day 4 · Session 3 (Replay to reproduce incidents) · 25 min.
#
# A customer in Al-Jabal was told by Mubadir that power was back on his feeder. He called again 40 minutes later:
# the outage had never ended. You replay the recorded session from its stored model outputs and tool responses,
# find the cause in the trace, fix the harness so the same session cannot close the report again, and add the
# incident to the regression suite that runs on every harness change.
#
# **Reference state.** `data/replay/INC-0412.json` (the recorded session, invented for the course), the five
# regression cases in `data/replay/suite.json`, and `M.replay`, which runs a recording through today's harness:
# the model outputs and tool responses come from the recording, the guards are the current code.
#
# **Tasks**
# - [ ] 1 · Read the recorded trace (5')
# - [ ] 2 · Replay it: the same wrong answer (7')
# - [ ] 3 · Fix the harness (7')
# - [ ] 4 · The new regression case and the suite (6')
# - [ ] ✱ Stretch · Replay the whole suite against a new bundle

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
import shutil

import mubadir as M

OUT = K.lab_dir("D4_3")
incident = K.read_json(K.DATA / "replay" / "INC-0412.json")
print(incident["summary"])
print("service note:", incident["service_note"])

# %% [markdown]
# ## 1 · Read the recorded trace (5')
#
# ✏️ **Exercise** · Print the session step by step (the model's action, then the tool's result). Then set
# `CAUSE_STEP` to the step whose tool result was wrong, and `CAUSE` to what was wrong with it.

# %%
for e in incident["events"]:
    if e["type"] == "model":
        print(f"step {e['step']} model -> {e['content']}")
    elif e["type"] == "tool":
        print(f"step {e['step']} tool  <- {e['result']}")
try:
    # BEGIN SOLUTION
    CAUSE_STEP = 2
    CAUSE = "get_outage answered 'restored' from a replica 140 minutes behind, and the agent closed the report on it"
    # END SOLUTION
except NotImplementedError:  # safety net
    CAUSE_STEP, CAUSE = 2, "a stale 'restored' status"
print(CAUSE_STEP, CAUSE)

# %% [markdown]
# 🔍 The model did what its prompt says: restored, so close the report. Was the model wrong? Where should the check
# live: in the prompt, in the model, or in the harness that runs the tool?

# %% [markdown]
# ## 2 · Replay it: the same wrong answer (7')
#
# Replay needs no model and no services: every model output and every tool response is in the recording, so the
# session runs again exactly, through today's harness.
#
# ✏️ **Exercise** · Replay the incident with no extra guard and check that it ends with the same final answer as
# the recording.

# %%
try:
    # BEGIN SOLUTION
    before = M.replay(incident)
    # END SOLUTION
except NotImplementedError:  # safety net
    before = M.replay(incident)
for t in before["trace"]:
    print(t)
assert before["final"] == incident["final"]
K.check(True, "the replay reproduces INC-0412 exactly")

# %% [markdown]
# ## 3 · Fix the harness (7')
#
# A guard is a function `guard(action, history)` that the harness calls before running a tool; it returns `None` to
# allow the call or a reason to block it. The agent then sees the block as the tool's result.
#
# ✏️ **Exercise** · Write `freshness_guard`: block `close_report` unless the most recent `get_outage` result in
# the history says `"restored"` and is at most `MAX_AGE_MIN` minutes old. Replay the incident with it.

# %%
MAX_AGE_MIN = 15


def freshness_guard(action: dict, history: list[dict]):
    # BEGIN SOLUTION
    if action.get("tool") != "close_report":
        return None
    outages = [e["result"] for e in history if e.get("type") == "tool" and e.get("tool") == "get_outage"]
    if not outages:
        return "close_report needs a get_outage check first"
    last = outages[-1]
    if last.get("status") != "restored":
        return f"outage status is {last.get('status')}, not restored"
    if last.get("age_minutes", 0) > MAX_AGE_MIN:
        return f"outage status is {last['age_minutes']} minutes old (limit {MAX_AGE_MIN}): confirm with the control room"
    return None
    # END SOLUTION


def reference_guard(action, history):
    if action.get("tool") != "close_report":
        return None
    outs = [e["result"] for e in history if e.get("type") == "tool" and e.get("tool") == "get_outage"]
    if not outs or outs[-1].get("status") != "restored" or outs[-1].get("age_minutes", 0) > MAX_AGE_MIN:
        return f"outage status not confirmed fresh (limit {MAX_AGE_MIN} minutes)"
    return None


try:
    freshness_guard({"tool": "find_customer"}, [])
except NotImplementedError:  # safety net
    freshness_guard = reference_guard
after = M.replay(incident, guards=[freshness_guard])
for t in after["trace"]:
    print(t)
assert after["diverged"] and after["blocked"] == "close_report"
K.check(True, "with the guard, the replay stops before close_report")

# %% [markdown]
# 🔍 With the guard on, what does the live agent do next? (It cannot close the report; the report stays open and
# goes to a person. The stand-in model would check the outage again: Lab 4.4's step limit bounds that.)

# %% [markdown]
# ## 4 · The new regression case and the suite (6')
#
# ✏️ **Exercise** · Copy the suite to `artifacts/D4_3/suite/`, add the incident as a case that expects
# `close_report` to be blocked, and run every case with and without the guard. The fix must not break a case that
# passed: a fresh "restored" must still close the report.

# %%
suite_dir = OUT / "suite"
shutil.copytree(K.DATA / "replay", suite_dir, dirs_exist_ok=True)
suite = K.read_json(suite_dir / "suite.json")
try:
    # BEGIN SOLUTION
    suite["cases"].append({"name": "INC-0412", "recording": "INC-0412.json", "expect": {"blocked_tool": "close_report"},
                           "why": "a stale 'restored' must not close a report"})
    # END SOLUTION
except NotImplementedError:  # safety net
    suite["cases"].append({"name": "INC-0412", "recording": "INC-0412.json", "expect": {"blocked_tool": "close_report"}})
K.write_json(suite_dir / "suite.json", suite)


def run_suite(guards, settings=None) -> dict:
    out = {}
    for case in suite["cases"]:
        rec = K.read_json(suite_dir / case["recording"])
        r = M.replay(rec, guards, settings)
        exp = case["expect"]
        if "blocked_tool" in exp:
            out[case["name"]] = r.get("blocked") == exp["blocked_tool"]
        else:
            out[case["name"]] = (not r["diverged"]) and exp["final_contains"] in (r["final"] or "")
    return out


table = {"without guard": run_suite([]), "with guard": run_suite([freshness_guard])}
for name in table["with guard"]:
    print(f"{name:22} without: {'pass' if table['without guard'][name] else 'FAIL':5} with: {'pass' if table['with guard'][name] else 'FAIL'}")
K.write_json(OUT / "suite_results.json", table)
assert all(table["with guard"].values()) and not table["without guard"]["INC-0412"]
K.check(True, "six of six cases pass with the guard; INC-0412 fails without it")

# %% [markdown]
# ## ✱ Stretch · The suite against a new bundle
#
# A new bundle removes `close_report` from the sandbox's allowed tools (closing goes to a person). Replay the
# suite with that bundle's settings. Which cases change, and is that what the bundle intends?

# %%
try:
    # BEGIN SOLUTION
    new = M.load_settings()
    new["sandbox"] = dict(new["sandbox"], allowed_tools=[t for t in new["sandbox"]["allowed_tools"] if t != "close_report"])
    results = run_suite([freshness_guard], new)
    print({k: ("pass" if v else "FAIL") for k, v in results.items()})
    print("changed:", [k for k in results if results[k] != table["with guard"][k]])
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. Why replay from the recording instead of running the same report again against the services?
#    <details><summary>Answer</summary>The services have moved on (the replica caught up) and a model can answer
#    differently; the recording holds exactly what happened, so the failure comes back every time.</details>
# 2. Why fix this in the harness and not only in the prompt?
#    <details><summary>Answer</summary>A guard runs on every call and can be tested by replay; a prompt instruction
#    is followed most of the time.</details>
# 3. What makes a regression case worth keeping?
#    <details><summary>Answer</summary>It reproduces a real failure, states what must happen instead, and runs on
#    every change to the bundle, so the incident cannot come back unnoticed.</details>
#
# ## Carry forward
#
# The suite with INC-0412 runs in the capstone on every change to Mubadir's bundle. Its post-incident note is part
# of the capstone's runbook.
