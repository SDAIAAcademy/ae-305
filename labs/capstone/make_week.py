"""Writes the capstone's release week into labs/capstone/week/ (fixed seed: the same files on every run).

    cd labs
    uv run python capstone/make_week.py

Everything is invented. The week runs from Monday 2 November to Thursday 5 November 2026:
  Monday     the scheduled retrain on September (labels complete on 1 November); the batch is the corrupt one
  Tuesday    the SCADA team re-delivers September, corrected
  Wednesday  the provider moves Nabd's model alias to a new snapshot, steady-2026-11-03
  Thursday   a Mubadir incident: two tickets for one report after a ticket-service timeout (INC-0419)
"""
from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import opskit as K  # noqa: E402
import mubadir as M  # noqa: E402

WEEK = HERE / "week"
SEED = 3051


def redeliver_september():
    """The corrected September batch: duplicates removed, region codes trimmed, Al-Hadba load back in percent."""
    with (K.DATA / "batches" / "feeders_2026-09.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    seen, out = set(), []
    for r in rows:
        key = tuple(r.values())
        if key in seen:
            continue
        seen.add(key)
        r = dict(r, region=r["region"].strip())
        if r["region"] == "HAD":
            r["load_peak_pct"] = f"{float(r['load_peak_pct']) * 100:.1f}"
        out.append(r)
    with (WEEK / "feeders_2026-09_redelivered.csv").open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    return len(rows), len(out)


def canary_week(rng):
    """Four hours of Nabd traffic for the new snapshot: the mix of languages is steady and the snapshot is a little
    faster and no worse, so a sound analysis lets it through."""
    rows, t = [], 0.0
    for i in range(4800):
        t += rng.expovariate(20)
        lang = "ar" if rng.random() < 0.45 else "en"
        base = rng.lognormvariate(math.log(1250), 0.35)
        stable_lat = base * (1.15 if lang == "ar" else 1.0)
        canary_lat = base * (1.05 if lang == "ar" else 0.92)
        stable_ok = rng.random() < (0.91 if lang == "en" else 0.89)
        canary_ok = rng.random() < (0.92 if lang == "en" else 0.90)
        rows.append({"i": i, "t_min": round(t, 2), "lang": lang,
                     "stable": {"latency_ms": round(stable_lat), "grade_ok": stable_ok},
                     "canary": {"latency_ms": round(canary_lat), "grade_ok": canary_ok}})
    with (WEEK / "canary_week.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def incident_0419():
    """Record the duplicate-ticket session as production logged it."""
    folder = HERE / "_tmp_svc"
    svc = M.Services(folder, flaky_create=True)
    r = M.run_session("Salam, no power since the morning prayer. Account ACC-40000411.", svc, session_id="S-0419")
    tickets = svc.tickets()
    svc.close()
    for p in folder.glob("*"):
        p.unlink()
    folder.rmdir()
    M.save_recording(r, WEEK / "INC-0419.json", meta={
        "synthetic": True, "incident": "INC-0419",
        "summary": "Two crews were paged for one customer report on feeder F-4293. The ticket service timed out "
                   "after committing the first ticket; the harness retried and opened a second.",
        "tickets_created": [t["ticket_id"] for t in tickets]})
    return [t["ticket_id"] for t in tickets]


def main():
    WEEK.mkdir(exist_ok=True)
    rng = random.Random(SEED)
    n_in, n_out = redeliver_september()
    canary_week(rng)
    tickets = incident_0419()
    K.write_json(WEEK / "nabd_release_2026.11.5.json", {
        "system": "nabd", "prompt": "prompt_v2.txt", "model": "steady", "index": "v4", "tools": "tools.json",
        "retrieval": {"k": 3}, "temperature": 0, "release": "nabd-2026.11.5",
        "change": "the provider's alias steady moves to snapshot steady-2026-11-03", "snapshot": "steady-2026-11-03"})
    K.write_json(WEEK / "events.json", {"synthetic": True, "week": "2026-11-02 to 2026-11-05", "events": [
        {"day": "Monday 2026-11-02", "system": "fault-risk classifier", "event": "scheduled retrain",
         "input": "data/batches/feeders_2026-09.csv", "note": "September's labels are complete since 1 November"},
        {"day": "Tuesday 2026-11-03", "system": "fault-risk classifier", "event": "re-delivered batch",
         "input": "capstone/week/feeders_2026-09_redelivered.csv", "note": "the SCADA team's corrected export"},
        {"day": "Wednesday 2026-11-04", "system": "Nabd", "event": "provider model update",
         "input": "capstone/week/nabd_release_2026.11.5.json and capstone/week/canary_week.jsonl",
         "note": "the alias steady now serves steady-2026-11-03"},
        {"day": "Thursday 2026-11-05", "system": "Mubadir", "event": "incident INC-0419",
         "input": "capstone/week/INC-0419.json", "note": "two tickets for one report"}]})
    print(f"September: {n_in} rows delivered, {n_out} after the re-delivery; INC-0419 tickets {tickets}")


if __name__ == "__main__":
    main()
