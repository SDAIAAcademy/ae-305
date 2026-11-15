# %% [markdown]
# # Lab 4.2 · Crash, resume, and no duplicate tickets
#
# Day 4 · Session 2 (Durable execution and safe retries) · 25 min.
#
# Two complaints reached Dhafer this month: a crew was sent twice to the same feeder because Mubadir opened two
# tickets for one report, and a session that stopped during a deployment started again from the beginning. You run
# Mubadir's ticket flow as a LangGraph graph with a SQLite checkpointer, crash it between two writes and resume it,
# then reproduce the duplicate ticket that a retry after a timeout creates and fix the tool with an idempotency key.
#
# **Reference state.** The services in `mubadir.py` on a SQLite file (tickets survive a crash, as in production),
# with two switches: `flaky_create` (the ticket service commits, then times out before it answers) and
# `idempotent` (it honours an idempotency key). No model is needed for steps 1 and 2: the flow is fixed.
#
# **Tasks**
# - [ ] 1 · The ticket graph with a checkpointer (6')
# - [ ] 2 · Crash mid-task and resume (6')
# - [ ] 3 · A retry after a timeout: two tickets (6')
# - [ ] 4 · An idempotency key: one ticket (7')
# - [ ] ✱ Stretch · Read the crashed session from a second process

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
import sqlite3
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

import mubadir as M

OUT = K.lab_dir("D4_2")
REPORT_ACCOUNT = "ACC-40000137"  # feeder F-2414, no known outage: the flow opens a ticket


class Ticket(TypedDict, total=False):
    account: str
    feeder_id: str
    outage: str
    ticket_id: str
    notified: bool


CRASH = {"before": None}  # set to a node name to kill the "process" once when that node starts


def crash_point(node: str):
    if CRASH["before"] == node:
        CRASH["before"] = None
        raise RuntimeError(f"process killed before {node} (a deployment restarted the pod)")

# %% [markdown]
# ## 1 · The ticket graph with a checkpointer (6')
#
# A LangGraph graph is a set of nodes that read and update a shared state. With a **checkpointer**, the state is
# saved after every step under a `thread_id`; invoking the graph again on the same thread with no input resumes
# from the last saved step instead of starting over.
#
# ✏️ **Exercise** · Complete `build_graph(svc, saver)`: four nodes, `find_customer` → `get_outage` →
# `create_ticket` → `notify_crew`, each calling the service and returning the fields it adds to the state. Call
# `crash_point(name)` first in each node. Compile with `checkpointer=saver`.

# %%
def build_graph(svc: M.Services, saver):
    def find_customer(state: Ticket) -> dict:
        crash_point("find_customer")
        return {"feeder_id": svc.call("find_customer", {"account": state["account"]})["feeder_id"]}

    def get_outage(state: Ticket) -> dict:
        crash_point("get_outage")
        return {"outage": svc.call("get_outage", {"feeder_id": state["feeder_id"]})["status"]}

    # BEGIN SOLUTION
    def create_ticket(state: Ticket) -> dict:
        crash_point("create_ticket")
        r = svc.call("create_ticket", {"account": state["account"], "feeder_id": state["feeder_id"], "summary": "customer reports no power"})
        return {"ticket_id": r["ticket_id"]}

    def notify_crew(state: Ticket) -> dict:
        crash_point("notify_crew")
        return {"notified": svc.call("notify_crew", {"ticket_id": state["ticket_id"]})["notified"]}

    g = StateGraph(Ticket)
    for name, fn in (("find_customer", find_customer), ("get_outage", get_outage),
                     ("create_ticket", create_ticket), ("notify_crew", notify_crew)):
        g.add_node(name, fn)
    g.add_edge(START, "find_customer")
    g.add_edge("find_customer", "get_outage")
    g.add_edge("get_outage", "create_ticket")
    g.add_edge("create_ticket", "notify_crew")
    g.add_edge("notify_crew", END)
    return g.compile(checkpointer=saver)
    # END SOLUTION


def reference_graph(svc, saver):
    def node(name, fn):
        def run(state):
            crash_point(name)
            return fn(state)
        return run
    steps = [("find_customer", lambda s: {"feeder_id": svc.call("find_customer", {"account": s["account"]})["feeder_id"]}),
             ("get_outage", lambda s: {"outage": svc.call("get_outage", {"feeder_id": s["feeder_id"]})["status"]}),
             ("create_ticket", lambda s: {"ticket_id": svc.call("create_ticket", {"account": s["account"], "feeder_id": s["feeder_id"],
                                                                                   "summary": "customer reports no power"})["ticket_id"]}),
             ("notify_crew", lambda s: {"notified": svc.call("notify_crew", {"ticket_id": s["ticket_id"]})["notified"]})]
    g = StateGraph(Ticket)
    for name, fn in steps:
        g.add_node(name, node(name, fn))
    g.add_edge(START, steps[0][0])
    for (a, _), (b, _) in zip(steps, steps[1:]):
        g.add_edge(a, b)
    g.add_edge(steps[-1][0], END)
    return g.compile(checkpointer=saver)


def saver_at(path):
    return SqliteSaver(sqlite3.connect(str(path), check_same_thread=False))


svc = M.Services(OUT / "svc_clean")
try:
    graph = build_graph(svc, saver_at(OUT / "checkpoints.db"))
except NotImplementedError:  # safety net
    graph = reference_graph(svc, saver_at(OUT / "checkpoints.db"))
    build_graph = reference_graph
final = graph.invoke({"account": REPORT_ACCOUNT}, {"configurable": {"thread_id": "S-4201"}})
print(final)
print("tickets:", svc.tickets())
assert final["notified"] and len(svc.tickets()) == 1

# %% [markdown]
# ## 2 · Crash mid-task and resume (6')
#
# The pod running Mubadir restarts after the ticket is created and before the crew is notified.
#
# ✏️ **Exercise** · Run the flow twice with a crash before `notify_crew`:
# - **restart**: after the crash, invoke again from the start on a new thread (what Mubadir did before);
# - **resume**: after the crash, invoke with `None` on the same thread.
#
# Count the tickets each way.

# %%
def tickets_after(mode: str) -> list[dict]:
    s = M.Services(OUT / f"svc_{mode}")
    g = build_graph(s, saver_at(OUT / f"checkpoints_{mode}.db"))
    CRASH["before"] = "notify_crew"
    try:
        g.invoke({"account": REPORT_ACCOUNT}, {"configurable": {"thread_id": "S-4202"}})
    except RuntimeError as e:
        print(f"[{mode}] crashed:", e)
    # BEGIN SOLUTION
    if mode == "restart":
        g.invoke({"account": REPORT_ACCOUNT}, {"configurable": {"thread_id": "S-4202-again"}})
    else:
        print(f"[{mode}] next step on the saved thread:", g.get_state({"configurable": {"thread_id": "S-4202"}}).next)
        g.invoke(None, {"configurable": {"thread_id": "S-4202"}})
    # END SOLUTION
    out = s.tickets()
    s.close()
    return out


results = {}
for mode in ("restart", "resume"):
    try:
        results[mode] = tickets_after(mode)
    except NotImplementedError:  # safety net: the reference recovery
        s = M.Services(OUT / f"svc_{mode}_ref")
        g = build_graph(s, saver_at(OUT / f"checkpoints_{mode}_ref.db"))
        CRASH["before"] = "notify_crew"
        try:
            g.invoke({"account": REPORT_ACCOUNT}, {"configurable": {"thread_id": "S-4202"}})
        except RuntimeError:
            pass
        g.invoke({"account": REPORT_ACCOUNT} if mode == "restart" else None,
                 {"configurable": {"thread_id": "S-4202-again" if mode == "restart" else "S-4202"}})
        results[mode] = s.tickets()
        s.close()
    print(mode, "->", results[mode])
assert len(results["restart"]) == 2 and len(results["resume"]) == 1 and results["resume"][0]["notified"]
K.check(True, "restart: two tickets, one never notified; resume: one ticket, notified")

# %% [markdown]
# 🔍 The restart left one ticket that no crew was told about. Which customer-facing promise does that break?

# %% [markdown]
# ## 3 · A retry after a timeout: two tickets (6')
#
# Now the agent itself. Its harness retries a tool call that times out (`retries_on_timeout: 2`). The ticket
# service commits the ticket and then fails to answer within 5 seconds.

# %%
flaky = M.Services(OUT / "svc_flaky", flaky_create=True)
r = M.run_session(f"No power at home. Account {REPORT_ACCOUNT}.", flaky, session_id="S-4203")
for e in r["events"]:
    if e["type"] in ("tool", "retry"):
        print(e["type"], e.get("tool"), e.get("args", {}).get("account", ""), "->", e.get("result", e.get("error")))
print("tickets:", flaky.tickets())
dupes = flaky.tickets()
flaky.close()

# %% [markdown]
# ✏️ **Exercise** · Explain in `WHY` (one sentence) why the retry created a second ticket, given that the first
# call failed.

# %%
try:
    # BEGIN SOLUTION
    WHY = "the timeout came after the ticket was committed, so the call failed for the caller but succeeded for the service, and the retry wrote again"
    # END SOLUTION
except NotImplementedError:  # safety net
    WHY = "a timeout does not say whether the write happened"
print(WHY)
assert len(dupes) == 2

# %% [markdown]
# ## 4 · An idempotency key: one ticket (7')
#
# An **idempotency key** names one intended write. The service stores the key with the ticket; a second call with
# the same key returns the first ticket instead of writing again. The key must be the same on every retry of the
# same intent, and different for a different intent.
#
# ✏️ **Exercise** · Write `KeyedServices`, a subclass of `M.Services` built with a `session_id`, whose `call`
# adds `idempotency_key` to `create_ticket` calls: a hash of the session id, the tool and its arguments. Run the
# flaky session again on an idempotent service.

# %%
class KeyedServices(M.Services):
    def __init__(self, folder, session_id: str, **kw):
        super().__init__(folder, **kw)
        self.session_id = session_id

    def call(self, name: str, args: dict) -> dict:
        # BEGIN SOLUTION
        if name == "create_ticket":
            args = dict(args, idempotency_key=K.short(K.sha256_json([self.session_id, name, args]), 16))
        return super().call(name, args)
        # END SOLUTION


fixed = KeyedServices(OUT / "svc_keyed", "S-4204", flaky_create=True, idempotent=True)
try:
    fixed.call("find_customer", {"account": REPORT_ACCOUNT})
except NotImplementedError:  # safety net: the reference key
    def keyed_call(self, name, args):
        if name == "create_ticket":
            args = dict(args, idempotency_key=K.short(K.sha256_json([self.session_id, name, args]), 16))
        return M.Services.call(self, name, args)
    KeyedServices.call = keyed_call
r = M.run_session(f"No power at home. Account {REPORT_ACCOUNT}.", fixed, session_id="S-4204")
for e in r["events"]:
    if e["type"] in ("tool", "retry"):
        print(e["type"], e.get("tool"), "->", e.get("result", e.get("error")))
print("tickets:", fixed.tickets())
assert len(fixed.tickets()) == 1 and "I opened ticket" in r["final"]
fixed.close()
K.check(True, "the retry returned the first ticket: one ticket, one crew")

# %% [markdown]
# 🔍 Why is the key built from the session and the arguments and not from the time of the call?

# %% [markdown]
# ## ✱ Stretch · A second process
#
# The checkpoint lives in SQLite, not in the notebook's memory. Crash a new thread before `notify_crew`, then read
# its saved state from a separate Python process and print the ticket it already holds.

# %%
try:
    # BEGIN SOLUTION
    s2 = M.Services(OUT / "svc_second")
    g2 = build_graph(s2, saver_at(OUT / "checkpoints_second.db"))
    CRASH["before"] = "notify_crew"
    try:
        g2.invoke({"account": REPORT_ACCOUNT}, {"configurable": {"thread_id": "S-4205"}})
    except RuntimeError as e:
        print("crashed:", e)
    code = ("import sqlite3, sys\nfrom langgraph.checkpoint.sqlite import SqliteSaver\n"
            "saver = SqliteSaver(sqlite3.connect(sys.argv[1]))\n"
            "t = saver.get_tuple({'configurable': {'thread_id': 'S-4205'}})\n"
            "print('second process sees:', {k: v for k, v in t.checkpoint['channel_values'].items() if k in ('account', 'ticket_id', 'notified')})\n")
    (OUT / "read_checkpoint.py").write_text(code, encoding="utf-8")
    out = subprocess.run([sys.executable, str(OUT / "read_checkpoint.py"), str(OUT / "checkpoints_second.db")],
                         capture_output=True, text=True, timeout=120)
    print(out.stdout.strip() or out.stderr[-500:])
    s2.close()
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. After a crash, why does resuming from the checkpoint not open a second ticket?
#    <details><summary>Answer</summary>The checkpoint saved the state after `create_ticket`, with the ticket id;
#    resuming runs only the steps after it.</details>
# 2. A checkpointer is in place. Why can a retry still create two tickets?
#    <details><summary>Answer</summary>The retry happens inside one step: the service committed and the answer was
#    lost. Only the service can recognise the repeat, through a key.</details>
# 3. Which of Mubadir's tools need an idempotency key?
#    <details><summary>Answer</summary>The ones that write: create_ticket, notify_crew (a crew paged twice), close_report
#    and update_customer_record. Reads can be retried freely.</details>
#
# ## Carry forward
#
# The capstone's agent incident is a duplicate write: the key and the checkpoint are its fix.
