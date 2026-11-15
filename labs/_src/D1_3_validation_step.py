# %% [markdown]
# # Lab 1.3 · A validation step that stops training
#
# Day 1 · Session 3 (Pipelines with validation) · 25 min.
#
# Every month the SCADA export team delivers a feeder batch, and the pipeline retrains the fault-risk model on it.
# You write the batch's data contract as a pandera schema, add the checks a schema cannot express on one row, and
# put validation in the pipeline as the step before training. Then you run the pipeline on three monthly batches:
# two train, the September batch stops with a report.
#
# **Reference state.** `data/batches/feeders_2026-07.csv`, `_2026-08.csv`, `_2026-09.csv`, and the pipeline runner
# `K.run_flow` (a small stand-in for an orchestrator such as Prefect or Airflow).
#
# **Tasks**
# - [ ] 1 · The contract as a schema (8')
# - [ ] 2 · Batch checks: row count and duplicates (5')
# - [ ] 3 · The step that stops the run (7')
# - [ ] 4 · Run the pipeline on three batches (5')
# - [ ] ✱ Stretch · Quarantine the failing rows and write the report for the data owner

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
import pandera.pandas as pa

OUT = K.lab_dir("D1_3")
july = K.load_batch("2026-07")
print(july.shape)
print(july.head(3).to_string())

# %% [markdown]
# ## 1 · The contract as a schema (8')
#
# The contract says what every row must be: the types, the allowed values and the physical ranges. Agree it with
# the data owner once, then check it on every batch, before any training.
#
# ✏️ **Exercise** · Write `SCHEMA`, a `pa.DataFrameSchema` with one `pa.Column` per column of the batch:
# `month` and `feeder_id` as strings matching `^\d{4}-\d{2}$` and `^F-\d{4}$`; `region` one of the six codes;
# `age_years` 0 to 60; `length_km` 0.5 to 100; `overhead_share`, `vegetation` and `dust_index` 0 to 1;
# `coast_km` 0 to 400; `peak_temp_c` 0 to 60; `load_peak_pct` 20 to 150 (a percentage of the feeder's rating);
# `faults_90d` 0 to 10; `fault_30d` 0 or 1. No column may be null.

# %%
import contracts

try:
    # BEGIN SOLUTION
    SCHEMA = pa.DataFrameSchema({
        "month": pa.Column(str, pa.Check.str_matches(r"^\d{4}-\d{2}$")),
        "feeder_id": pa.Column(str, pa.Check.str_matches(r"^F-\d{4}$")),
        "region": pa.Column(str, pa.Check.isin(list(K.REGIONS))),
        "age_years": pa.Column(int, pa.Check.in_range(0, 60)),
        "length_km": pa.Column(float, pa.Check.in_range(0.5, 100)),
        "overhead_share": pa.Column(float, pa.Check.in_range(0, 1)),
        "vegetation": pa.Column(float, pa.Check.in_range(0, 1)),
        "coast_km": pa.Column(float, pa.Check.in_range(0, 400)),
        "peak_temp_c": pa.Column(float, pa.Check.in_range(0, 60)),
        "dust_index": pa.Column(float, pa.Check.in_range(0, 1)),
        "load_peak_pct": pa.Column(float, pa.Check.in_range(20, 150)),
        "faults_90d": pa.Column(int, pa.Check.in_range(0, 10)),
        "fault_30d": pa.Column(int, pa.Check.isin([0, 1])),
    }, strict=True)
    # END SOLUTION
except NotImplementedError:  # safety net: the reference contract
    SCHEMA = contracts.SCHEMA

# %%
try:
    SCHEMA.validate(july, lazy=True)
    schema_ok = True
except pa.errors.SchemaErrors as e:
    schema_ok = False
    print(e.failure_cases.head())
K.check(schema_ok, "the July batch meets the contract")

# %% [markdown]
# ## 2 · Batch checks: row count and duplicates (5')
#
# Some rules are about the batch, not a row: one row per feeder, every feeder present, the month the file says.
#
# ✏️ **Exercise** · Write `batch_checks(df, month)` returning a list of problems (empty when the batch is fine):
# row count within 2% of the 4,800 feeders, no duplicate `feeder_id`, every `month` equal to `month`.

# %%
N_FEEDERS = 4800


def batch_checks(df: pd.DataFrame, month: str) -> list[str]:
    # BEGIN SOLUTION
    problems = []
    if abs(len(df) - N_FEEDERS) > 0.02 * N_FEEDERS:
        problems.append(f"{len(df)} rows, expected {N_FEEDERS}")
    dup = int(df["feeder_id"].duplicated().sum())
    if dup:
        problems.append(f"{dup} duplicate feeder_id rows")
    wrong = int((df["month"] != month).sum())
    if wrong:
        problems.append(f"{wrong} rows of another month")
    return problems
    # END SOLUTION


# %%
try:
    print("July:", batch_checks(july, "2026-07") or "no problem")
except NotImplementedError:  # safety net: the reference checks
    batch_checks = contracts.batch_checks
    print("July:", batch_checks(july, "2026-07") or "no problem")

# %% [markdown]
# ## 3 · The step that stops the run (7')
#
# ✏️ **Exercise** · Write the pipeline step `validate(ctx)`: run the schema lazily (every failure, not the first)
# and the batch checks on `ctx["df"]`. If anything fails, write a short report to `artifacts/D1_3/` and raise
# `K.StopRun` with a one-line reason; otherwise return `{"rows": len(df)}`. Training comes after it, so a
# stopped run trains nothing.

# %%
def load(ctx):
    ctx["df"] = K.load_batch(ctx["batch"])
    return {"loaded_rows": len(ctx["df"])}


def validate(ctx):
    # BEGIN SOLUTION
    df, problems = ctx["df"], batch_checks(ctx["df"], ctx["batch"])
    failures = pd.DataFrame()
    try:
        SCHEMA.validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        failures = e.failure_cases
        for (col, check), n in failures.groupby(["column", "check"]).size().items():
            problems.append(f"{col}: {n} rows fail {check}")
    if problems:
        report = OUT / f"validation_{ctx['batch']}.txt"
        report.write_text("\n".join(problems) + "\n", encoding="utf-8")
        ctx["failure_cases"] = failures
        raise K.StopRun(f"{len(problems)} contract problems, see {report.name}")
    return {"rows": len(df)}
    # END SOLUTION


def train(ctx):
    months = K.MONTHS[K.MONTHS.index(ctx["batch"]) - 2: K.MONTHS.index(ctx["batch"]) + 1]
    df = K.training_frame(months)
    model = K.train_fault_model(df, K.FEATURES, {"max_iter": K.pick(100, 30)})
    return {"trained_on": months, "train_rows": len(df)}


STEPS = [("load", load), ("validate", validate), ("train", train)]

# %% [markdown]
# ## 4 · Run the pipeline on three batches (5')

# %%
try:
    validate({"df": july, "batch": "2026-07"})
except NotImplementedError:  # safety net: the reference step
    STEPS = [("load", load), ("validate", contracts.validate_step(OUT)), ("train", train)]
logs = {}
for batch in ("2026-07", "2026-08", "2026-09"):
    logs[batch] = K.run_flow("retrain", STEPS, {"batch": batch}, trigger="schedule", log_dir=OUT / "runs")
    K.print_run(logs[batch])
assert logs["2026-07"].status == "succeeded" and logs["2026-08"].status == "succeeded"
assert logs["2026-09"].status == "stopped" and logs["2026-09"].steps[-1]["step"] == "validate"
print("\n".join(contracts.problems(K.load_batch("2026-09"), "2026-09")))
K.check(True, "the corrupt batch stopped the run before training")

# %% [markdown]
# 🔍 Read the September report. Which problem would have trained a model that looked fine on its metric? (A load
# written as a fraction is a valid number; only the range says it is wrong.)

# %% [markdown]
# ## ✱ Stretch · Quarantine and report
#
# Split the September batch into rows that pass and rows that fail, save the failing rows to
# `artifacts/D1_3/quarantine_2026-09.csv`, and write three lines for the SCADA export team: what failed, how many
# rows, an example.

# %%
try:
    # BEGIN SOLUTION
    sep = K.load_batch("2026-09")
    bad_idx = set()
    try:
        SCHEMA.validate(sep, lazy=True)
    except pa.errors.SchemaErrors as e:
        bad_idx = set(e.failure_cases["index"].dropna().astype(int))
    bad_idx |= set(sep.index[sep.duplicated("feeder_id", keep="first")])
    sep.loc[sorted(bad_idx)].to_csv(OUT / "quarantine_2026-09.csv", index=False)
    print(f"{len(bad_idx)} rows quarantined of {len(sep)}")
    print(sep.loc[sorted(bad_idx)].groupby("region").size().to_string())
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. Why is validation a step before training and not a check on the trained model's metric?
#    <details><summary>Answer</summary>A model trained on loads written as fractions can still score well on the
#    same broken data. The contract stops the run before the damage, and names the cause.</details>
# 2. Why validate lazily?
#    <details><summary>Answer</summary>The data owner gets every problem in one report instead of one per
#    delivery.</details>
# 3. The September batch has 36 duplicated rows. Would dropping duplicates in the pipeline be enough?
#    <details><summary>Answer</summary>No: it hides a fault in the export and leaves the two other problems. Stop,
#    report, and let the owner fix the source.</details>
#
# ## Carry forward
#
# `validate` and `SCHEMA` are the validation step of the retraining pipeline in Lab 3.4 (which ships its own copy).
