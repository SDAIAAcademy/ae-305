# %% [markdown]
# # Lab 3.2 · Two shifts in a replayed month
#
# Day 3 · Session 2 (Drift, skew and delayed labels) · 25 min.
#
# The fault-risk classifier scores feeders every day, but whether a feeder faulted is known only 30 days later, and
# later still for mountain feeders. Until then, Lamya can only watch the **inputs**. You replay October's serving
# inputs (two shifts are planted, and so are a heat spike, two quiet days and the seasonal cooling), alert the
# naive way and count the false alarms, then tune the monitor until it alerts on the two shifts and nothing else.
#
# **Reference state.** `data/reference/replay_month.csv`: 30 days of serving inputs (date, feeder, region, peak
# temperature, dust index, peak load), 400 feeders a day, 120 on the two maintenance-freeze days.
#
# **Tasks**
# - [ ] 1 · Drift per feature per day (7')
# - [ ] 2 · Naive alerts and their false alarms (5')
# - [ ] 3 · Tune threshold and persistence (8')
# - [ ] 4 · The note: shifts found, alarms removed (5')
# - [ ] ✱ Stretch · Measure skew between the training snapshot and serving for one feature

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
import numpy as np
import pandas as pd

OUT = K.lab_dir("D3_2")
serving = pd.read_csv(K.DATA / "reference" / "replay_month.csv")
serving["day"] = serving["date"].str[-2:].astype(int)
FEATURES = ["peak_temp_c", "dust_index", "load_peak_pct"]
print(serving.groupby("day").size().to_dict())
print(serving.groupby("day")[FEATURES].mean().round(2).iloc[[0, 6, 7, 11, 20, 29]].to_string())

# %% [markdown]
# ## 1 · Drift per feature per day (7')
#
# The **population stability index** compares a day's distribution of one feature with a reference distribution,
# bin by bin: PSI = Σ (current share − reference share) × ln(current share / reference share), with bins cut at the
# reference's deciles. Common rules of thumb: below 0.1 stable, 0.1 to 0.25 a moderate move, above 0.25 a large one.
#
# ✏️ **Exercise** · Write `psi(reference, current, bins=10)`, then build `fixed`: one row per day from day 8, one
# column per feature, with the first week (days 1 to 7) as the reference.

# %%
def psi(reference, current, bins: int = 10) -> float:
    # BEGIN SOLUTION
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    ref = np.histogram(reference, edges)[0] / len(reference)
    cur = np.histogram(current, edges)[0] / len(current)
    ref, cur = np.clip(ref, 1e-4, None), np.clip(cur, 1e-4, None)  # an empty bin would make the log infinite
    return float(np.sum((cur - ref) * np.log(cur / ref)))
    # END SOLUTION


def reference_psi(reference, current, bins=10):
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    r = np.clip(np.histogram(reference, edges)[0] / len(reference), 1e-4, None)
    c = np.clip(np.histogram(current, edges)[0] / len(current), 1e-4, None)
    return float(np.sum((c - r) * np.log(c / r)))


try:
    psi(np.arange(10.0), np.arange(10.0))
except NotImplementedError:  # safety net
    psi = reference_psi

first_week = serving[serving.day <= 7]
fixed = pd.DataFrame([{"day": d, "n": len(g), **{f: round(psi(first_week[f], g[f]), 3) for f in FEATURES}}
                      for d, g in serving[serving.day >= 8].groupby("day")]).set_index("day")
print(fixed.to_string())

# %% [markdown]
# ## 2 · Naive alerts and their false alarms (5')
#
# The first monitor anyone writes: alert on any day when any feature's PSI is above 0.1.
#
# ✏️ **Exercise** · Count `naive`, the (day, feature) pairs that alert. Then look at the days: which alerts are
# the heat spike on day 8, the quiet day 17 (120 feeders), and the seasonal cooling of October, and which are real shifts?

# %%
try:
    # BEGIN SOLUTION
    naive = [(d, f) for d, row in fixed.iterrows() for f in FEATURES if row[f] > 0.1]
    # END SOLUTION
except NotImplementedError:  # safety net
    naive = [(d, f) for d, row in fixed.iterrows() for f in FEATURES if row[f] > 0.1]
print(len(naive), "alerts in 23 days:")
print(pd.Series([f for _, f in naive]).value_counts().to_string())

# %% [markdown]
# 🔍 Temperature alerts on most days after the second week: October cools by about three degrees, as it does every
# year, and the model was trained on a full year that includes it. A fixed first-week reference turns the season
# into an alarm.

# %% [markdown]
# ## 3 · Tune threshold and persistence (8')
#
# Three changes, each aimed at one kind of false alarm:
#
# - **a rolling reference**: the previous seven days instead of the first week, so a slow seasonal move is
#   absorbed while a step is not;
# - **a minimum sample**: a day with fewer than 200 feeders is not judged;
# - **persistence**: alert only when the same feature is above 0.2 on three judged days in a row.
#
# ✏️ **Exercise** · Write `monitor(serving, threshold=0.2, persist=3, min_n=200, window=7)` returning a list of
# alerts `{"feature", "day" (the day it fires), "since" (the first day of the run), "psi"}`, one per run.

# %%
def monitor(serving: pd.DataFrame, threshold: float = 0.2, persist: int = 3, min_n: int = 200, window: int = 7) -> list[dict]:
    # BEGIN SOLUTION
    alerts = []
    for f in FEATURES:
        run = []
        for d in range(window + 1, serving.day.max() + 1):
            today = serving[serving.day == d]
            if len(today) < min_n:
                continue  # not judged: neither extends nor breaks a run
            ref = serving[(serving.day >= d - window) & (serving.day < d)]
            value = psi(ref[f], today[f])
            if value > threshold:
                run.append((d, value))
                if len(run) == persist:
                    alerts.append({"feature": f, "day": d, "since": run[0][0], "psi": round(max(v for _, v in run), 3)})
            else:
                run = []
    return sorted(alerts, key=lambda a: a["day"])
    # END SOLUTION


def reference_monitor(serving, threshold=0.2, persist=3, min_n=200, window=7):
    alerts = []
    for f in FEATURES:
        run = []
        for d in range(window + 1, serving.day.max() + 1):
            today = serving[serving.day == d]
            if len(today) < min_n:
                continue
            ref = serving[(serving.day >= d - window) & (serving.day < d)]
            v = psi(ref[f], today[f])
            if v > threshold:
                run.append((d, v))
                if len(run) == persist:
                    alerts.append({"feature": f, "day": d, "since": run[0][0], "psi": round(max(x for _, x in run), 3)})
            else:
                run = []
    return sorted(alerts, key=lambda a: a["day"])


try:
    tuned = monitor(serving)
except NotImplementedError:  # safety net
    tuned = reference_monitor(serving)
for a in tuned:
    print(a)
assert [(a["feature"], a["since"]) for a in tuned] == [("load_peak_pct", 12), ("dust_index", 22)], tuned
K.check(True, f"{len(naive)} naive alerts -> {len(tuned)} alerts, one per planted shift")

# %% [markdown]
# 🔍 Try `persist=1`, then `threshold=0.1`. Which false alarm comes back first?

# %% [markdown]
# ## 4 · The note: shifts found, alarms removed (5')
#
# ✏️ **Exercise** · Write `artifacts/D3_2/monitor_note.md` for Lamya: the two shifts (feature, first day, size),
# what each could mean, the false alarms removed and by which rule, and what the rolling reference can no longer
# see (a slow drift that is not seasonal).

# %%
try:
    # BEGIN SOLUTION
    lines = ["# Input monitor for the fault-risk classifier, October 2026", "",
             f"Naive rule (PSI > 0.1 on any day against the first week): {len(naive)} alerts in 23 days.",
             "Tuned rule: PSI > 0.2 against the previous seven days, on three judged days in a row; days with",
             "fewer than 200 feeders are not judged.", "", "## Shifts found"]
    for a in tuned:
        lines.append(f"- {a['feature']}: from day {a['since']}, alert on day {a['day']}, PSI up to {a['psi']}")
    lines += ["", "Load stepped up overnight on day 12 while temperatures fell: a measurement change (skew), not",
              "a change in the grid. Dust rises steadily from day 21: a real change in the world, which the",
              "model has seen in spring.", "", "## Alarms removed",
              "- the heat spike of day 8: one day, removed by persistence",
              "- the maintenance-freeze day 17: 120 feeders, removed by the minimum sample",
              "- October's cooling: absorbed by the rolling reference", "", "## What this monitor cannot see",
              "A slow drift is absorbed by a rolling reference. Keep a monthly comparison with the training",
              "snapshot as well."]
    note = "\n".join(lines) + "\n"
    # END SOLUTION
except NotImplementedError:  # safety net
    note = "# Input monitor\n\n" + "\n".join(f"- {a['feature']} from day {a['since']}" for a in tuned) + "\n"
(OUT / "monitor_note.md").write_text(note, encoding="utf-8")
K.write_json(OUT / "alerts.json", tuned)
print(note)

# %% [markdown]
# ## ✱ Stretch · Skew against the training snapshot
#
# Drift is the world changing; **skew** is serving computing a feature differently from training. Join each
# serving row to the same feeder's row in the October training batch (`data/batches/feeders_2026-10.csv`) and
# print the median ratio of serving load to batch load per day. On which day does it step, and by how much?

# %%
try:
    # BEGIN SOLUTION
    batch = pd.read_csv(K.DATA / "batches" / "feeders_2026-10.csv")[["feeder_id", "load_peak_pct"]]
    joined = serving.merge(batch, on="feeder_id", suffixes=("", "_batch"))
    ratio = (joined.load_peak_pct / joined.load_peak_pct_batch).groupby(joined.day).median()
    print(ratio.loc[8:16].round(3).to_string())
    print(f"step on day 12: {ratio.loc[12:14].mean() / ratio.loc[9:11].mean() - 1:+.1%}")
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. A feature's PSI is 0.6 on one day, then back to normal. Alert?
#    <details><summary>Answer</summary>Not with persistence: one day is usually weather or a data delay. Log it, and
#    alert if it repeats.</details>
# 2. Load rose 12% overnight while temperatures fell. Drift or skew, and who do you call?
#    <details><summary>Answer</summary>Probably skew: the meters were recalibrated. Call the SCADA team before
#    retraining on it; retraining would teach the model the error.</details>
# 3. Why can input monitors not replace accuracy monitoring?
#    <details><summary>Answer</summary>Inputs can move without hurting the model and the model can fail with stable
#    inputs; once labels arrive (30 days, longer in Al-Jabal), measure the model itself.</details>
#
# ## Carry forward
#
# `artifacts/D3_2/alerts.json` is the drift signal Lab 3.4's retraining trigger reads.
