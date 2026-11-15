# %% [markdown]
# # Lab 3.3 · Online evaluation and a review queue
#
# Day 3 · Session 3 (Online evaluation and review queues) · 25 min.
#
# The offline gate (Lab 2.2) checks 24 fixed cases before a release. After it, Nabd answers hundreds of real
# questions a day. You take one week of recorded traces, redact them before they are stored, grade a sample with
# the platform team's groundedness grader, correct the failure rate for the grader's known errors, and send what
# needs a person to a review queue for Saqer's reviewers.
#
# **Reference state.** `data/reference/live_traces.jsonl`: 400 traces from one week (question, retrieved manual,
# context, answer). Some questions contain a customer's name, phone number, account number or national ID. The
# first 150 traces were labelled by reviewers (`live_traces_labels.jsonl`): that is the calibration set. The grader
# is `graders.groundedness`, built and calibrated the AE-303 way.
#
# **Tasks**
# - [ ] 1 · Redact before storage (6')
# - [ ] 2 · Sample the week (4')
# - [ ] 3 · Grade with the calibrated grader (6')
# - [ ] 4 · Route to review and correct the rate (9')
# - [ ] ✱ Stretch · A retention rule that deletes traces past their limit

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
import random
import re

import pandas as pd

import graders as G

OUT = K.lab_dir("D3_3")
raw = K.read_jsonl(K.DATA / "reference" / "live_traces.jsonl")
labels = {r["trace_id"]: r["human_ok"] for r in K.read_jsonl(K.DATA / "reference" / "live_traces_labels.jsonl")}
CALIBRATION = raw[:150]           # labelled by reviewers
WEEK = raw[150:]                  # the traces to evaluate
print(len(raw), "traces;", len(CALIBRATION), "labelled for calibration;", len(WEEK), "to evaluate")
print(next(t for t in raw if "called from" in t["question"])["question"])

# %% [markdown]
# ## 1 · Redact before storage (6')
#
# Traces are stored for weeks and read by people outside field operations. Personal data that the evaluation does
# not need is not stored (PDPL: collect only what the purpose needs; the Data Management and Personal Data
# Protection Standards set the controls).
#
# ✏️ **Exercise** · Write `redact(text)` replacing a customer's name after "The customer", Saudi mobile numbers
# (`05` and eight digits), account numbers (`ACC-` and eight digits) and national IDs (ten digits starting with 1
# or 2) with `[name]`, `[phone]`, `[account]`, `[national-id]`. Then build `traces`: every trace with its question
# redacted.

# %%
def redact(text: str) -> str:
    # BEGIN SOLUTION
    text = re.sub(r"(The customer) [A-Z][\w'-]+(?: [A-Z][\w'-]+)+", r"\1 [name]", text)
    text = re.sub(r"\b05\d{8}\b", "[phone]", text)
    text = re.sub(r"\bACC-\d{8}\b", "[account]", text)
    return re.sub(r"\b[12]\d{9}\b", "[national-id]", text)
    # END SOLUTION


def reference_redact(text):
    text = re.sub(r"(The customer) [A-Z][\w'-]+(?: [A-Z][\w'-]+)+", r"\1 [name]", text)
    for rx, label in ((r"\b05\d{8}\b", "[phone]"), (r"\bACC-\d{8}\b", "[account]"), (r"\b[12]\d{9}\b", "[national-id]")):
        text = re.sub(rx, label, text)
    return text


try:
    redact("probe")
except NotImplementedError:  # safety net
    redact = reference_redact
traces = [dict(t, question=redact(t["question"])) for t in raw]
changed = sum(a["question"] != b["question"] for a, b in zip(raw, traces))
leaks = [t["trace_id"] for t in traces if re.search(r"05\d{8}|ACC-\d{8}|\b[12]\d{9}\b|customer [A-Z][a-z]", t["question"])]
print(changed, "questions redacted; leaks left:", leaks)
print(next(t for t in traces if "[phone]" in t["question"])["question"])
assert not leaks
with (OUT / "traces_redacted.jsonl").open("w", encoding="utf-8") as f:
    for t in traces:
        f.write(json.dumps(t, ensure_ascii=False) + "\n")

# %% [markdown]
# ## 2 · Sample the week (4')
#
# Grading every trace is cheap with a code grader but not with a model as judge, and reviewers' time is the scarce
# part. Take a fixed-size random sample, with a seed so the sample can be reproduced.
#
# ✏️ **Exercise** · `sample`: 100 traces of `WEEK` (redacted), drawn with `random.Random(305)`.

# %%
week = [t for t in traces if t["trace_id"] not in {c["trace_id"] for c in CALIBRATION}]
try:
    # BEGIN SOLUTION
    sample = random.Random(305).sample(week, 100)
    # END SOLUTION
except NotImplementedError:  # safety net
    sample = random.Random(305).sample(week, 100)
print(len(sample), "sampled; days:", pd.Series([t["day"] for t in sample]).value_counts().sort_index().to_dict())

# %% [markdown]
# ## 3 · Grade with the calibrated grader (6')
#
# ✏️ **Exercise** · Write `grade(trace)` returning the grader's label (`"pass"` or `"fail"`), calling
# `G.groundedness(answer, context, cited=G.citations(answer), retrieved=trace["retrieved"])`. Then compute the raw
# failure rate of the sample with its 95% interval (`K.wilson`).

# %%
def grade(trace: dict) -> str:
    # BEGIN SOLUTION
    return G.groundedness(trace["answer"], trace["context"], cited=G.citations(trace["answer"]), retrieved=trace["retrieved"])["label"]
    # END SOLUTION


try:
    grade(sample[0])
except NotImplementedError:  # safety net
    def grade(trace):
        return G.groundedness(trace["answer"], trace["context"], G.citations(trace["answer"]), trace["retrieved"])["label"]
graded = [dict(t, grade=grade(t)) for t in sample]
fails = sum(t["grade"] == "fail" for t in graded)
raw_rate = fails / len(graded)
print(f"raw failure rate {raw_rate:.2f}, 95% interval {K.wilson(fails, len(graded))}")

# %% [markdown]
# 🔍 Read three failing answers. Are they all bad? (One kind of good answer ends with a polite sentence the grader
# cannot find in the manual.)

# %% [markdown]
# ## 4 · Route to review and correct the rate (9')
#
# A grader makes errors in both directions. On the calibration set, measure its **sensitivity** (the share of bad
# answers it fails) and **specificity** (the share of good answers it passes). The Rogan-Gladen estimator then
# corrects the raw rate: true rate = (raw + specificity − 1) / (sensitivity + specificity − 1).
#
# ✏️ **Exercise** · Compute `se`, `sp` and `corrected` (clipped to 0..1). Build the review queue: every failing
# trace, plus one passing trace in ten drawn at random (so the reviewers also see what the grader lets through).
# Write it to `artifacts/D3_3/review_queue.csv` with the trace id, day, reason, question and answer.

# %%
try:
    # BEGIN SOLUTION
    cal = [dict(t, grade=grade(t), human_ok=labels[t["trace_id"]]) for t in traces[:150]]
    bad = [c for c in cal if not c["human_ok"]]
    good = [c for c in cal if c["human_ok"]]
    se = sum(c["grade"] == "fail" for c in bad) / len(bad)
    sp = sum(c["grade"] == "pass" for c in good) / len(good)
    corrected = min(1.0, max(0.0, (raw_rate + sp - 1) / (se + sp - 1)))
    rng = random.Random(305)
    queue = [dict(t, reason="grader failed") for t in graded if t["grade"] == "fail"]
    queue += [dict(t, reason="random check of a pass") for t in graded if t["grade"] == "pass" and rng.random() < 0.1]
    # END SOLUTION
except NotImplementedError:  # safety net
    cal = [dict(t, grade=grade(t), human_ok=labels[t["trace_id"]]) for t in traces[:150]]
    se = sum(c["grade"] == "fail" for c in cal if not c["human_ok"]) / sum(not c["human_ok"] for c in cal)
    sp = sum(c["grade"] == "pass" for c in cal if c["human_ok"]) / sum(c["human_ok"] for c in cal)
    corrected = min(1.0, max(0.0, (raw_rate + sp - 1) / (se + sp - 1)))
    rng = random.Random(305)
    queue = [dict(t, reason="grader failed") for t in graded if t["grade"] == "fail"]
    queue += [dict(t, reason="random check of a pass") for t in graded if t["grade"] == "pass" and rng.random() < 0.1]
pd.DataFrame(queue)[["trace_id", "day", "reason", "question", "answer"]].to_csv(OUT / "review_queue.csv", index=False)
truth = sum(not labels[t["trace_id"]] for t in sample) / len(sample)  # known here only because the data is invented
summary = {"sampled": len(sample), "raw_failure_rate": raw_rate, "sensitivity": round(se, 3), "specificity": round(sp, 3),
           "corrected_failure_rate": round(corrected, 3), "review_queue": len(queue),
           "true_rate_in_sample": truth}
K.write_json(OUT / "online_eval.json", summary)
print(json.dumps(summary, indent=1))
assert abs(corrected - truth) < abs(raw_rate - truth)
K.check(True, f"raw {raw_rate:.2f} -> corrected {corrected:.2f}; reviewers get {len(queue)} traces")

# %% [markdown]
# 🔍 The corrected rate is an estimate from 100 traces and a calibration set of 150: its error is several points.
# What would you report to Saqer: the raw rate, the corrected rate, or both with the interval?

# %% [markdown]
# ## ✱ Stretch · Retention
#
# Wahaj's rule for traces: keep redacted traces for 3 days for debugging, longer only while they wait in the
# review queue (PDPL Article 18: destroy personal data once it is no longer needed for the purpose; the redaction
# already removed it, and the rule keeps the store small as well).
#
# Write `to_delete(traces, today, keep_days, held)` returning the trace ids older than `keep_days` that are not in
# `held`. Run it for day 7.

# %%
try:
    # BEGIN SOLUTION
    def to_delete(traces, today: int, keep_days: int, held: set) -> list[str]:
        return [t["trace_id"] for t in traces if today - t["day"] >= keep_days and t["trace_id"] not in held]

    held = {t["trace_id"] for t in queue}
    gone = to_delete(traces, today=7, keep_days=3, held=held)
    print(len(gone), "traces deleted on day 7;", len(traces) - len(gone), "kept,", len(held), "of them held for review")
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. The grader fails 29% of the sample. Why is that not Nabd's failure rate?
#    <details><summary>Answer</summary>The grader is wrong sometimes in both directions; with its sensitivity and
#    specificity measured on labelled traces, the rate can be corrected.</details>
# 2. Why send a few passing traces to review?
#    <details><summary>Answer</summary>To catch what the grader lets through (a wrong number with the right words)
#    and to keep measuring its sensitivity as Nabd changes.</details>
# 3. Why redact before storage and not before display?
#    <details><summary>Answer</summary>Anything stored can be copied, exported and read later; data that is never
#    stored does not need a retention rule or an access control.</details>
#
# ## Carry forward
#
# `artifacts/D3_3/online_eval.json` and the review queue go into the capstone's runbook as the online evaluation
# of Nabd.
