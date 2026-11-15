# %% [markdown]
# # Lab 4.4 · Limits and a kill switch at the gateway
#
# Day 4 · Session 4 (Budgets, gateways and kill switches) · 25 min.
#
# On 14 October the outage service started answering `pending` for every feeder, and Mubadir asked it again, and
# again: the expensive days of Lab 2.4. You reproduce one runaway session with no limits, put step and spend limits
# at the gateway that every model call passes through, stop the whole agent version with a kill switch while
# sessions are running, and hand the stopped sessions to customer care without losing any of them.
#
# **Reference state.** `data/reference/runaway.json` (the report and the outage service's answer), the gateway
# `K.Gateway` (one process; in production a proxy such as LiteLLM), the session store `K.SessionStore` (SQLite)
# and the scripted stand-in model, which checks again while an outage is pending.
#
# **Tasks**
# - [ ] 1 · The runaway session without limits (4')
# - [ ] 2 · Step and spend limits (8')
# - [ ] 3 · The kill switch (7')
# - [ ] 4 · Sessions kept and handed over (6')
# - [ ] ✱ Stretch · The same limits as a LiteLLM proxy configuration

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
import re

import pandas as pd

import mubadir as M

OUT = K.lab_dir("D4_4")
runaway = K.read_json(K.DATA / "reference" / "runaway.json")
VERSION = "mubadir-2026.10.2"
DAILY_BUDGET = round(K.read_json(K.DATA / "budgets.json")["mubadir"] / 31, 2)
print(runaway, "| daily budget", DAILY_BUDGET, "SAR")

# %% [markdown]
# ## 1 · The runaway session without limits (4')
#
# The version running on 14 October had no step limit in its harness (here: up to 80 steps) and no gateway policy.

# %%
gw0 = K.Gateway()
svc = M.Services(OUT / "svc_runaway", outages=runaway["outages"])
r = M.run_session(runaway["report"], svc, gateway=gw0, version=VERSION, session_id="S-4400", max_steps=K.pick(200, 80))
s = gw0.sessions["S-4400"]
print(r["status"], "after", r["steps"], "model calls;", f"{s['spend']:.4f} SAR")
print("tools called:", pd.Series([e["tool"] for e in r["events"] if e["type"] == "tool"]).value_counts().to_dict())
usage = [e["usage"]["input_tokens"] for e in r["events"] if e["type"] == "model"]
print("input tokens per call: first", usage[0], "| last", usage[-1])
svc.close()

# %% [markdown]
# 🔍 Each call sends the whole conversation again, so each costs more than the last: the cost of a loop grows with
# the square of its length.

# %% [markdown]
# ## 2 · Step and spend limits (8')
#
# The gateway calls `policy(state)` before every model call; `state` has `session_steps`, `session_spend`,
# `day_spend` and `version`. A returned reason refuses the call, and the harness ends the session as
# `stopped_by_gateway`.
#
# ✏️ **Exercise** · Write `policy`: refuse when the session has made 12 calls, when it has spent 0.01 SAR, or when
# the agent's spend today has reached the daily budget. Say which limit in the reason.

# %%
STEP_LIMIT, SESSION_SPEND_LIMIT = 12, 0.01


def policy(state: dict) -> str | None:
    # BEGIN SOLUTION
    if state["session_steps"] >= STEP_LIMIT:
        return f"step limit: {state['session_steps']} calls in this session (limit {STEP_LIMIT})"
    if state["session_spend"] >= SESSION_SPEND_LIMIT:
        return f"session spend limit: {state['session_spend']:.4f} SAR (limit {SESSION_SPEND_LIMIT})"
    if state["day_spend"] >= DAILY_BUDGET:
        return f"daily budget: {state['day_spend']:.2f} SAR (budget {DAILY_BUDGET})"
    return None
    # END SOLUTION


try:
    policy({"session_steps": 0, "session_spend": 0.0, "day_spend": 0.0, "version": VERSION})
except NotImplementedError:  # safety net
    def policy(state):
        if state["session_steps"] >= STEP_LIMIT:
            return f"step limit {STEP_LIMIT}"
        if state["session_spend"] >= SESSION_SPEND_LIMIT:
            return f"session spend limit {SESSION_SPEND_LIMIT}"
        return f"daily budget {DAILY_BUDGET}" if state["day_spend"] >= DAILY_BUDGET else None
gw1 = K.Gateway(policy)
svc = M.Services(OUT / "svc_limited", outages=runaway["outages"])
r1 = M.run_session(runaway["report"], svc, gateway=gw1, version=VERSION, session_id="S-4401", max_steps=K.pick(200, 80))
print(r1["status"], "after", r1["steps"], "model calls;", f"{gw1.sessions['S-4401']['spend']:.4f} SAR")
print(gw1.events[-1])
svc.close()
assert r1["status"] == "stopped_by_gateway" and r1["steps"] <= STEP_LIMIT

# %% [markdown]
# 🔍 Why at the gateway and not only in the harness's `max_steps`? (The gateway sees every session of every
# version, including a harness with a bug or a new bundle that raised the limit; and it sees the money.)

# %% [markdown]
# ## 3 · The kill switch (7')
#
# On the morning of 14 October six customers write in while the outage service answers `pending` for every feeder.
# Limits stop each session; the duty engineer should not wait for six of them.
#
# ✏️ **Exercise** · Run the six sessions in order through one gateway with your policy and a session store. After
# each session, if two sessions of the version have been stopped by the step limit, Dhafer turns the kill switch
# on for `VERSION` (`gw.kill(VERSION, by=...)`). Count how many model calls the switch saved.

# %%
accounts = list(M.customers())[:6]
cust = M.customers()
outages = {cust[a]["feeder_id"]: {"status": "pending", "ticket": None, "age_minutes": 1} for a in accounts}
store = K.SessionStore(OUT / "sessions.db")
gw = K.Gateway(policy)
svc = M.Services(OUT / "svc_morning", outages=outages)
runs = []
try:
    # BEGIN SOLUTION
    for i, acc in enumerate(accounts, 1):
        res = M.run_session(f"Any news on my outage? Account {acc}.", svc, gateway=gw, version=VERSION,
                            session_id=f"S-44{10 + i}", store=store, max_steps=K.pick(200, 80))
        runs.append(res)
        stopped = sum(1 for e in gw.events if e["event"] == "refused" and e["why"].startswith("step limit"))
        if stopped >= 2 and VERSION not in gw.killed:
            gw.kill(VERSION, by="Dhafer Al-Hazzani")
    # END SOLUTION
except NotImplementedError:  # safety net
    for i, acc in enumerate(accounts, 1):
        runs.append(M.run_session(f"Any news on my outage? Account {acc}.", svc, gateway=gw, version=VERSION,
                                  session_id=f"S-44{10 + i}", store=store, max_steps=K.pick(200, 80)))
        if sum(e["event"] == "refused" for e in gw.events) >= 2 and VERSION not in gw.killed:
            gw.kill(VERSION, by="Dhafer Al-Hazzani")
for res in runs:
    print(res["session_id"], res["status"], res["steps"], "calls")
for e in gw.events:
    print(e)
calls = sum(res["steps"] for res in runs)
saved = STEP_LIMIT * len(runs) - calls
print(f"{calls} model calls; the kill switch saved {saved} calls; spend {gw.day_spend:.4f} SAR")
assert any(e["event"] == "kill switch on" for e in gw.events) and runs[-1]["steps"] == 0
svc.close()

# %% [markdown]
# ## 4 · Sessions kept and handed over (6')
#
# Stopping an agent must not drop the customers it was serving. Every session is in the store with its messages.
#
# ✏️ **Exercise** · Build `handover`: one row per stored session that did not finish (`status` not `"done"`), with
# the session id, the account (from the first user message), the steps, the spend, the last tool result, and a note
# for customer care. Write it to `artifacts/D4_4/handover.csv`.

# %%
sessions = store.all()
try:
    # BEGIN SOLUTION
    rows = []
    for s in sessions:
        if s["status"] == "done":
            continue
        msgs = s["messages"]
        account = re.search(r"ACC-\d{8}", msgs[1]["content"]).group(0)
        last_tool = next((m["content"] for m in reversed(msgs) if m["role"] == "user" and m["content"].startswith("Tool result")), "none")
        rows.append({"session": s["id"], "account": account, "status": s["status"], "steps": s["steps"],
                     "spend_sar": round(s["spend"], 4), "last_tool_result": last_tool[:120],
                     "note": "outage service answered pending; call the customer and confirm with the control room"})
    handover = pd.DataFrame(rows)
    # END SOLUTION
except NotImplementedError:  # safety net
    handover = pd.DataFrame([{"session": s["id"], "account": re.search(r"ACC-\d{8}", s["messages"][1]["content"]).group(0),
                              "status": s["status"], "steps": s["steps"], "note": "hand to customer care"}
                             for s in sessions if s["status"] != "done"])
handover.to_csv(OUT / "handover.csv", index=False)
print(handover.drop(columns=[c for c in ("last_tool_result",) if c in handover]).to_string(index=False))
store.close()
assert len(handover) == len(accounts)
K.check(True, f"{len(handover)} stopped sessions handed to customer care, none lost")

# %% [markdown]
# ## ✱ Stretch · The same limits in LiteLLM
#
# LiteLLM's proxy puts budgets on virtual keys, users and teams: `max_budget` with a `budget_duration` (for example
# `"1d"`), and rate limits that answer HTTP 429. Budgets need the proxy's database (PostgreSQL). One key per agent
# version makes the kill switch "delete the key". Write the proxy configuration and the key request for Mubadir,
# and check that they parse.

# %%
import yaml

try:
    # BEGIN SOLUTION
    CONFIG = """model_list:
  - model_name: steady
    litellm_params:
      model: openrouter/google/gemma-4-31b-it:free
      api_key: os.environ/OPENROUTER_API_KEY
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
"""
    KEY_REQUEST = {"models": ["steady"], "max_budget": DAILY_BUDGET, "budget_duration": "1d",
                   "metadata": {"agent": "mubadir", "version": VERSION}}
    yaml.safe_load(CONFIG)
    (OUT / "litellm_config.yaml").write_text(CONFIG, encoding="utf-8")
    K.write_json(OUT / "litellm_key_request.json", KEY_REQUEST)
    print(CONFIG)
    print("POST /key/generate", json.dumps(KEY_REQUEST))
    print("Per-session step limits stay in the harness and in the gateway policy of step 2.")
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. A step limit stops each runaway session. Why also have a kill switch per version?
#    <details><summary>Answer</summary>When every session of a version fails the same way, waiting for each to hit
#    its limit costs money and customers' time; one switch stops them all and the old version can take over.</details>
# 2. Why does the kill switch work on the version and not on the whole agent?
#    <details><summary>Answer</summary>So the previous version (or a person) keeps serving; stopping all of Mubadir
#    would be an outage of its own.</details>
# 3. What must survive a stop?
#    <details><summary>Answer</summary>Every session with its messages and state, so a person can finish the work
#    and the incident can be replayed.</details>
#
# ## Carry forward
#
# The policy, the kill switch and the handover file are part of the capstone's runbook. The capstone starts after
# this lab.
