"""Capstone starter: Wahaj's release week, one command per day. Make it yours.

    cd labs
    uv run python capstone/make_week.py                         # once: writes capstone/week/
    uv run python capstone/starter.py monday --approver "Lamya Al-Muqbil"
    uv run python capstone/starter.py tuesday --approver "Lamya Al-Muqbil"
    uv run python capstone/starter.py wednesday
    uv run python capstone/starter.py thursday
    uv run python capstone/starter.py status

Each command writes into --out (default capstone/out, or $CAPSTONE_OUT): pipeline run logs in runs/, one line per
decision in release_log.jsonl, and a timestamped trace of everything it did in traces/<day>.jsonl. Copy those into
your own repository with your README and runbook.

What is wired in, from the labs (search for "CAPSTONE:" to find what to change):
  monday, tuesday  the retraining pipeline of Lab 3.4: load, validate against the contract (Lab 1.3), train on
                   seven months, register with lineage, gate overall and by region (Lab 1.4), approve, promote
  wednesday        the offline evaluation gate (Lab 2.2), then a canary with an analysis and triggers (Lab 2.3)
  thursday         the incident's report rerun against a ticket service that times out (Lab 4.2), and the
                   regression suite replayed through the harness guards (Lab 4.3)

Synthetic data only. Without a working model key, Nabd's gate runs on the scripted stand-in model; say so in your
README.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LABS))
os.chdir(LABS)
os.environ["OPS_QUICK"] = "0"  # the week always runs at full size, so everyone's numbers agree

import pandas as pd  # noqa: E402

import contracts  # noqa: E402
import evalgate as G  # noqa: E402
import mubadir as M  # noqa: E402
import nabd  # noqa: E402
import opskit as K  # noqa: E402

WEEK = LABS / "capstone" / "week"


# ------------------------------------------------------------------ logs with timestamps
def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Week:
    def __init__(self, out: Path, day: str):
        self.out, self.day = out, day
        for d in ("runs", "traces"):
            (out / d).mkdir(parents=True, exist_ok=True)

    def trace(self, event: str, **data):
        with (self.out / "traces" / f"{self.day}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": now(), "day": self.day, "event": event, **data}, ensure_ascii=False, default=str) + "\n")
        print(f"[{self.day}] {event}", {k: v for k, v in data.items() if k not in ("rows", "auc")})

    def decide(self, system: str, release: str, decision: str, metric: str, evidence):
        line = {"ts": now(), "day": self.day, "system": system, "release": release, "decision": decision,
                "decided_on": metric, "evidence": evidence}
        with (self.out / "release_log.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")
        self.trace("decision", system=system, release=release, decision=decision, decided_on=metric)


# ------------------------------------------------------------------ Monday and Tuesday: the retraining pipeline
# CAPSTONE: the gate rule and its tolerance. Justify the tolerance in your README (Lab 1.4's stretch measures it).
TOLERANCE = 0.03
APPROVERS = {"Lamya Al-Muqbil", "Dhafer Al-Hazzani"}


def gate(table: pd.DataFrame) -> tuple[bool, list[str]]:
    champ, ch = table.loc["champion"], table.loc["challenger"]
    reasons = [f"overall AUC {ch['all']:.3f} is not above {champ['all']:.3f}"] if ch["all"] <= champ["all"] else []
    reasons += [f"{K.REGIONS[r]} AUC {ch[r]:.3f} is more than {TOLERANCE} below {champ[r]:.3f}"
                for r in K.REGIONS if ch[r] < champ[r] - TOLERANCE]
    return not reasons, reasons or ["passed overall and in every region"]


def registry(out: Path):
    folder = out / "registry"
    if (folder / "mlflow.db").exists():
        return K.mlflow_client(folder)
    print("building the reference registry (champion v3), about a minute")
    return K.seed_registry(folder)


def retrain(w: Week, batch_file: Path, month: str, approver: str | None):
    client = registry(w.out)
    i = K.MONTHS.index(month)
    months = K.MONTHS[i - 6: i + 1]

    def load(ctx):
        return {"df": pd.read_csv(batch_file)}

    def train(ctx):
        frames = [K.load_batch(m) for m in months[:-1]] + [ctx["df"]]
        df = pd.concat(frames, ignore_index=True)
        df = df[~K.is_holdout(df)].sort_values(["month", "feeder_id"]).reset_index(drop=True)
        h, _ = K.snapshot(df, w.out / "registry" / "snapshots")
        model = K.train_fault_model(df, K.FEATURES, K.TRAIN_PARAMS)
        v = K.register_fault_model(client, model, months=months, features=K.FEATURES, params=K.TRAIN_PARAMS,
                                   snapshot_hash=h, metrics={}, author="retrain pipeline",
                                   note=f"{w.day} retrain on {batch_file.name}")
        client.set_registered_model_alias("fault-risk", "challenger", str(v))
        return {"version": v, "data_snapshot": h}

    def gate_step(ctx):
        hold = ctx["df"][K.is_holdout(ctx["df"])].sort_values("feeder_id").reset_index(drop=True)
        table = pd.DataFrame({a: K.auc_by_region(hold["fault_30d"], K.predict_risk(K.load_registered(client, a)[1], hold), hold["region"])
                              for a in ("champion", "challenger")}).T
        ok, reasons = gate(table)
        w.trace("gate", auc=table.round(3).to_dict("index"), passed=ok, reasons=reasons)
        if not ok:
            raise K.StopRun("; ".join(reasons))
        return {"gate": reasons[0]}

    def approve(ctx):
        if approver not in APPROVERS:
            raise K.StopRun(f"waiting for approval: {approver!r} is not an approver of fault-risk")
        return {"approved_by": approver, "approved_at": now()}

    def promote(ctx):
        old = client.get_model_version_by_alias("fault-risk", "champion").version
        client.set_registered_model_alias("fault-risk", "previous-champion", old)
        client.set_registered_model_alias("fault-risk", "champion", str(ctx["version"]))
        for k in ("approved_by", "approved_at", "gate"):
            client.set_model_version_tag("fault-risk", str(ctx["version"]), k, str(ctx[k]))
        client.set_model_version_tag("fault-risk", str(ctx["version"]), "promoted_from", str(old))
        return {"promoted": f"v{old} -> v{ctx['version']}"}

    steps = [("load", load), ("validate", contracts.validate_step(w.out / "runs")), ("train", train),
             ("gate", gate_step), ("approve", approve), ("promote", promote)]
    w.trace("pipeline start", batch=str(batch_file.relative_to(LABS)), months=months)
    log = K.run_flow("retrain", steps, {"batch": month}, trigger=f"{w.day} schedule", log_dir=w.out / "runs")
    K.print_run(log)
    w.trace("pipeline end", run_id=log.run_id, status=log.status, reason=log.reason)
    champ = client.get_model_version_by_alias("fault-risk", "champion")
    decision = {"succeeded": "promoted", "stopped": "stopped"}.get(log.status, log.status)
    w.decide("fault-risk classifier", f"fault-risk v{champ.version}" if decision == "promoted" else f"retrain {month}",
             decision, log.steps[-1]["step"], log.reason or f"champion is now v{champ.version}")


# ------------------------------------------------------------------ Wednesday: a provider model update for Nabd
# CAPSTONE: the canary's objective, triggers and stages. State each in your runbook with the reason for its value.
SLO_P95_MS, MAX_QUALITY_DROP, MIN_SAMPLE = 2500, 0.05, 50
STEPS = [{"setWeight": 5}, {"pause": 60}, {"setWeight": 25}, {"pause": 30}, {"setWeight": 50}, {"pause": 30}, {"setWeight": 100}]


def analyse(window: list[dict]) -> tuple[str, str]:
    n = len(window)
    if n < MIN_SAMPLE:
        return "inconclusive", f"{n} requests, fewer than {MIN_SAMPLE}"
    p95 = K.p95([r["latency_ms"] for r in window])
    ok = sum(r["grade_ok"] for r in window) / n
    ok_s = sum(r["stable"]["grade_ok"] for r in window) / n
    ar = sum(r["lang"] == "ar" for r in window) / n
    why = f"n={n}, p95 {p95:.0f} ms, ok {ok:.3f} against stable {ok_s:.3f}, Arabic {ar:.0%}"
    if p95 > SLO_P95_MS:
        return "fail", "latency trigger: " + why
    if ok < ok_s - MAX_QUALITY_DROP:
        return "fail", "quality trigger: " + why
    return "pass", why


def wednesday(w: Week):
    candidate = K.read_json(WEEK / "nabd_release_2026.11.5.json")
    champion = nabd.load_release("champion")
    base, cand = G.evaluate(champion), G.evaluate(candidate)
    verdict = G.gate(cand, base)
    w.trace("offline gate", model=cand["model"], metrics={m: v["rate"] for m, v in cand["metrics"].items()},
            decision=verdict["decision"], reasons=verdict["reasons"])
    if verdict["decision"] != "ship":
        w.decide("Nabd", candidate["release"], "blocked", "offline gate", verdict["reasons"])
        return
    traffic = K.read_jsonl(WEEK / "canary_week.jsonl")
    log = K.run_rollout(traffic, STEPS, analyse)
    for e in log:
        w.trace("rollout", step=e["event"], **{k: v for k, v in e.items() if k != "event"})
    abort = next((e for e in log if e["event"].startswith("abort")), None)
    paused = next((e for e in log if e["event"].startswith("paused")), None)
    if abort:
        w.decide("Nabd", candidate["release"], "rolled back", abort["why"].split(":")[0], abort["why"])
    elif paused:
        w.decide("Nabd", candidate["release"], "paused for a person", "inconclusive analysis", paused["event"])
    else:
        last = [e for e in log if e["event"].startswith("analysis")][-1]
        w.decide("Nabd", candidate["release"], "shipped", "every canary analysis passed", last["why"])


# ------------------------------------------------------------------ Thursday: a Mubadir incident
MAX_AGE_MIN = 15


def freshness_guard(action, history):
    """Lab 4.3's fix for INC-0412: never close a report on a stale 'restored'."""
    if action.get("tool") != "close_report":
        return None
    outs = [e["result"] for e in history if e.get("type") == "tool" and e.get("tool") == "get_outage"]
    if not outs or outs[-1].get("status") != "restored" or outs[-1].get("age_minutes", 0) > MAX_AGE_MIN:
        return f"outage status not confirmed fresh (limit {MAX_AGE_MIN} minutes)"
    return None


GUARDS = [freshness_guard]


def services_for(folder: Path, session_id: str) -> M.Services:
    """CAPSTONE: INC-0419. The ticket service below commits, then times out once (as it did on Thursday).
    Return services with which a retry cannot open a second ticket (Lab 4.2)."""
    return M.Services(folder, flaky_create=True)


def thursday(w: Week):
    rec = K.read_json(WEEK / "INC-0419.json")
    w.trace("incident", incident=rec["incident"], summary=rec["summary"], tickets=rec.get("tickets_created"))
    for e in rec["events"]:
        if e["type"] in ("tool", "retry"):
            w.trace("recorded " + e["type"], step=e["step"], tool=e.get("tool"), result=e.get("result", e.get("error")))
    # The same report, live, against a ticket service that times out after committing: how many tickets now?
    folder = w.out / "thursday_services"
    if folder.exists():
        for p in folder.glob("*"):
            p.unlink()
    svc = services_for(folder, "S-0419-fix")
    run = M.run_session(rec["events"][0]["text"], svc, session_id="S-0419-fix")
    tickets = svc.tickets()
    svc.close()
    w.trace("rerun with the fix", status=run["status"], final=run["final"], tickets=[t["ticket_id"] for t in tickets])
    suite = K.read_json(K.DATA / "replay" / "suite.json")["cases"] + [
        {"name": "INC-0412", "recording": str(K.DATA / "replay" / "INC-0412.json"), "expect": {"blocked_tool": "close_report"}},
    ]
    results = {}
    for case in suite:
        path = Path(case["recording"])
        path = path if path.is_absolute() else K.DATA / "replay" / path
        r = M.replay(K.read_json(path), GUARDS)
        exp = case["expect"]
        ok = (r.get("blocked") == exp["blocked_tool"]) if "blocked_tool" in exp else \
            ((not r["diverged"]) and exp["final_contains"] in (r["final"] or ""))
        results[case["name"]] = ok
        w.trace("replay case", case=case["name"], passed=ok, blocked=r.get("blocked"), why=r.get("why"))
    results["INC-0419: one ticket after a timeout"] = len(tickets) == 1
    passed = sum(results.values())
    decision = "fixed" if all(results.values()) else "open"
    w.decide("Mubadir", "harness and ticket service", decision, "regression suite and the INC-0419 rerun",
             f"{passed} of {len(results)} checks pass; {len(tickets)} ticket(s) after the timeout")


# ------------------------------------------------------------------ command line
def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("day", choices=["monday", "tuesday", "wednesday", "thursday", "status"])
    p.add_argument("--approver", default=None, help="who approves a promotion (monday, tuesday)")
    p.add_argument("--out", default=os.environ.get("CAPSTONE_OUT", str(LABS / "capstone" / "out")))
    a = p.parse_args()
    out = Path(a.out).resolve()
    if not WEEK.exists():
        sys.exit("capstone/week/ is missing: run  uv run python capstone/make_week.py  first")
    w = Week(out, a.day)
    if a.day == "monday":
        retrain(w, K.DATA / "batches" / "feeders_2026-09.csv", "2026-09", a.approver)
    elif a.day == "tuesday":
        retrain(w, WEEK / "feeders_2026-09_redelivered.csv", "2026-09", a.approver)
    elif a.day == "wednesday":
        wednesday(w)
    elif a.day == "thursday":
        thursday(w)
    else:
        log = out / "release_log.jsonl"
        print(log.read_text(encoding="utf-8") if log.exists() else "no decisions yet")


if __name__ == "__main__":
    main()
