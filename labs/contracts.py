"""The data contract of a monthly feeder batch, as agreed with the SCADA export team (reference version).

Lab 1.3 writes it; Lab 3.4 and the capstone pipeline import this copy.
"""
from __future__ import annotations

import pandas as pd
import pandera.pandas as pa

import opskit as K

N_FEEDERS = 4800

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


def batch_checks(df: pd.DataFrame, month: str) -> list[str]:
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


def problems(df: pd.DataFrame, month: str) -> list[str]:
    """Every contract problem of one batch: the batch checks, then each failing column check with its count."""
    out = batch_checks(df, month)
    try:
        SCHEMA.validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        for (col, check), n in e.failure_cases.groupby(["column", "check"]).size().items():
            out.append(f"{col}: {n} rows fail {check}")
    return out


def validate_step(report_dir):
    """A pipeline step (for K.run_flow) that stops the run on any contract problem."""
    def validate(ctx):
        found = problems(ctx["df"], ctx["batch"])
        if found:
            report = K.write_json(report_dir / f"validation_{ctx['batch']}.json", {"batch": ctx["batch"], "problems": found})
            raise K.StopRun(f"{len(found)} contract problems, see {report.name}")
        return {"rows": len(ctx["df"])}
    return validate
