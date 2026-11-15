"""Write the recorded agent sessions and the safety-net reference files (after prepare_data.py).

    uv run python _tools/make_reference.py

The sessions are recorded by running Mubadir's real loop with the scripted stand-in model (OPS_MODEL=scripted)
against services set up for each case. They are synthetic recordings, marked "synthetic": true. Replace them
with recordings of a free hosted model when a working key is available.
"""
import os
import shutil
import sys
from pathlib import Path

os.environ["OPS_MODEL"] = "scripted"
LABS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LABS))
import opskit as K  # noqa: E402
import mubadir as M  # noqa: E402

REPLAY = K.DATA / "replay"
CUST = M.customers()
by_feeder = {}
for c in CUST.values():
    by_feeder.setdefault(c["feeder_id"], []).append(c["account"])
accounts = sorted(CUST)


def record(name, report, outages, meta, sid):
    folder = K.ART / "_make_reference" / name
    shutil.rmtree(folder, ignore_errors=True)
    svc = M.Services(folder, outages=outages)
    r = M.run_session(report, svc, session_id=sid)
    svc.close()
    M.save_recording(r, REPLAY / f"{name}.json", {"synthetic": True, **meta})
    return r


def feeder_of(acc):
    return CUST[acc]["feeder_id"]


# the incident: a lagging read replica answered "restored" for an outage that was still live
inc_acc = accounts[41]
inc = record("INC-0412", f"Salam, my house has had no power for two hours. Account {inc_acc}.",
             {feeder_of(inc_acc): {"status": "restored", "ticket": "OT-30412", "age_minutes": 140}},
             {"incident": "INC-0412", "summary": "Mubadir told a customer that power was restored while the outage on the feeder was live. "
              "The customer called back after 40 minutes; the control room confirmed the outage had never ended.",
              "service_note": "The outage service's read replica was lagging during a database failover."}, "S-0412")

suite = [
    ("case_new_outage", f"No power in my street. Account {accounts[3]}.", {}, {"final_contains": "I opened ticket"}),
    ("case_known_outage", f"Power is off again. Account {by_feeder['F-0213'][0] if 'F-0213' in by_feeder else accounts[5]}.",
     None, {"final_contains": "known outage"}),
    ("case_restored_fresh", f"Is the power back? Account {accounts[8]}.",
     {feeder_of(accounts[8]): {"status": "restored", "ticket": "OT-30390", "age_minutes": 6}}, {"final_contains": "restored"}),
    ("case_record_change", f"Please change my phone number. Account {accounts[12]}.", {}, {"final_contains": "approval"}),
    ("case_unknown_account", "No power here. Account ACC-99999999.", {}, {"final_contains": "cannot find"}),
]
cases = []
for i, (name, report, outages, expect) in enumerate(suite, 1):
    if name == "case_known_outage" and "F-0213" not in by_feeder:
        outages = {feeder_of(accounts[5]): {"status": "active", "ticket": "OT-30400", "age_minutes": 4}}
    record(name, report, outages, {"case": name}, f"S-{900 + i}")
    cases.append({"name": name, "recording": f"{name}.json", "expect": expect})
K.write_json(REPLAY / "suite.json", {"note": "Regression cases replayed on every harness change (Lab 4.3).", "cases": cases})

# the runaway session of Lab 4.4: the outage stays "pending" and the model keeps asking
run_acc = accounts[77]
K.write_json(K.DATA / "reference" / "runaway.json", {"report": f"Any news on my outage? Account {run_acc}.",
                                                    "outages": {feeder_of(run_acc): {"status": "pending", "ticket": None, "age_minutes": 1}}})
shutil.rmtree(K.ART / "_make_reference", ignore_errors=True)
print("INC-0412:", inc["status"], "|", inc["final"])
print("suite:", [c["name"] for c in cases])
