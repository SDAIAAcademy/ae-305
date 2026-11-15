# %% [markdown]
# # Lab 2.3 · A canary that rolls itself back
#
# Day 2 · Session 3 (Shadow and canary on evidence) · 25 min.
#
# The provider's new snapshot `steady-2026-10-14` (the unrecorded change of Lab 1.1) passed Nabd's offline gate.
# Wahaj pinned the old snapshot and now releases the new one through a canary. You replay four hours of crew
# traffic: first in shadow, then through canary stages that advance only when an analysis passes. You write the
# analysis and its triggers, and watch it roll the canary back.
#
# **Reference state.** `data/replay/canary_traffic.jsonl`: 4,800 recorded requests, each with the stable
# version's and the candidate's latency and grade (the calibrated grader's verdict), so any share of traffic can
# be replayed through either version. `K.run_rollout` follows the step semantics of Argo Rollouts.
#
# **Tasks**
# - [ ] 1 · Shadow first (5')
# - [ ] 2 · Analyse one canary window (8')
# - [ ] 3 · Stages and triggers (7')
# - [ ] 4 · Read where and why it rolled back (5')
# - [ ] ✱ Stretch · Write the same analysis as an Argo Rollouts AnalysisTemplate

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

OUT = K.lab_dir("D2_3")
traffic = K.read_jsonl(K.DATA / "replay" / "canary_traffic.jsonl")
print(len(traffic), "requests over", round(traffic[-1]["t_min"]), "minutes")
print(traffic[0])
SLO_P95_MS = 2500        # Nabd's latency objective: 95% of answers within 2.5 seconds
MAX_QUALITY_DROP = 0.05  # the canary may not grade more than 5 points below stable on the same requests
MIN_SAMPLE = 50          # fewer requests than this is not evidence either way

# %% [markdown]
# ## 1 · Shadow first (5')
#
# In shadow mode the candidate receives a copy of every request and its answers are graded, but users only ever
# see the stable version's answer. It costs double tokens and risks nobody.
#
# ✏️ **Exercise** · Compare stable and candidate on the first 30 minutes: p95 latency (`K.p95`) and the share of
# answers graded ok. Save the numbers in `shadow`.

# %%
window = [r for r in traffic if r["t_min"] < 30]
try:
    # BEGIN SOLUTION
    shadow = {v: {"p95_ms": K.p95([r[v]["latency_ms"] for r in window]),
                  "ok": round(sum(r[v]["grade_ok"] for r in window) / len(window), 3)} for v in ("stable", "canary")}
    shadow["arabic_share"] = round(sum(r["lang"] == "ar" for r in window) / len(window), 3)
    # END SOLUTION
except NotImplementedError:  # safety net
    shadow = K.reference("D2_3_shadow")
K.save_reference("D2_3_shadow", shadow)
print(len(window), "requests in shadow:", shadow)

# %% [markdown]
# 🔍 The shadow looks good: the candidate is no slower and grades a little better. Note the share of Arabic
# requests in that half hour.

# %% [markdown]
# ## 2 · Analyse one canary window (8')
#
# At the end of each pause the controller hands the analysis the requests the canary served in that pause, each
# with the stable version's outcome on the same request (`r["stable"]`), so quality is compared pair by pair.
#
# ✏️ **Exercise** · Write `analyse(window)` returning `(verdict, why)`:
# `"inconclusive"` below `MIN_SAMPLE` requests; `"fail"` when the canary's p95 latency is above `SLO_P95_MS` or
# its ok-share is more than `MAX_QUALITY_DROP` below stable's on the same requests; otherwise `"pass"`. Put the
# numbers in `why`: they are what the release log will say.

# %%
def analyse(window: list[dict]) -> tuple[str, str]:
    # BEGIN SOLUTION
    n = len(window)
    if n < MIN_SAMPLE:
        return "inconclusive", f"{n} requests, fewer than {MIN_SAMPLE}"
    p95 = K.p95([r["latency_ms"] for r in window])
    ok = sum(r["grade_ok"] for r in window) / n
    ok_stable = sum(r["stable"]["grade_ok"] for r in window) / n
    arabic = sum(r["lang"] == "ar" for r in window) / n
    why = f"n={n}, p95 {p95:.0f} ms, ok {ok:.3f} against stable {ok_stable:.3f}, Arabic {arabic:.0%}"
    if p95 > SLO_P95_MS:
        return "fail", f"latency trigger: {why}"
    if ok < ok_stable - MAX_QUALITY_DROP:
        return "fail", f"quality trigger: {why}"
    return "pass", why
    # END SOLUTION


# %%
probe = [dict(r["canary"], i=r["i"], lang=r["lang"], stable=r["stable"]) for r in traffic[:40]]
try:
    print(analyse(probe))
except NotImplementedError:  # safety net: the reference analysis
    def analyse(window):
        n = len(window)
        if n < MIN_SAMPLE:
            return "inconclusive", f"{n} requests"
        p95 = K.p95([r["latency_ms"] for r in window])
        ok = sum(r["grade_ok"] for r in window) / n
        ok_s = sum(r["stable"]["grade_ok"] for r in window) / n
        why = f"n={n}, p95 {p95:.0f} ms, ok {ok:.3f} against stable {ok_s:.3f}"
        if p95 > SLO_P95_MS:
            return "fail", "latency trigger: " + why
        if ok < ok_s - MAX_QUALITY_DROP:
            return "fail", "quality trigger: " + why
        return "pass", why
    print(analyse(probe))
assert analyse(probe)[0] == "inconclusive"

# %% [markdown]
# ## 3 · Stages and triggers (7')
#
# ✏️ **Exercise** · Write `STEPS` in the Argo Rollouts style: 5% of traffic for 60 minutes, then 25% for 30, then
# 50% for 30, then 100%. Run the rollout with your analysis.

# %%
try:
    # BEGIN SOLUTION
    STEPS = [{"setWeight": 5}, {"pause": 60}, {"setWeight": 25}, {"pause": 30},
             {"setWeight": 50}, {"pause": 30}, {"setWeight": 100}]
    # END SOLUTION
except NotImplementedError:  # safety net
    STEPS = [{"setWeight": 5}, {"pause": 60}, {"setWeight": 25}, {"pause": 30}, {"setWeight": 50}, {"pause": 30}, {"setWeight": 100}]
log = K.run_rollout(traffic, STEPS, analyse)
for e in log:
    print(e)

# %% [markdown]
# ## 4 · Read where and why it rolled back (5')
#
# ✏️ **Exercise** · Find the abort event, then add one line to the release log (`artifacts/D2_3/release_log.jsonl`)
# with the release, the decision `rolled back`, the stage, the stated metric and the numbers.

# %%
abort = next((e for e in log if e["event"].startswith("abort")), None)
try:
    # BEGIN SOLUTION
    stage = [e for e in log if e["event"].startswith("analysis")][-1]
    entry = {"release": "nabd-2026.11.4", "change": "model snapshot steady-2026-09-12 to steady-2026-10-14",
             "decision": "rolled back", "stage": stage["event"], "metric": abort["why"].split(":")[0],
             "evidence": abort["why"], "at_minute": abort["t_min"]}
    # END SOLUTION
except NotImplementedError:  # safety net
    entry = {"release": "nabd-2026.11.4", "decision": "rolled back", "evidence": abort["why"] if abort else None}
with (OUT / "release_log.jsonl").open("w", encoding="utf-8") as f:
    f.write(json.dumps(entry) + "\n")
print(json.dumps(entry, indent=1))
assert abort is not None and "25" in [e for e in log if e["event"].startswith("analysis")][-1]["event"]
K.check(True, "the canary rolled back at 25% on a stated trigger")

# %% [markdown]
# 🔍 The 5% stage passed and the shadow looked better than stable. What changed at minute 70, and why did neither
# the offline gate nor the shadow see it? (Compare the Arabic share in the passing and the failing windows.)

# %% [markdown]
# ## ✱ Stretch · The same analysis for Argo Rollouts
#
# On a cluster, the analysis is an `AnalysisTemplate` that queries a metrics backend (Prometheus) and the canary
# steps live in the `Rollout`. Write the template for the latency trigger into `artifacts/D2_3/analysis.yaml` and
# compare it with `labs/cluster/analysis-template.yaml`.

# %%
try:
    # BEGIN SOLUTION
    TEMPLATE = """apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: nabd-latency
spec:
  metrics:
    - name: p95-latency
      interval: 5m
      failureLimit: 0
      successCondition: result[0] <= 2.5
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            histogram_quantile(0.95, sum(rate(nabd_answer_seconds_bucket{track="canary"}[5m])) by (le))
"""
    (OUT / "analysis.yaml").write_text(TEMPLATE, encoding="utf-8")
    print((K.LABS / "cluster" / "analysis-template.yaml").read_text(encoding="utf-8")[:400])
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. The 5% stage served 70 requests and passed. Would 30 requests have been enough?
#    <details><summary>Answer</summary>No: below the minimum sample the analysis says inconclusive and the
#    rollout waits. A quiet window is not evidence.</details>
# 2. Why compare quality with the stable version's outcome on the same requests, not with last week's average?
#    <details><summary>Answer</summary>The mix of questions changes through the day; a paired comparison removes
#    the mix and leaves the version.</details>
# 3. The shadow looked better than stable. What would a longer or wider shadow have needed to catch the problem?
#    <details><summary>Answer</summary>Traffic like the later shift's: Arabic questions. Shadow and canary are only
#    as good as the traffic they see.</details>
#
# ## Carry forward
#
# The release log now holds two shipped releases (Lab 2.2) and one rolled back on a stated metric: the evidence
# LO3 asks for, in the shape the capstone uses.
