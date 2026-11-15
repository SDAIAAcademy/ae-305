# %% [markdown]
# # Lab 2.4 · Cost per successful outcome
#
# Day 2 · Session 4 (Cost and capacity signals) · 25 min.
#
# The finance team asks Dhafer what each system cost in October and whether it was worth it. You price a month of
# Wahaj's logs (tokens, cached tokens, processor hours and outcomes), compute the cost per **successful** outcome,
# the cache hit rate and the utilisation of each system, show the cost back to the teams that use them, and write
# budget alerts that would have fired in time.
#
# **Reference state.** `data/reference/cost_month.csv` (one row per day, system and team), `data/prices.json`
# (assumed prices in Saudi riyals, to replace with your provider's price list) and `data/budgets.json`.
#
# **Tasks**
# - [ ] 1 · Price the month (6')
# - [ ] 2 · Cost per successful outcome by system (6')
# - [ ] 3 · Utilisation and cache hit rate (5')
# - [ ] 4 · Showback by team and a budget alert (8')
# - [ ] ✱ Stretch · Alert on the month-end forecast, not on the spend so far

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
import pandas as pd

OUT = K.lab_dir("D2_4")
logs = pd.read_csv(K.DATA / "reference" / "cost_month.csv")
P = K.prices()
BUDGETS = {k: v for k, v in K.read_json(K.DATA / "budgets.json").items() if k != "note"}
print(P["note"])
print(logs.head(4).to_string())
print("an outcome is: classifier = a flagged feeder confirmed by inspection; nabd = an answer the crew accepted;",
      "mubadir = a report resolved without a person redoing it")

# %% [markdown]
# ## 1 · Price the month (6')
#
# ✏️ **Exercise** · Add a column `cost_sar` to `logs`: fresh input tokens, cached input tokens and output tokens at
# their prices per million, plus processor hours used at the node-hour price.

# %%
try:
    # BEGIN SOLUTION
    fresh = logs.input_tokens - logs.cached_input_tokens
    logs["cost_sar"] = ((fresh * P["input_per_million_tokens"] + logs.cached_input_tokens * P["cached_input_per_million_tokens"]
                         + logs.output_tokens * P["output_per_million_tokens"]) / 1e6
                        + logs.cpu_node_hours_used * P["cpu_node_hour"])
    # END SOLUTION
except NotImplementedError:  # safety net
    fresh = logs.input_tokens - logs.cached_input_tokens
    logs["cost_sar"] = ((fresh * P["input_per_million_tokens"] + logs.cached_input_tokens * P["cached_input_per_million_tokens"]
                         + logs.output_tokens * P["output_per_million_tokens"]) / 1e6 + logs.cpu_node_hours_used * P["cpu_node_hour"])
print(logs.groupby("system").cost_sar.sum().round(2).to_string())

# %% [markdown]
# ## 2 · Cost per successful outcome by system (6')
#
# ✏️ **Exercise** · Build `by_system` with, per system: cost, requests, successes, cost per request and cost per
# successful outcome. Which one would you show the finance team, and why?

# %%
try:
    # BEGIN SOLUTION
    by_system = logs.groupby("system").agg(cost_sar=("cost_sar", "sum"), requests=("requests", "sum"),
                                           successes=("successes", "sum"), attempts=("attempts", "sum"))
    by_system["cost_per_request"] = by_system.cost_sar / by_system.requests
    by_system["success_rate"] = by_system.successes / by_system.attempts
    by_system["cost_per_success"] = by_system.cost_sar / by_system.successes
    # END SOLUTION
except NotImplementedError:  # safety net
    by_system = logs.groupby("system").agg(cost_sar=("cost_sar", "sum"), requests=("requests", "sum"),
                                           successes=("successes", "sum"), attempts=("attempts", "sum"))
    by_system["cost_per_request"] = by_system.cost_sar / by_system.requests
    by_system["success_rate"] = by_system.successes / by_system.attempts
    by_system["cost_per_success"] = by_system.cost_sar / by_system.successes
print(by_system.round(4).to_string())
by_system.round(4).to_csv(OUT / "cost_by_system.csv")

# %% [markdown]
# 🔍 Mubadir's cost per resolved report rises in the middle of the month while its requests do not. Find the days.

# %%
daily = logs[logs.system == "mubadir"].set_index("date")
daily_cps = (daily.cost_sar / daily.successes).round(4)
print(daily_cps.loc["2026-10-12":"2026-10-18"].to_string())

# %% [markdown]
# ## 3 · Utilisation and cache hit rate (5')
#
# ✏️ **Exercise** · Per system: utilisation (processor hours used over hours provisioned) and cache hit rate
# (cached input tokens over input tokens). For Nabd, compare the cache hit rate before and after 18 October.

# %%
try:
    # BEGIN SOLUTION
    use = logs.groupby("system")[["cpu_node_hours_used", "cpu_node_hours_provisioned", "cached_input_tokens", "input_tokens"]].sum()
    use["utilisation"] = use.cpu_node_hours_used / use.cpu_node_hours_provisioned
    use["cache_hit_rate"] = (use.cached_input_tokens / use.input_tokens).fillna(0)
    n = logs[logs.system == "nabd"]
    before, after = n[n.date < "2026-10-18"], n[n.date >= "2026-10-18"]
    nabd_cache = {"before_18th": before.cached_input_tokens.sum() / before.input_tokens.sum(),
                  "from_18th": after.cached_input_tokens.sum() / after.input_tokens.sum()}
    # END SOLUTION
except NotImplementedError:  # safety net
    use = logs.groupby("system")[["cpu_node_hours_used", "cpu_node_hours_provisioned", "cached_input_tokens", "input_tokens"]].sum()
    use["utilisation"] = use.cpu_node_hours_used / use.cpu_node_hours_provisioned
    use["cache_hit_rate"] = (use.cached_input_tokens / use.input_tokens).fillna(0)
    n = logs[logs.system == "nabd"]
    nabd_cache = {"before_18th": n[n.date < "2026-10-18"].cached_input_tokens.sum() / n[n.date < "2026-10-18"].input_tokens.sum(),
                  "from_18th": n[n.date >= "2026-10-18"].cached_input_tokens.sum() / n[n.date >= "2026-10-18"].input_tokens.sum()}
print(use[["utilisation", "cache_hit_rate"]].round(3).to_string())
print({k: round(v, 3) for k, v in nabd_cache.items()})
assert nabd_cache["from_18th"] < nabd_cache["before_18th"] / 2

# %% [markdown]
# 🔍 On 18 October someone added the date at the top of Nabd's system prompt. Why does a changing first line stop
# the provider's prompt cache from matching? (A cache matches a request's beginning: stable text first, changing
# text last.)

# %% [markdown]
# ## 4 · Showback by team and a budget alert (8')
#
# Showback tells each team what its use cost, without moving money; chargeback would bill it.
#
# ✏️ **Exercise** · Build `showback`, the cost per team and system. Then write `alerts(logs, budgets)`: for each
# system and day, alert when the spend so far this month is above the budget's share for the days passed by more
# than 20% (a burn-rate rule), starting on the seventh day so that one planned retraining day does not alert.
# Return the first alert day per system.

# %%
try:
    # BEGIN SOLUTION
    showback = logs.pivot_table(index="team", columns="system", values="cost_sar", aggfunc="sum", fill_value=0).round(2)
    showback["total"] = showback.sum(axis=1)

    def alerts(logs: pd.DataFrame, budgets: dict, days_in_month: int = 31, margin: float = 0.20, from_day: int = 7) -> dict:
        out = {}
        for system, g in logs.groupby("system"):
            d = g.groupby("date").cost_sar.sum().sort_index()
            spent = d.cumsum()
            for i, (date, s) in enumerate(spent.items(), 1):
                allowed = budgets[system] * i / days_in_month
                if i >= from_day and s > allowed * (1 + margin):
                    out[system] = {"date": date, "spent": round(s, 2), "allowed_so_far": round(allowed, 2)}
                    break
        return out
    # END SOLUTION
except NotImplementedError:  # safety net
    showback = logs.pivot_table(index="team", columns="system", values="cost_sar", aggfunc="sum", fill_value=0).round(2)
    showback["total"] = showback.sum(axis=1)

    def alerts(logs, budgets, days_in_month=31, margin=0.20, from_day=7):
        out = {}
        for system, g in logs.groupby("system"):
            spent = g.groupby("date").cost_sar.sum().sort_index().cumsum()
            for i, (date, s) in enumerate(spent.items(), 1):
                if i >= from_day and s > budgets[system] * i / days_in_month * (1 + margin):
                    out[system] = {"date": date, "spent": round(s, 2), "allowed_so_far": round(budgets[system] * i / days_in_month, 2)}
                    break
        return out
print(showback.to_string())
fired = alerts(logs, BUDGETS)
print(fired)
showback.to_csv(OUT / "showback.csv")
K.write_json(OUT / "alert_rules.json", {"rule": "from day 7, month-to-date spend above the budget's daily share by more than 20%",
                                        "budgets_sar": BUDGETS, "fired": fired})
K.save_reference("D2_4_alerts", fired)
assert set(fired) == {"mubadir"} and "2026-10-14" <= fired["mubadir"]["date"] <= "2026-10-16", fired
K.check(True, f"Mubadir's budget alert fires on {fired['mubadir']['date']}, during the runaway days")

# %% [markdown]
# ## ✱ Stretch · Alert on the forecast
#
# A burn-rate rule waits until the money is spent. Project each system's month-end spend from the last seven days'
# average and alert when the projection is above the budget. On which day would Mubadir's alert have fired?

# %%
try:
    # BEGIN SOLUTION
    for system, g in logs.groupby("system"):
        d = g.groupby("date").cost_sar.sum().sort_index()
        for i in range(7, len(d) + 1):
            projected = d.iloc[:i].sum() + d.iloc[i - 7:i].mean() * (31 - i)
            if projected > BUDGETS[system]:
                print(system, "forecast alert on", d.index[i - 1], f"(projected {projected:.2f} SAR of {BUDGETS[system]})")
                break
        else:
            print(system, "no forecast alert")
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. A cheaper model halves the cost per request and doubles the retries. What happens to the cost per successful
#    outcome?
#    <details><summary>Answer</summary>It can rise: failed attempts are paid for too. Compare designs on cost per
#    success, not per call.</details>
# 2. The classifier's utilisation is low. Is it waste?
#    <details><summary>Answer</summary>Mostly: its provisioned nodes wait for one daily batch and a monthly
#    retrain. Scale to zero between runs, or share the nodes.</details>
# 3. Why show the cost back to teams rather than keep one platform bill?
#    <details><summary>Answer</summary>The teams decide how much they use; seeing their own cost per outcome is what
#    changes their choices.</details>
#
# ## Carry forward
#
# `artifacts/D2_4/cost_by_system.csv`, `showback.csv` and `alert_rules.json` are the cost table and alert rules of
# the capstone's runbook. Day 4 finds the cause of Mubadir's expensive days: a runaway loop.
