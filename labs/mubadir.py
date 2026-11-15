"""Mubadir (مبادر), Wahaj's outage-ticket agent: the services it calls, its loop, its session log and replay.

    import mubadir as M
    svc = M.Services(K.lab_dir("D4_x/svc"))
    result = M.run_session("My power is off. Account ACC-40000137.", svc)

The agent is a model in a loop. Each turn the model answers with one JSON object, a tool call
{"tool": name, "args": {...}} or a final reply {"final": text}. The harness runs the tool through `Services`,
with the retries and guards of its settings, and writes every event to the session log. `replay` runs a
recorded session again from its stored model outputs and tool responses, through today's harness code.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
import time
from pathlib import Path

import opskit as K

DATA = K.DATA
BUNDLE = DATA / "mubadir"


def customers() -> dict:
    with (DATA / "ops" / "customers.csv").open(encoding="utf-8") as f:
        return {r["account"]: r for r in csv.DictReader(f)}


DEFAULT_OUTAGES = {  # feeder -> outage record, as the outage service reports it
    "F-0213": {"status": "active", "ticket": "OT-30400", "age_minutes": 4},
}


class Services:
    """The services behind Mubadir's tools, on a SQLite file in `folder`.

    outages: feeder -> {"status", "ticket", "age_minutes"}; a feeder not listed has no outage ("none").
    flaky_create: the ticket service commits the ticket, then times out before it answers (once).
    idempotent: the ticket service honours an idempotency key (the fix of Lab 4.2)."""

    def __init__(self, folder, outages: dict | None = None, flaky_create: bool = False, idempotent: bool = False):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.folder / "services.db"), check_same_thread=False)
        self.db.execute("create table if not exists tickets (id text primary key, account text, feeder_id text, "
                        "summary text, idem_key text unique, notified int default 0)")
        self.db.execute("create table if not exists closed_reports (account text, feeder_id text)")
        self.db.execute("create table if not exists approvals (account text, field text, value text, status text)")
        self.db.commit()
        self.outages = dict(DEFAULT_OUTAGES if outages is None else outages)
        self.flaky_create = flaky_create
        self.idempotent = idempotent
        self._customers = customers()
        self.calls = []

    # -- read tools
    def find_customer(self, account: str) -> dict:
        c = self._customers.get(account)
        if not c:
            return {"error": f"no customer with account {account}"}
        return {"account": account, "feeder_id": c["feeder_id"], "region": c["region"], "life_support": c["life_support"] == "True"}

    def get_outage(self, feeder_id: str) -> dict:
        o = self.outages.get(feeder_id)
        return {"feeder_id": feeder_id, **(o or {"status": "none", "ticket": None, "age_minutes": 0})}

    # -- write tools
    def create_ticket(self, account: str, feeder_id: str, summary: str, idempotency_key: str | None = None) -> dict:
        if self.idempotent and idempotency_key:
            row = self.db.execute("select id from tickets where idem_key=?", (idempotency_key,)).fetchone()
            if row:
                return {"ticket_id": row[0], "replayed": True}
        n = self.db.execute("select count(*) from tickets").fetchone()[0]
        tid = f"OT-{31000 + n + 1}"
        self.db.execute("insert into tickets (id, account, feeder_id, summary, idem_key) values (?,?,?,?,?)",
                        (tid, account, feeder_id, summary, idempotency_key if self.idempotent else None))
        self.db.commit()
        if self.flaky_create:
            self.flaky_create = False
            raise TimeoutError("ticket service did not answer within 5 s")
        return {"ticket_id": tid}

    def notify_crew(self, ticket_id: str) -> dict:
        self.db.execute("update tickets set notified=1 where id=?", (ticket_id,))
        self.db.commit()
        return {"ticket_id": ticket_id, "notified": True}

    def close_report(self, account: str, feeder_id: str) -> dict:
        self.db.execute("insert into closed_reports values (?,?)", (account, feeder_id))
        self.db.commit()
        return {"account": account, "closed": True}

    def update_customer_record(self, account: str, field: str, value: str) -> dict:
        self.db.execute("insert into approvals values (?,?,?,?)", (account, field, value, "pending"))
        self.db.commit()
        return {"status": "pending_approval", "approver": "control-room duty engineer"}

    def tickets(self) -> list[dict]:
        cur = self.db.execute("select id, account, feeder_id, notified from tickets order by id")
        return [{"ticket_id": a, "account": b, "feeder_id": c, "notified": bool(d)} for a, b, c, d in cur]

    def call(self, name: str, args: dict) -> dict:
        self.calls.append((name, dict(args)))
        fn = getattr(self, name, None)
        if fn is None or name.startswith("_"):
            return {"error": f"no tool {name}"}
        return fn(**args)

    def close(self):
        self.db.close()


# ------------------------------------------------------------------ the harness
def load_settings(folder=BUNDLE) -> dict:
    """harness.yaml and sandbox.yaml of a bundle folder."""
    import yaml
    folder = Path(folder)
    return {"harness": yaml.safe_load((folder / "harness.yaml").read_text(encoding="utf-8")),
            "sandbox": yaml.safe_load((folder / "sandbox.yaml").read_text(encoding="utf-8")),
            "prompt": (folder / "prompt.md").read_text(encoding="utf-8"),
            "tools": json.loads((folder / "tools.json").read_text(encoding="utf-8"))}


def parse_action(text: str) -> dict:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {"final": text or ""}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"final": text}


def sandbox_guard(sandbox: dict):
    def guard(action, history):
        if action["tool"] not in sandbox["allowed_tools"]:
            return f"tool {action['tool']} is not allowed by the sandbox policy"
        return None
    return guard


def run_session(report: str, services: Services, *, settings: dict | None = None, guards: list | None = None,
                session_id: str = "S-1", model: str | None = None, gateway=None, version: str = "mubadir-dev",
                store=None, max_steps: int | None = None) -> dict:
    """Run one customer report to the end. Returns {"status", "final", "events", "steps"}.

    Every model output and every tool response goes into `events`: that list is the session log, and it is
    what replay needs. With a gateway, each model call goes through it; with a store, the session is saved
    after every step, so a stop loses nothing."""
    s = settings or load_settings()
    h, sandbox = s["harness"], s["sandbox"]
    guards = [sandbox_guard(sandbox)] + list(guards or [])
    messages = [{"role": "system", "content": s["prompt"]}, {"role": "user", "content": report}]
    events, status, final = [{"type": "report", "text": report}], "max_steps", None
    limit = max_steps or h["max_steps"]
    for step in range(1, limit + 1):
        try:
            reply = (gateway.call(session_id, version, messages, model or h["model"]) if gateway
                     else K.chat(messages, model or h["model"]))
        except K.LimitExceeded as e:
            status = "stopped_by_gateway"
            events.append({"type": "stopped", "step": step, "why": str(e)})
            break
        action = parse_action(reply["content"])
        events.append({"type": "model", "step": step, "content": reply["content"], "model": reply["model"],
                       "usage": reply["usage"]})
        if "final" in action:
            status, final = "done", action["final"]
            break
        blocked = next((g(action, events) for g in guards if g(action, events)), None)
        if blocked:
            result = {"error": blocked, "blocked": True}
        else:
            result = None
            for attempt in range(1 + h.get("retries_on_timeout", 0)):
                try:
                    result = services.call(action["tool"], action.get("args", {}))
                    break
                except TimeoutError as e:
                    events.append({"type": "retry", "step": step, "tool": action["tool"], "attempt": attempt + 1, "error": str(e)})
                    result = {"error": str(e)}
        events.append({"type": "tool", "step": step, "tool": action["tool"], "args": action.get("args", {}), "result": result})
        messages.append({"role": "assistant", "content": reply["content"]})
        messages.append({"role": "user", "content": "Tool result: " + json.dumps({"tool": action["tool"], "result": result}, ensure_ascii=False)})
        if store is not None:
            store.save(session_id, version, "running", step, getattr(gateway, "sessions", {}).get(session_id, {}).get("spend", 0.0), messages)
    if store is not None:
        spend = getattr(gateway, "sessions", {}).get(session_id, {}).get("spend", 0.0)
        store.save(session_id, version, status, len([e for e in events if e["type"] == "model"]), spend, messages)
    return {"session_id": session_id, "status": status, "final": final, "events": events,
            "steps": len([e for e in events if e["type"] == "model"])}


def save_recording(result: dict, path, meta: dict | None = None) -> Path:
    return K.write_json(path, {**(meta or {}), "session_id": result["session_id"], "status": result["status"],
                               "final": result["final"], "events": result["events"]})


def replay(recording: dict, guards: list | None = None, settings: dict | None = None) -> dict:
    """Run a recorded session again through today's harness: the model outputs and the tool responses come
    from the recording, the guards are the current code. Stops where the harness acts differently."""
    s = settings or load_settings()
    guards = [sandbox_guard(s["sandbox"])] + list(guards or [])
    events = recording["events"]
    seen, out = [events[0]], []
    for i, e in enumerate(events):
        if e["type"] != "model":
            continue
        action = parse_action(e["content"])
        seen.append(e)
        if "final" in action:
            out.append({"step": e["step"], "final": action["final"]})
            return {"diverged": False, "final": action["final"], "trace": out}
        blocked = next((g(action, seen) for g in guards if g(action, seen)), None)
        if blocked:
            out.append({"step": e["step"], "blocked": action["tool"], "why": blocked})
            return {"diverged": True, "final": None, "blocked": action["tool"], "why": blocked, "trace": out}
        recorded = next(x for x in events[i + 1:] if x["type"] == "tool")
        seen.append(recorded)
        out.append({"step": e["step"], "tool": action["tool"], "args": action.get("args", {}), "result": recorded["result"]})
    return {"diverged": False, "final": None, "trace": out}


def run_case(case: dict, guards: list | None = None) -> tuple[bool, str]:
    """A regression case: a recording and what must happen when it is replayed."""
    r = replay(K.read_json(DATA / "replay" / case["recording"]), guards)
    exp = case["expect"]
    if "blocked_tool" in exp:
        return r.get("blocked") == exp["blocked_tool"], f"blocked {r.get('blocked')}"
    if "final_contains" in exp:
        ok = (not r["diverged"]) and r["final"] is not None and exp["final_contains"] in r["final"]
        return ok, ("final: " + (r["final"] or "")[:60]) if not r["diverged"] else f"diverged: {r.get('why')}"
    return False, "unknown expectation"


# ------------------------------------------------------------------ the scripted stand-in model
ACCOUNT = re.compile(r"ACC-\d{8}")


def _results(messages):
    out = []
    for m in messages[2:]:
        if m["role"] == "user" and m["content"].startswith("Tool result: "):
            out.append(json.loads(m["content"][len("Tool result: "):]))
    return out


def _say(obj) -> dict:
    return {"content": json.dumps(obj, ensure_ascii=False), "tool_calls": []}


def scripted_mubadir(messages: list[dict], tools: list) -> dict:
    """A deterministic stand-in for the hosted model behind Mubadir. It follows the prompt's procedure, and it
    trusts whatever the outage service says (which is how INC-0412 happened)."""
    time.sleep(0.01)
    report = messages[1]["content"]
    res = _results(messages)
    last = {}
    for r in res:
        last.setdefault(r["tool"], []).append(r["result"])
    acc = ACCOUNT.search(report)
    if not acc:
        return _say({"final": "Please send your account number, which starts with ACC-."})
    account = acc.group(0)
    if "find_customer" not in last:
        return _say({"tool": "find_customer", "args": {"account": account}})
    cust = last["find_customer"][-1]
    if "error" in cust:
        return _say({"final": f"I cannot find the account {account}. Please check the number on your bill."})
    feeder = cust["feeder_id"]
    if any(w in report.lower() for w in ("change my", "update my", "new phone")):
        if "update_customer_record" not in last:
            return _say({"tool": "update_customer_record", "args": {"account": account, "field": "phone", "value": "as given by the customer"}})
        return _say({"final": "Your change is waiting for approval by our duty engineer; we will confirm it."})
    outs = last.get("get_outage", [])
    if not outs or (outs[-1].get("status") == "pending") or outs[-1].get("blocked"):
        return _say({"tool": "get_outage", "args": {"feeder_id": feeder}})
    o = outs[-1]
    if "error" in o and not o.get("status"):
        return _say({"tool": "get_outage", "args": {"feeder_id": feeder}})
    if o["status"] == "active":
        return _say({"final": f"There is a known outage on your feeder {feeder}, ticket {o['ticket']}. A crew is working on it."})
    if o["status"] == "restored":
        closes = last.get("close_report", [])
        if not closes:
            return _say({"tool": "close_report", "args": {"account": account, "feeder_id": feeder}})
        if closes[-1].get("blocked"):
            return _say({"tool": "get_outage", "args": {"feeder_id": feeder}})
        return _say({"final": f"Power is restored on your feeder {feeder}. If you are still without power, reply to this message."})
    tickets = last.get("create_ticket", [])
    if not tickets:
        return _say({"tool": "create_ticket", "args": {"account": account, "feeder_id": feeder, "summary": "customer reports no power"}})
    t = tickets[-1]
    if "error" in t:
        return _say({"tool": "create_ticket", "args": {"account": account, "feeder_id": feeder, "summary": "customer reports no power"}})
    if "notify_crew" not in last:
        return _say({"tool": "notify_crew", "args": {"ticket_id": t["ticket_id"]}})
    return _say({"final": f"I opened ticket {t['ticket_id']} for your feeder {feeder} and sent it to the duty crew."})


K.register_standin("You are Mubadir", lambda m, t, persona: scripted_mubadir(m, t))
