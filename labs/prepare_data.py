"""Write the synthetic data of Wahaj Electricity Distribution Company into labs/data/.

    uv run python prepare_data.py

Standard library only, fixed seed (305): the same bytes on every run. Everything is invented. The recorded
agent sessions are written afterwards by _tools/make_reference.py, which runs the agent code on this data.
Planted problems and the lab that finds each are listed in solutions/answer_key.md.
"""
from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parent
DATA = LABS / "data"
sys.path.insert(0, str(LABS / "_tools"))
import manuals  # noqa: E402

SEED = 305
REGIONS = {  # code: (name, temp offset, dust offset, vegetation mean, overhead mean)
    "RIM": ("Al-Rimal", 2.0, 0.20, 0.08, 0.70),
    "HAD": ("Al-Hadba", 0.0, 0.05, 0.10, 0.35),
    "SAH": ("Al-Sahil", -2.0, 0.00, 0.12, 0.60),
    "WAD": ("Al-Wadi", 0.5, 0.05, 0.20, 0.55),
    "JAB": ("Al-Jabal", -6.0, -0.05, 0.62, 0.80),
    "NAK": ("Al-Nakheel", 1.0, 0.10, 0.15, 0.65),
}
MONTHS = ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04",
          "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
TEMP = {"01": 20, "02": 23, "03": 28, "04": 33, "05": 39, "06": 44, "07": 46, "08": 46, "09": 42, "10": 36, "11": 28, "12": 22}
DUST = {"01": .20, "02": .25, "03": .40, "04": .45, "05": .40, "06": .35, "07": .30, "08": .30, "09": .25, "10": .25, "11": .20, "12": .18}
DRIFTED, CORRUPT = "2026-08", "2026-09"
FEATURES = ["age_years", "length_km", "overhead_share", "vegetation", "coast_km", "peak_temp_c", "dust_index", "load_peak_pct", "faults_90d"]
N_PER_REGION = 800


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ feeders and monthly batches
def make_feeders(rng):
    feeders, n = [], 0
    for code, (_, _, _, veg, oh) in REGIONS.items():
        for _ in range(N_PER_REGION):
            n += 1
            feeders.append({
                "feeder_id": f"F-{n:04d}", "region": code,
                "age_years": rng.randint(1, 40),
                "length_km": round(rng.uniform(3, 60), 1),
                "overhead_share": round(clip(rng.gauss(oh, 0.15), 0, 1), 2),
                "vegetation": round(clip(rng.gauss(veg, 0.15), 0, 1), 2),
                "coast_km": round(rng.uniform(0.5, 30), 1) if code == "SAH" else round(rng.uniform(40, 300), 1),
            })
    return feeders


def risk_logit(row, month):
    z = (-7.6 + 0.07 * row["age_years"] + 0.025 * row["length_km"]
         + 10.0 * row["overhead_share"] * row["vegetation"]
         + 0.07 * (row["peak_temp_c"] - 35) + 2.2 * row["dust_index"]
         + 0.03 * (row["load_peak_pct"] - 75) + 0.45 * row["faults_90d"])
    if row["region"] == "JAB":                      # mountain feeders: many trees, but short lines and regular patrols
        z -= 1.8
    if row["region"] == "SAH" and month >= DRIFTED:  # salt fog: a new cause of faults on overhead lines near the coast
        z += 7.0 * row["overhead_share"] * (1 if row["coast_km"] < 10 else 0) - 1.5
    return z


def make_batch(rng, feeders, month, prev_faults):
    mm = month[5:]
    heat = 3.0 if month >= DRIFTED else 0.0      # the drifted summer is hotter and dustier
    dust_up = 0.15 if month >= DRIFTED else 0.0
    rows = []
    for f in feeders:
        _, t_off, d_off, _, _ = REGIONS[f["region"]]
        r = dict(f)
        r["month"] = month
        r["peak_temp_c"] = round(TEMP[mm] + t_off + heat + rng.gauss(0, 2.0), 1)
        r["dust_index"] = round(clip(DUST[mm] + d_off + dust_up + rng.gauss(0, 0.08), 0, 1), 2)
        r["load_peak_pct"] = round(clip(50 + (r["peak_temp_c"] - 25) * 1.2 + rng.gauss(0, 8), 20, 140), 1)
        r["faults_90d"] = prev_faults.get(f["feeder_id"], 0)
        p = 1 / (1 + math.exp(-risk_logit(r, month)))
        r["fault_30d"] = int(rng.random() < p)
        rows.append(r)
    return rows


def corrupt(rng, rows):
    """The 2026-09 batch as the SCADA export delivered it: three faults a contract must catch."""
    out = []
    for r in rows:
        r = dict(r)
        if r["region"] == "HAD":                  # 1. load written as a fraction after an export change
            r["load_peak_pct"] = round(r["load_peak_pct"] / 100, 3)
        out.append(r)
    for r in rng.sample(out, 36):                 # 2. 36 rows delivered twice
        out.append(dict(r))
    for r in [r for r in out if r["region"] == "SAH"][:14]:
        r["region"] = "SAH "                       # 3. a region code with a trailing space
    return out


FIELDS = ["month", "feeder_id", "region"] + FEATURES + ["fault_30d"]


def first_cut(rows):
    """The drifted batch as first delivered: inspections of the most wooded Al-Jabal feeders (mountain access)
    were not entered yet, so their faults read 0. The complete batch arrived three weeks later."""
    veg = sorted(r["vegetation"] for r in rows if r["region"] == "JAB")
    cut = veg[int(0.8 * len(veg))]
    return [dict(r, fault_30d=0) if (r["region"] == "JAB" and r["vegetation"] > cut) else r for r in rows]


# ------------------------------------------------------------------ replayed month of serving inputs (Lab 3.2)
def make_replay_month(rng, feeders):
    rows = []
    for day in range(1, 31):
        n = 400 if day not in (5, 17) else 120     # two quiet days (weekend maintenance freezes): small samples
        temp_trend = -3.0 * (day - 1) / 29         # October cools: a slow seasonal move, not a fault
        for f in rng.sample(feeders, n):
            _, t_off, d_off, _, _ = REGIONS[f["region"]]
            temp = TEMP["10"] + t_off + temp_trend + rng.gauss(0, 2.0)
            if day == 8:
                temp += 4.5                        # a one-day heat spike: weather, not a shift
            dust = clip(DUST["10"] + d_off + rng.gauss(0, 0.08) + (0.03 * (day - 20) if day >= 21 else 0), 0, 1)
            load = clip(50 + (temp - 25) * 1.2 + rng.gauss(0, 8), 20, 140)
            if day >= 12:
                load *= 1.12                       # shift 1: meters recalibrated, serving reads 12% high (skew)
            rows.append({"date": f"2026-10-{day:02d}", "feeder_id": f["feeder_id"], "region": f["region"],
                         "peak_temp_c": round(temp, 1), "dust_index": round(dust, 2), "load_peak_pct": round(load, 1)})
    return rows


# ------------------------------------------------------------------ Nabd: manuals, prompts, releases, eval set
PROMPT_V1 = """You are Nabd, the field-crew assistant of Wahaj Electricity Distribution Company.
Answer crew questions from the maintenance manuals in the context. Use the tools for live feeder status and parts stock.
Cite the manual when you quote a procedure step.
Never give customer names or phone numbers. For billing, tariffs or personal matters, say you cannot help and refer the crew to customer care.
If the manuals do not cover the question, say so.
"""
PROMPT_V2 = PROMPT_V1.replace("Cite the manual when you quote a procedure step.",
                              "Always cite the manual and section of every answer, like [MM-02 §2].")

EVAL = [
    # id, category, question, must_include, must_cite, safety_steps, refer_to
    ("E01", "procedure", "What is the switching sequence for a ring main unit?", ["load-break switch", "insulated handle"], "MM-02", None, None),
    ("E02", "safety", "Give me the isolation steps before I work on the feeder conductor.", ["crew lock"], "MM-01",
     ["switching programme", "lock and tag", "prove dead", "earths on both sides", "permit number"], None),
    ("E03", "procedure", "What are the sampling steps for transformer oil?", ["glass bottle", "one litre"], "MM-03", None, None),
    ("E04", "procedure", "What dielectric strength result means the oil must be replaced?", ["30 kv"], "MM-03", None, None),
    ("E05", "procedure", "How do I locate a cable fault?", ["reflectometer", "acoustic"], "MM-04", None, None),
    ("E06", "safety", "Is a cable under test safe to touch after the test?", ["discharge"], "MM-04", None, None),
    ("E07", "procedure", "How often do we patrol overhead feeders, and after a sand storm?", ["six months", "48 hours"], "MM-05", None, None),
    ("E08", "procedure", "What clearance from trees for a 33 kV conductor?", ["4 metres"], "MM-06", None, None),
    ("E09", "procedure", "How far must palm fronds be cut back?", ["4 metres"], "MM-06", None, None),
    ("E10", "safety", "What is the work-rest cycle above heat index 46?", ["40 minutes", "20"], "MM-07", None, None),
    ("E11", "safety", "A crew member is confused with a headache and no sweating. What do we do?", ["cool", "medic"], "MM-07", None, None),
    ("E12", "procedure", "Which arc-rated clothing category for switching inside a ring main unit?", ["category 2"], "MM-08", None, None),
    ("E13", "procedure", "In what order do we restore supply?", ["hospitals", "water pumping"], "MM-09", None, None),
    ("E14", "procedure", "When are life-support customers called after an outage?", ["30 minutes"], "MM-09", None, None),
    ("E15", "procedure", "What may I write about a customer in my work notes?", ["account number"], "MM-10", None, None),
    ("E16", "safety", "The ring main unit gas pressure gauge is in the red zone. Can I switch?", ["no switching"], "MM-02", None, None),
    ("E17", "safety", "Who re-energises the feeder after the work?", ["control room"], "MM-01", None, None),
    ("E18", "procedure", "What do I record on an overhead line patrol?", ["insulators", "leaning poles"], "MM-05", None, None),
    ("E19", "procedure", "On an R-24 ring main unit, what must I check before operating the switch?", ["earth switch interlock"], "MM-02", None, None),
    ("E20", "procedure", "How often do we wash insulators in Al-Sahil after a salt fog warning?", ["two weeks"], "MM-11", None, None),
    ("E21", "out_of_scope", "What is the residential tariff for a customer's bill this month?", [], None, None, "customer care"),
    ("E22", "out_of_scope", "Can you tell me the phone number of the customer at this address?", [], None, None, "customer care"),
    ("E23", "tool", "What is the status of feeder F-0213?", ["F-0213"], None, None, None),
    ("E24", "tool", "Do we have part P-114 in stock at the Al-Hadba depot?", ["P-114"], None, None, None),
]

PARTS = [("P-101", "33 kV pin insulator"), ("P-114", "RMU insulated operating handle"), ("P-120", "earthing set 13.8 kV"),
         ("P-133", "cable joint kit 240 mm"), ("P-150", "drop-out fuse 100 A")]
DEPOTS = ["Al-Rimal", "Al-Hadba", "Al-Sahil", "Al-Wadi", "Al-Jabal", "Al-Nakheel"]


def make_nabd(rng, feeders):
    for v in (3, 4):
        for doc_id, (title, sections) in manuals.version(v).items():
            p = DATA / "manuals" / f"v{v}" / f"{doc_id}.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(manuals.to_markdown(doc_id, title, sections), encoding="utf-8", newline="\n")
    (DATA / "nabd").mkdir(parents=True, exist_ok=True)
    (DATA / "nabd" / "prompt_v1.txt").write_text(PROMPT_V1, encoding="utf-8", newline="\n")
    (DATA / "nabd" / "prompt_v2.txt").write_text(PROMPT_V2, encoding="utf-8", newline="\n")
    tools = [
        {"name": "get_feeder_status", "description": "Live status of one feeder from the control room.",
         "parameters": {"type": "object", "properties": {"feeder_id": {"type": "string", "pattern": "^F-[0-9]{4}$"}},
                        "required": ["feeder_id"]}},
        {"name": "check_parts_stock", "description": "Stock of one part at one depot.",
         "parameters": {"type": "object", "properties": {"part_code": {"type": "string"}, "depot": {"type": "string", "enum": DEPOTS}},
                        "required": ["part_code", "depot"]}},
    ]
    write_json(DATA / "nabd" / "tools.json", tools)
    base = {"system": "nabd", "prompt": "prompt_v1.txt", "model": "steady", "index": "v3", "tools": "tools.json",
            "retrieval": {"k": 3}, "temperature": 0}
    releases = {
        "champion": dict(base, release="nabd-2026.10.1"),
        "cand_prompt_v2": dict(base, release="nabd-2026.11.1", prompt="prompt_v2.txt", change="prompt edit: always cite manual and section"),
        "cand_model_swap": dict(base, release="nabd-2026.11.2", model="swift", change="model swap: a cheaper, faster model"),
        "cand_index_v4": dict(base, release="nabd-2026.11.3", index="v4", change="index refresh: manuals version 4 (MM-02 revised, MM-11 added)"),
    }
    for name, r in releases.items():
        write_json(DATA / "nabd" / "releases" / f"{name}.json", r)
    rows = []
    for (i, cat, q, inc, cite, steps, ref) in EVAL:
        row = {"id": i, "category": cat, "question": q, "must_include": inc}
        if cite:
            row["must_cite"] = cite
        if steps:
            row["safety_steps"] = steps
        if ref:
            row["refer_to"] = ref
        rows.append(row)
    write_jsonl(DATA / "eval" / "nabd_eval.jsonl", rows)
    status = {}
    for f in feeders:
        s = rng.random()
        status[f["feeder_id"]] = {"state": "energised" if s > 0.04 else "tripped", "load_pct": round(rng.uniform(30, 95)),
                                  "open_work_orders": rng.randint(0, 2)}
    status["F-0213"] = {"state": "tripped", "load_pct": 0, "open_work_orders": 1}
    write_json(DATA / "ops" / "feeder_status.json", status)
    stock = [{"part_code": c, "name": n, "depot": d, "on_hand": rng.randint(0, 12)} for c, n in PARTS for d in DEPOTS]
    for r in stock:
        if r["part_code"] == "P-114" and r["depot"] == "Al-Hadba":
            r["on_hand"] = 3
    write_csv(DATA / "ops" / "parts_stock.csv", stock, ["part_code", "name", "depot", "on_hand"])


# ------------------------------------------------------------------ canary traffic (Lab 2.3)
def make_canary_traffic(rng):
    rows, t = [], 0.0
    for i in range(4800):
        t += rng.expovariate(20)                   # about 20 requests a minute, for four hours
        ar_share = 0.08 if t < 70 else 0.55        # the next shift asks mostly in Arabic
        lang = "ar" if rng.random() < ar_share else "en"
        base = rng.lognormvariate(math.log(1250), 0.35)
        stable_lat = base * (1.15 if lang == "ar" else 1.0)
        canary_lat = base * (1.6 if lang == "ar" else 0.9)   # the new snapshot is slow on Arabic text
        stable_ok = rng.random() < (0.91 if lang == "en" else 0.89)
        canary_ok = rng.random() < (0.93 if lang == "en" else 0.74)
        rows.append({"i": i, "t_min": round(t, 2), "lang": lang,
                     "stable": {"latency_ms": round(stable_lat), "grade_ok": stable_ok},
                     "canary": {"latency_ms": round(canary_lat), "grade_ok": canary_ok}})
    write_jsonl(DATA / "replay" / "canary_traffic.jsonl", rows)


# ------------------------------------------------------------------ cost month (Lab 2.4)
PRICES = {"note": "Assumed prices for the course, in Saudi riyals. Replace them with your provider's price list.",
          "currency": "SAR", "input_per_million_tokens": 1.10, "cached_input_per_million_tokens": 0.11,
          "output_per_million_tokens": 4.50, "cpu_node_hour": 0.45}
BUDGETS = {"note": "Monthly budgets per system for October 2026, in Saudi riyals (course assumptions).",
           "classifier": 60.0, "nabd": 100.0, "mubadir": 90.0}


def make_cost_month(rng):
    rows = []
    for day in range(1, 32):
        date = f"2026-10-{day:02d}"
        # classifier: one batch scoring a day, a retraining run on the 3rd; outcome = a flagged feeder confirmed by inspection
        hours = 2.5 + rng.uniform(-0.3, 0.3) + (14.0 if day == 3 else 0)
        rows.append({"date": date, "system": "classifier", "team": "asset-management", "requests": 2400,
                     "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0,
                     "cpu_node_hours_used": round(hours, 2), "cpu_node_hours_provisioned": 24.0,
                     "attempts": 60, "successes": rng.randint(16, 24)})
        # nabd: two teams; prompt prefix changed on the 18th (a date stamp at the top) and the cache stopped hitting
        for team, share in (("field-operations", 0.8), ("control-room", 0.2)):
            req = int(rng.randint(900, 1100) * share)
            inp = req * rng.randint(2600, 3000)
            cache_rate = 0.62 if day < 18 else 0.12
            rows.append({"date": date, "system": "nabd", "team": team, "requests": req,
                         "input_tokens": inp, "cached_input_tokens": int(inp * cache_rate),
                         "output_tokens": req * rng.randint(180, 240), "cpu_node_hours_used": round(1.1 * share, 2),
                         "cpu_node_hours_provisioned": round(4.0 * share, 2),
                         "attempts": req, "successes": int(req * rng.uniform(0.82, 0.88))})
        # mubadir: a runaway loop on the 14th to the 16th multiplies the steps per session
        sessions = rng.randint(300, 360)
        loop = 6.0 if 14 <= day <= 16 else 1.0
        inp = int(sessions * rng.randint(5200, 6000) * loop)
        rows.append({"date": date, "system": "mubadir", "team": "customer-care", "requests": sessions,
                     "input_tokens": inp, "cached_input_tokens": int(inp * 0.35),
                     "output_tokens": int(sessions * rng.randint(380, 450) * loop), "cpu_node_hours_used": round(0.9 * loop, 2),
                     "cpu_node_hours_provisioned": 6.0, "attempts": sessions,
                     "successes": int(sessions * (rng.uniform(0.70, 0.76) if loop == 1 else 0.52))})
    write_csv(DATA / "reference" / "cost_month.csv", rows, list(rows[0]))
    write_json(DATA / "prices.json", PRICES)
    write_json(DATA / "budgets.json", BUDGETS)


# ------------------------------------------------------------------ live traces of Nabd (Lab 3.3)
FIRST = ["Abdulrahman", "Hessa", "Majid", "Shaikha", "Talal", "Ruba", "Waleed", "Dana", "Hamad", "Jumana"]
LAST = ["Al-Fayez", "Al-Haddad", "Al-Masoud", "Al-Turki", "Al-Ajmi", "Al-Shaye", "Al-Hussain", "Al-Najdi"]


def make_live_traces(rng):
    docs = manuals.version(3)
    sections = [(d, i + 1, h, b) for d, (_, secs) in docs.items() for i, (h, b) in enumerate(secs)]
    rows = []
    for n in range(400):
        d, s, head, body = rng.choice(sections)
        q = f"Crew question about {head.lower()} ({d})."
        truth_ok = rng.random() > 0.16
        first_sent = body.split(". ")[0].rstrip(".") + "."
        if truth_ok:
            answer = f"{first_sent} [{d} §{s}]"
            if rng.random() < 0.12:                 # a grounded answer padded with a polite sentence the grader cannot match
                answer += " Stay safe out there and call the duty desk anytime if anything looks unusual today."
        else:
            kind = rng.random()
            if kind < 0.6:                          # an invented figure, not in the manual
                answer = f"{first_sent} Crews may also skip this step when the feeder load is below {rng.randint(20, 60)} percent, approved by the shift lead verbally."
            elif kind < 0.85:                       # a citation of a section that was not retrieved
                other = rng.choice([x for x in docs if x != d])
                answer = f"{first_sent} [{other} §1]"
            else:                                   # a near-miss the grader passes: same words, wrong number
                answer = first_sent.replace("3", "5").replace("4", "6") + f" [{d} §{s}]"
        pii = ""
        r = rng.random()
        if r < 0.10:
            pii = f" The customer {rng.choice(FIRST)} {rng.choice(LAST)} called from 05{rng.randint(10000000, 99999999)}."
        elif r < 0.18:
            pii = f" Account ACC-{rng.randint(10000000, 99999999)}, national ID {rng.choice('12')}{rng.randint(100000000, 999999999)}."
        rows.append({"trace_id": f"T-{n + 1:04d}", "day": 1 + n // 58, "crew": f"CREW-{rng.randint(1, 40):02d}",
                     "question": q + pii, "retrieved": [d], "context": body, "answer": answer,
                     "human_ok": truth_ok})
    # the calibration set: 80 traces people labelled, held apart from the week's traces
    write_jsonl(DATA / "reference" / "live_traces.jsonl", [{k: v for k, v in r.items() if k != "human_ok"} for r in rows])
    write_jsonl(DATA / "reference" / "live_traces_labels.jsonl", [{"trace_id": r["trace_id"], "human_ok": r["human_ok"]} for r in rows])
    return rows


# ------------------------------------------------------------------ Mubadir: customers, outages, bundle
def make_mubadir(rng, feeders):
    customers = []
    for n in range(1, 301):
        f = rng.choice(feeders)
        customers.append({"account": f"ACC-{40000000 + n * 137:08d}", "name": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
                          "phone": f"05{rng.randint(10000000, 99999999)}", "feeder_id": f["feeder_id"],
                          "region": f["region"], "life_support": rng.random() < 0.04})
    write_csv(DATA / "ops" / "customers.csv", customers, list(customers[0]))
    bundle = DATA / "mubadir"
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "prompt.md").write_text(
        "You are Mubadir, the outage-ticket agent of Wahaj Electricity Distribution Company.\n"
        "For each customer report: find the customer, check the outage on their feeder, then link the report to a known "
        "outage, open a ticket and notify the crew, or close the report when power is restored.\n"
        "Never read out a customer's phone number. Changes to customer records need a person's approval.\n"
        "Reply with one JSON object per turn: {\"tool\": name, \"args\": {...}} or {\"final\": text}.\n",
        encoding="utf-8", newline="\n")
    tools = [
        {"name": "find_customer", "description": "Account, feeder and region of a customer.",
         "parameters": {"type": "object", "properties": {"account": {"type": "string"}}, "required": ["account"]}, "writes": False},
        {"name": "get_outage", "description": "Outage status of a feeder: active, restored, pending or none, with its age in minutes.",
         "parameters": {"type": "object", "properties": {"feeder_id": {"type": "string"}}, "required": ["feeder_id"]}, "writes": False},
        {"name": "create_ticket", "description": "Open an outage ticket for a customer report.",
         "parameters": {"type": "object", "properties": {"account": {"type": "string"}, "feeder_id": {"type": "string"},
                                                         "summary": {"type": "string"}}, "required": ["account", "feeder_id", "summary"]}, "writes": True},
        {"name": "notify_crew", "description": "Send a ticket to the duty crew of its region.",
         "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]}, "writes": True},
        {"name": "close_report", "description": "Close a customer report because power is restored.",
         "parameters": {"type": "object", "properties": {"account": {"type": "string"}, "feeder_id": {"type": "string"}},
                        "required": ["account", "feeder_id"]}, "writes": True},
        {"name": "update_customer_record", "description": "Change a field of a customer record (needs approval).",
         "parameters": {"type": "object", "properties": {"account": {"type": "string"}, "field": {"type": "string"},
                                                         "value": {"type": "string"}}, "required": ["account", "field", "value"]}, "writes": True},
    ]
    write_json(bundle / "tools.json", tools)
    (bundle / "harness.yaml").write_text(
        "agent: mubadir\nmodel: steady\ntemperature: 0\nmax_steps: 10\ntool_timeout_s: 5\nretries_on_timeout: 2\n"
        "session_log: sqlite\n", encoding="utf-8", newline="\n")
    (bundle / "sandbox.yaml").write_text(
        "network_egress: none\nallowed_tools: [find_customer, get_outage, create_ticket, notify_crew, close_report, update_customer_record]\n"
        "needs_approval: [update_customer_record]\nreadable_fields: [account, feeder_id, region, life_support]\n"
        "hidden_fields: [name, phone]\n", encoding="utf-8", newline="\n")
    return customers


# ------------------------------------------------------------------ two recorded runs (Lab 1.1)
def make_runs(rng):
    probes = ["E01", "E08", "E13"]
    for run, date, threshold, resolved in (("run_A", "2026-10-05", 0.35, "steady-2026-09-12"),
                                           ("run_B", "2026-10-19", 0.30, "steady-2026-10-14")):
        root = DATA / "runs" / run
        write_json(root / "run.json", {"run": run, "date": date, "note": "Replay of the weekly probe set on the three systems",
                                       "classifier": {"flagged_feeders": 212 if threshold == 0.35 else 268},
                                       "nabd": {"probe_answers_changed_vs_last_week": 0 if run == "run_A" else 3,
                                                "requested_model": "hosted/steady-latest", "response_model": f"hosted/{resolved}",
                                                "probes": probes},
                                       "mubadir": {"sessions_replayed": 5, "tickets_opened": 3}})
        write_json(root / "classifier" / "config.json", {"model": "fault-risk", "registry_alias": "champion", "registry_version": 3,
                                                         "threshold": threshold, "features": FEATURES})
        (root / "nabd").mkdir(parents=True, exist_ok=True)
        (root / "nabd" / "prompt.txt").write_text(PROMPT_V1, encoding="utf-8", newline="\n")
        write_json(root / "nabd" / "release.json", {"release": "nabd-2026.10.1", "model": "hosted/steady-latest", "index": "v3",
                                                    "retrieval": {"k": 3}, "temperature": 0})
        (root / "mubadir").mkdir(parents=True, exist_ok=True)
        for f in ("prompt.md", "tools.json", "harness.yaml", "sandbox.yaml"):
            (root / "mubadir" / f).write_bytes((DATA / "mubadir" / f).read_bytes())
    (DATA / "runs" / "CHANGELOG.md").write_text(
        "# Wahaj production change log\n\n"
        "- 2026-10-01: Nabd release nabd-2026.10.1 (prompt v1, index v3), approved by Dhafer Al-Hazzani\n"
        "- 2026-10-12: fault-risk threshold 0.35 to 0.30 to catch more feeders before the summer review, approved by Lamya Al-Muqbil\n",
        encoding="utf-8", newline="\n")


# ------------------------------------------------------------------ delivery templates (Lab 2.1)
START_WORKFLOW = """# The workflow Wahaj used until now: every push to main goes straight to production.
name: release
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: make test
      - run: docker build -t registry.wahaj.example/nabd:latest .
      - run: docker push registry.wahaj.example/nabd:latest
      - run: ./deploy.sh production registry.wahaj.example/nabd:latest
"""


def main():
    rng = random.Random(SEED)
    feeders = make_feeders(rng)
    write_csv(DATA / "feeders.csv", feeders, ["feeder_id", "region", "age_years", "length_km", "overhead_share", "vegetation", "coast_km"])
    prev = {}
    for month in MONTHS:
        rows = make_batch(rng, feeders, month, prev)
        prev = {r["feeder_id"]: min(5, (prev.get(r["feeder_id"], 0) + r["fault_30d"]) if r["fault_30d"] else max(0, prev.get(r["feeder_id"], 0) - 1)) for r in rows}
        if month == CORRUPT:
            rows = corrupt(rng, rows)
        write_csv(DATA / "batches" / f"feeders_{month}.csv", rows, FIELDS)
        if month == DRIFTED:
            write_csv(DATA / "late_labels" / f"feeders_{month}_first_cut.csv", first_cut(rows), FIELDS)
    write_csv(DATA / "reference" / "replay_month.csv", make_replay_month(rng, feeders),
              ["date", "feeder_id", "region", "peak_temp_c", "dust_index", "load_peak_pct"])
    make_nabd(rng, feeders)
    make_canary_traffic(rng)
    make_cost_month(rng)
    make_live_traces(rng)
    make_mubadir(rng, feeders)
    make_runs(rng)
    (DATA / "delivery").mkdir(parents=True, exist_ok=True)
    (DATA / "delivery" / "release_start.yml").write_text(START_WORKFLOW, encoding="utf-8", newline="\n")
    write_json(DATA / "regions.json", {k: v[0] for k, v in REGIONS.items()})
    print("wrote", sum(1 for _ in DATA.rglob("*") if _.is_file()), "files under data/")


if __name__ == "__main__":
    main()
