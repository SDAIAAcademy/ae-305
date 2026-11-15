"""Shared helpers for the AE-305 labs (Wahaj Electricity Distribution Company).

    import opskit as K

Sections: settings and paths; hashing; the fault-risk model (data, training, evaluation); the model registry
(MLflow); a small pipeline runner; the delivery checker and simulator; the rollout simulator; language model
calls (a free hosted model, or the scripted stand-in); prices and the gateway.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
import shutil
import sqlite3
import sys
import time
import zlib
from dataclasses import dataclass, field
from pathlib import Path

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
os.environ.setdefault("MLFLOW_ENABLE_LOGGED_MODEL_CREATION", "true")
os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")

for _stream in (sys.stdout, sys.stderr):  # a Windows console prints the check marks too
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# ------------------------------------------------------------------ settings and paths
LABS = Path(__file__).resolve().parent
DATA = LABS / "data"
ART = LABS / "artifacts"
try:
    from dotenv import load_dotenv
    load_dotenv(LABS / ".env")
except ImportError:  # python-dotenv is optional
    pass

QUICK = os.environ.get("OPS_QUICK", "0") == "1"
REGIONS = {"RIM": "Al-Rimal", "HAD": "Al-Hadba", "SAH": "Al-Sahil", "WAD": "Al-Wadi", "JAB": "Al-Jabal", "NAK": "Al-Nakheel"}
MONTHS = ["2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04",
          "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10"]
FEATURES = ["age_years", "length_km", "overhead_share", "vegetation", "coast_km",
            "peak_temp_c", "dust_index", "load_peak_pct", "faults_90d"]


def pick(full, quick):
    """The full value, or the small one in quick mode (OPS_QUICK=1)."""
    return quick if QUICK else full


def check(ok: bool, what: str) -> bool:
    print(("✅ " if ok else "❌ ") + what)
    return bool(ok)


def lab_dir(name: str, reset: bool = True) -> Path:
    """A fresh working folder under labs/artifacts/ for one lab."""
    p = ART / name
    if reset and p.exists():
        shutil.rmtree(p, ignore_errors=True)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_json(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path, obj) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def save_reference(name: str, value):
    """Write a safety-net reference file. Only the course maintainers' solution run sets OPS_WRITE_REFERENCE=1."""
    if os.environ.get("OPS_WRITE_REFERENCE") == "1":
        write_json(DATA / "reference" / f"{name}.json", value)


def reference(name: str):
    """A supplied reference result (data/reference/<name>.json), for the safety-net cells."""
    return read_json(DATA / "reference" / f"{name}.json")


# ------------------------------------------------------------------ hashing
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path) -> str:
    """Hash of a file's bytes, with line endings normalised so Windows and Linux checkouts agree."""
    return sha256_bytes(Path(path).read_bytes().replace(b"\r\n", b"\n"))


def sha256_json(obj) -> str:
    return sha256_bytes(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def short(h: str, n: int = 12) -> str:
    return h[:n]


# ------------------------------------------------------------------ the fault-risk model
TRAIN_PARAMS = {"max_iter": pick(150, 60), "learning_rate": 0.05, "max_leaf_nodes": 15, "recent_weight": 4, "random_state": 305}


def load_batch(month: str, first_cut: bool = False):
    import pandas as pd
    if first_cut:
        return pd.read_csv(DATA / "late_labels" / f"feeders_{month}_first_cut.csv")
    return pd.read_csv(DATA / "batches" / f"feeders_{month}.csv")


def is_holdout(df):
    """A quarter of the feeders (number divisible by 4) never enter training: they are the gate's holdout."""
    return df["feeder_id"].str[2:].astype(int) % 4 == 0


def design_matrix(df, features=FEATURES):
    x = df[list(features)].copy()
    for r in REGIONS:
        x[f"region_{r}"] = (df["region"] == r).astype(int)
    return x


def training_frame(months: list[str], first_cut_months: tuple = ()):
    """Training rows of the given months (holdout feeders removed), in a fixed order."""
    import pandas as pd
    df = pd.concat([load_batch(m, first_cut=m in first_cut_months) for m in months], ignore_index=True)
    df = df[~is_holdout(df)].sort_values(["month", "feeder_id"]).reset_index(drop=True)
    return df


def train_fault_model(df, features=FEATURES, params: dict | None = None):
    """Train the fault-risk classifier. The newest month weighs `recent_weight` times the others."""
    import numpy as np
    from sklearn.ensemble import HistGradientBoostingClassifier
    p = dict(TRAIN_PARAMS, **(params or {}))
    w = np.where(df["month"] == df["month"].max(), float(p["recent_weight"]), 1.0)
    model = HistGradientBoostingClassifier(max_iter=p["max_iter"], learning_rate=p["learning_rate"],
                                           max_leaf_nodes=p["max_leaf_nodes"], early_stopping=False,
                                           random_state=p["random_state"])
    model.fit(design_matrix(df, features), df["fault_30d"], sample_weight=w)
    model.feature_list_ = list(features)
    return model


def predict_risk(model, df):
    return model.predict_proba(design_matrix(df, getattr(model, "feature_list_", FEATURES)))[:, 1]


def holdout_frame(month: str = "2026-08"):
    df = load_batch(month)
    return df[is_holdout(df)].sort_values("feeder_id").reset_index(drop=True)


def code_hash() -> str:
    """The version of the training code: a hash of the functions that build the model."""
    src = "".join(inspect.getsource(f) for f in (design_matrix, training_frame, train_fault_model))
    return short(sha256_bytes(src.encode("utf-8")))


def snapshot(df, store) -> tuple[str, Path]:
    """Write a training frame into a content-addressed store, as DVC or lakeFS would: the name is the hash."""
    store = Path(store)
    store.mkdir(parents=True, exist_ok=True)
    data = df.to_csv(index=False, lineterminator="\n").encode("utf-8")
    h = sha256_bytes(data)
    path = store / f"{h[:2]}" / f"{h}.csv"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        path.write_bytes(data)
    return h, path


# ------------------------------------------------------------------ the model registry (MLflow)
def mlflow_client(folder):
    """An MLflow tracking store and registry in a local folder (SQLite plus an artifact folder)."""
    import mlflow
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    uri = "sqlite:///" + (folder / "mlflow.db").as_posix()
    mlflow.set_tracking_uri(uri)
    mlflow.set_registry_uri(uri)
    exp = mlflow.get_experiment_by_name("fault-risk")
    if exp is None:
        mlflow.create_experiment("fault-risk", artifact_location=(folder / "mlruns").as_uri())
    mlflow.set_experiment("fault-risk")
    return mlflow.MlflowClient(tracking_uri=uri, registry_uri=uri)


def register_fault_model(client, model, *, months, features, params, snapshot_hash, metrics: dict,
                         name="fault-risk", author="Lamya Al-Muqbil", note="", first_cut_months=()):
    """Log one trained model with its lineage and register it as a new version. Returns the version number."""
    import logging
    import warnings
    import mlflow
    import mlflow.sklearn
    logging.getLogger("mlflow").setLevel(logging.ERROR)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with mlflow.start_run(run_name=note or f"train {months[0]}..{months[-1]}") as run:
            mlflow.log_params({**{k: v for k, v in params.items()}, "months": ",".join(months),
                               "features": ",".join(features), "first_cut_months": ",".join(first_cut_months)})
            mlflow.log_metrics({k: float(v) for k, v in metrics.items()})
            mlflow.set_tags({"data_snapshot": snapshot_hash, "code_hash": code_hash(), "author": author, "note": note})
            info = mlflow.sklearn.log_model(model, name="model", registered_model_name=name,
                                            input_example=None, serialization_format="pickle")
    versions = client.search_model_versions(f"name='{name}' and run_id='{run.info.run_id}'")
    v = max(int(x.version) for x in versions)
    client.set_model_version_tag(name, str(v), "data_snapshot", snapshot_hash)
    client.set_model_version_tag(name, str(v), "code_hash", code_hash())
    client.set_model_version_tag(name, str(v), "months", ",".join(months))
    if note:
        client.update_model_version(name, str(v), description=note)
    return v


def auc_by_region(y, p, regions) -> dict:
    """AUC overall and in each region."""
    import numpy as np
    from sklearn.metrics import roc_auc_score
    y, p, regions = np.asarray(y), np.asarray(p), np.asarray(regions)
    out = {"all": round(float(roc_auc_score(y, p)), 3)}
    for r in REGIONS:
        s = regions == r
        out[r] = round(float(roc_auc_score(y[s], p[s])), 3)
    return out


REGISTRY_PLAN = {
    # version: (months, first-cut months, note)
    1: (MONTHS[:6], (), "first model, winter and spring"),
    2: (MONTHS[:8], (), "retrained with early summer"),
    3: (MONTHS[:9], (), "champion since August: November to July"),
}


def seed_registry(folder, versions=(1, 2, 3), challengers: bool = False, quiet: bool = True):
    """Build the reference registry the labs start from: Lamya's three versions (v3 is the champion) and,
    with challengers=True, the two October challengers of Lab 1.4. Returns the MLflow client."""
    folder = Path(folder)
    client = mlflow_client(folder)
    store = folder / "snapshots"
    hold = holdout_frame("2026-07")
    registered = {}
    for v in versions:
        months, fc, note = REGISTRY_PLAN[v]
        df = training_frame(months, fc)
        h, _ = snapshot(df, store)
        model = train_fault_model(df, FEATURES, TRAIN_PARAMS)
        m = auc_by_region(hold["fault_30d"], predict_risk(model, hold), hold["region"])
        registered[v] = register_fault_model(client, model, months=months, features=FEATURES, params=TRAIN_PARAMS,
                                             snapshot_hash=h, metrics={"auc_holdout_2026_07": m["all"]}, note=note)
        if not quiet:
            print(f"registered fault-risk v{v}: {note}")
    if 3 in versions:
        client.set_registered_model_alias("fault-risk", "champion", str(registered[3]))
    if challengers:
        window = MONTHS[3:10]  # February to the drifted August
        for alias, fc, author, note in (("challenger-a", ("2026-08",), "scheduled retrain script", "October retrain on the first cut of August"),
                                        ("challenger-b", (), "Lamya Al-Muqbil", "October retrain on the complete August batch")):
            df = training_frame(window, fc)
            h, _ = snapshot(df, store)
            model = train_fault_model(df, FEATURES, TRAIN_PARAMS)
            v = register_fault_model(client, model, months=window, features=FEATURES, params=TRAIN_PARAMS,
                                     snapshot_hash=h, metrics={}, author=author, note=note, first_cut_months=fc)
            client.set_registered_model_alias("fault-risk", alias, str(v))
            if not quiet:
                print(f"registered fault-risk v{v} as {alias}: {note}")
    return client


def load_registered(client, alias: str = "champion", name: str = "fault-risk"):
    import mlflow.sklearn
    mv = client.get_model_version_by_alias(name, alias)
    model = mlflow.sklearn.load_model(f"models:/{name}@{alias}")
    model.feature_list_ = mv.tags.get("features", "").split(",") if mv.tags.get("features") else \
        client.get_run(mv.run_id).data.params["features"].split(",")
    return mv, model


# ------------------------------------------------------------------ a small pipeline runner
class StopRun(Exception):
    """Raised by a step to stop the run on purpose (a failed validation, a failed gate)."""


@dataclass
class RunLog:
    flow: str
    run_id: str
    trigger: str
    steps: list = field(default_factory=list)
    status: str = "running"
    reason: str = ""

    def as_dict(self):
        return {"flow": self.flow, "run_id": self.run_id, "trigger": self.trigger, "status": self.status,
                "reason": self.reason, "steps": self.steps}


def run_flow(name: str, steps: list, ctx: dict, trigger: str = "manual", log_dir=None) -> RunLog:
    """Run steps in order, as an orchestrator (Prefect, Airflow) would: each step gets the context and returns
    a dict merged into it. A StopRun ends the run as "stopped"; any other exception as "failed". The run log
    is written to log_dir/<run_id>.json with the duration of each step."""
    run_id = f"{name}-{ctx.get('batch', 'run')}-{short(sha256_json([name, trigger, ctx.get('batch')]), 6)}"
    log = RunLog(name, run_id, trigger)
    for step_name, fn in steps:
        t0 = time.perf_counter()
        try:
            out = fn(ctx) or {}
            ctx.update(out)
            log.steps.append({"step": step_name, "status": "ok", "seconds": round(time.perf_counter() - t0, 2),
                              "output": {k: v for k, v in out.items() if isinstance(v, (str, int, float, bool, list, dict))}})
        except StopRun as e:
            log.steps.append({"step": step_name, "status": "stopped", "seconds": round(time.perf_counter() - t0, 2), "reason": str(e)})
            log.status, log.reason = "stopped", f"{step_name}: {e}"
            break
        except Exception as e:  # noqa: BLE001
            log.steps.append({"step": step_name, "status": "failed", "seconds": round(time.perf_counter() - t0, 2), "reason": repr(e)})
            log.status, log.reason = "failed", f"{step_name}: {e!r}"
            break
    else:
        log.status = "succeeded"
    if log_dir:
        write_json(Path(log_dir) / f"{run_id}.json", log.as_dict())
    return log


def print_run(log: RunLog):
    print(f"{log.run_id} [{log.trigger}] -> {log.status.upper()}" + (f" ({log.reason})" if log.reason else ""))
    for s in log.steps:
        print(f"   {s['status']:8} {s['step']:<16} {s['seconds']:>6.2f} s  {s.get('reason', '')}")


# ------------------------------------------------------------------ delivery: check and simulate a workflow
def check_workflow(text: str) -> list[tuple[bool, str]]:
    """The rules of Lab 2.1, checked on a GitHub Actions workflow. Returns (passed, rule) pairs."""
    import yaml
    wf = yaml.safe_load(text)
    on = wf.get("on", wf.get(True, {}))  # YAML reads a bare `on:` key as True
    jobs = wf.get("jobs", {})
    res = []
    res.append((isinstance(on, dict) and "main" in str(on.get("push", {})), "runs on a push (merge) to main"))
    build = [j for j, v in jobs.items() if "outputs" in v and "digest" in json.dumps(v.get("outputs", {}))]
    res.append((bool(build), "a build job publishes the image digest as an output"))
    envs = {j: (v.get("environment") if isinstance(v.get("environment"), str) else (v.get("environment") or {}).get("name"))
            for j, v in jobs.items()}
    stg = [j for j, e in envs.items() if e == "staging"]
    prd = [j for j, e in envs.items() if e == "production"]
    res.append((len(stg) == 1, "one job deploys to the staging environment"))
    res.append((len(prd) == 1, "one job deploys to the production environment (its reviewers are the approval step)"))

    def needs(j):
        n = jobs[j].get("needs", [])
        return [n] if isinstance(n, str) else list(n)
    if stg and prd:
        res.append((stg[0] in needs(prd[0]), "production needs staging"))
        res.append((bool(build) and build[0] in needs(stg[0]), "staging needs the build"))
    body = json.dumps(jobs)
    res.append((":latest" not in body, "no deploy uses a moving tag such as :latest"))
    deploy_steps = [json.dumps(jobs[j].get("steps", [])) for j in stg + prd]
    res.append((bool(deploy_steps) and all("docker build" not in s for s in deploy_steps),
                "staging and production deploy the built digest, they do not build again"))
    res.append((bool(stg) and "smoke" in json.dumps(jobs[stg[0]].get("steps", [])).lower(), "staging runs a smoke check before production"))
    return res


def simulate_release(text: str, approvals: dict, commit: str = "a1b2c3d", log_dir=None) -> list[dict]:
    """Walk the workflow's jobs in dependency order, as the runner would. Build produces a digest from the
    commit; a job with an environment needs an approval when approvals names a reviewer for it (production);
    each deploy writes environments/<env>.json. Returns the deployment log."""
    import yaml
    wf = yaml.safe_load(text)
    jobs = wf["jobs"]
    order, done = [], set()
    while len(order) < len(jobs):
        progressed = False
        for j, v in jobs.items():
            n = v.get("needs", [])
            n = [n] if isinstance(n, str) else list(n)
            if j not in done and all(x in done for x in n):
                order.append(j)
                done.add(j)
                progressed = True
        if not progressed:
            raise ValueError("the jobs' needs form a cycle")
    log, digest = [], None
    root = Path(log_dir) if log_dir else lab_dir("D2_1/sim")
    for j in order:
        v = jobs[j]
        env = v.get("environment")
        env = env if isinstance(env, str) else (env or {}).get("name")
        steps = json.dumps(v.get("steps", []))
        if "docker build" in steps:
            digest = "sha256:" + sha256_bytes(f"nabd@{commit}".encode())[:16]
            log.append({"job": j, "event": "built", "digest": digest})
        if env:
            if env in approvals and not approvals[env]:
                log.append({"job": j, "event": "waiting for approval", "environment": env})
                break
            if env in approvals:
                log.append({"job": j, "event": "approved", "environment": env, "by": approvals[env]})
            write_json(root / "environments" / f"{env}.json", {"environment": env, "digest": digest, "commit": commit})
            log.append({"job": j, "event": "deployed", "environment": env, "digest": digest})
            if "smoke" in steps.lower():
                log.append({"job": j, "event": "smoke check passed", "environment": env})
    return log


# ------------------------------------------------------------------ the rollout simulator (Lab 2.3)
def in_canary(i: int, weight: int) -> bool:
    """A request goes to the canary when its stable hash falls below the weight (sticky routing)."""
    return zlib.crc32(f"req-{i}".encode()) % 100 < weight


def run_rollout(traffic: list[dict], steps: list[dict], analyse, start_min: float = 0.0) -> list[dict]:
    """Replay traffic through canary steps in the Argo Rollouts style.

    steps: [{"setWeight": 5}, {"pause": 30}, {"setWeight": 25}, {"pause": 30}, ...] (pause in minutes of traffic).
    At the end of every pause, analyse(window) is called on the requests the canary served during that pause;
    it returns "pass", "fail" or "inconclusive". "fail" aborts: the weight returns to 0 and the rollout stops.
    "inconclusive" extends the pause once by the same length. Returns the rollout log."""
    log, weight, t = [], 0, start_min
    traffic = sorted(traffic, key=lambda r: r["t_min"])
    for step in steps:
        if "setWeight" in step:
            weight = step["setWeight"]
            log.append({"t_min": round(t, 1), "event": f"setWeight {weight}"})
            continue
        length = step["pause"]
        for attempt in (1, 2):
            end = t + length
            window = [dict(r["canary"], i=r["i"], lang=r["lang"], t_min=r["t_min"], stable=r["stable"])
                      for r in traffic if t <= r["t_min"] < end and in_canary(r["i"], weight)]
            verdict, why = analyse(window)
            log.append({"t_min": round(end, 1), "event": f"analysis at weight {weight}", "n": len(window),
                        "verdict": verdict, "why": why})
            t = end
            if verdict != "inconclusive" or attempt == 2:
                break
        if verdict == "fail":
            log.append({"t_min": round(t, 1), "event": "abort: rolled back to stable", "why": why})
            return log
        if verdict == "inconclusive":
            log.append({"t_min": round(t, 1), "event": "paused: still inconclusive, waiting for a person"})
            return log
    log.append({"t_min": round(t, 1), "event": "promoted: canary is the new stable"})
    return log


def p95(values) -> float:
    v = sorted(values)
    if not v:
        return float("nan")
    return float(v[min(len(v) - 1, int(math.ceil(0.95 * len(v))) - 1)])


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 3), round(c + h, 3))


# ------------------------------------------------------------------ language model calls
OPENROUTER = "https://openrouter.ai/api/v1"
LIVE_MODELS = {  # model names in a release -> a free hosted model; change them in .env
    "steady": os.environ.get("OPS_MODEL_STEADY", "google/gemma-4-31b-it:free"),
    "swift": os.environ.get("OPS_MODEL_SWIFT", "google/gemma-4-26b-a4b-it:free"),
}
STANDINS: dict = {}  # system-prompt prefix -> function(messages, tools, persona); nabd.py and mubadir.py register theirs


def register_standin(prompt_prefix: str, fn):
    """Route scripted calls whose system prompt starts with prompt_prefix to fn(messages, tools, persona)."""
    STANDINS[prompt_prefix] = fn
_live_ok: bool | None = None


def live() -> bool:
    """True when a working OpenRouter key is set and OPS_MODEL is not 'scripted'."""
    global _live_ok
    if os.environ.get("OPS_MODEL", "") == "scripted" or not os.environ.get("OPENROUTER_API_KEY"):
        return False
    if _live_ok is None:
        try:  # the key endpoint answers only for a valid key
            import urllib.request
            req = urllib.request.Request(OPENROUTER + "/key", headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]})
            with urllib.request.urlopen(req, timeout=15) as r:
                _live_ok = r.status == 200
        except Exception as e:  # noqa: BLE001
            print("the OpenRouter key did not work, using the scripted stand-in model:", type(e).__name__)
            _live_ok = False
    return _live_ok


def resolve(model: str) -> str:
    """The model actually called for a release's model name."""
    if model.startswith("scripted/"):
        return model
    return LIVE_MODELS.get(model, model) if live() else f"scripted/{model}"


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chat(messages: list[dict], model: str, tools: list | None = None, temperature: float = 0.0) -> dict:
    """One model call. Returns {"content", "tool_calls": [{"name", "args"}], "model", "usage", "latency_ms"}."""
    name = resolve(model)
    t0 = time.perf_counter()
    if name.startswith("scripted/"):
        system = messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        fn = next((f for prefix, f in STANDINS.items() if system.startswith(prefix)), None)
        if fn is None:
            raise RuntimeError("no scripted stand-in for this system prompt; import nabd or mubadir first")
        reply = fn(messages, tools or [], name.split("/", 1)[1])
    else:
        from openai import OpenAI
        client = OpenAI(base_url=OPENROUTER, api_key=os.environ["OPENROUTER_API_KEY"])
        kw = {"tools": [{"type": "function", "function": {k: t[k] for k in ("name", "description", "parameters")}} for t in tools]} if tools else {}
        r = client.chat.completions.create(model=name, messages=messages, temperature=temperature, **kw)
        m = r.choices[0].message
        calls = [{"name": c.function.name, "args": json.loads(c.function.arguments or "{}")} for c in (m.tool_calls or [])]
        reply = {"content": m.content or "", "tool_calls": calls, "model": r.model,
                 "usage": {"input_tokens": r.usage.prompt_tokens, "output_tokens": r.usage.completion_tokens}}
    reply.setdefault("model", name)
    reply.setdefault("usage", {"input_tokens": sum(estimate_tokens(str(m.get("content", ""))) for m in messages),
                               "output_tokens": estimate_tokens(reply.get("content", "") or json.dumps(reply.get("tool_calls")))})
    reply["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return reply


# ------------------------------------------------------------------ prices and the gateway
def prices() -> dict:
    return read_json(DATA / "prices.json")


def token_cost(input_tokens: int, output_tokens: int, cached_input_tokens: int = 0, p: dict | None = None) -> float:
    p = p or prices()
    fresh = input_tokens - cached_input_tokens
    return (fresh * p["input_per_million_tokens"] + cached_input_tokens * p["cached_input_per_million_tokens"]
            + output_tokens * p["output_per_million_tokens"]) / 1e6


class LimitExceeded(Exception):
    """Raised by the gateway when a call would break a limit."""


class SessionStore:
    """Durable session records in SQLite: a stopped agent loses nothing."""

    def __init__(self, path):
        self.db = sqlite3.connect(str(path))
        self.db.execute("create table if not exists sessions (id text primary key, version text, status text, "
                        "steps int, spend real, messages text, note text)")
        self.db.commit()

    def save(self, sid, version, status, steps, spend, messages, note=""):
        self.db.execute("insert or replace into sessions values (?,?,?,?,?,?,?)",
                        (sid, version, status, steps, spend, json.dumps(messages, ensure_ascii=False), note))
        self.db.commit()

    def get(self, sid):
        r = self.db.execute("select * from sessions where id=?", (sid,)).fetchone()
        if not r:
            return None
        return {"id": r[0], "version": r[1], "status": r[2], "steps": r[3], "spend": r[4], "messages": json.loads(r[5]), "note": r[6]}

    def all(self):
        return [self.get(r[0]) for r in self.db.execute("select id from sessions order by id")]

    def close(self):
        self.db.close()


class Gateway:
    """A model gateway in one process: every model call of every agent session passes through `call`.

    policy(state) -> None or a reason string; state holds the session's steps and spend, the day's spend and the
    version. A reason stops the call (LimitExceeded). `kill(version)` stops every session of an agent version."""

    def __init__(self, policy=None):
        self.policy = policy or (lambda state: None)
        self.sessions: dict = {}
        self.day_spend = 0.0
        self.killed: set = set()
        self.events: list = []

    def kill(self, version: str, by: str):
        self.killed.add(version)
        self.events.append({"event": "kill switch on", "version": version, "by": by})

    def call(self, session_id: str, version: str, messages: list, model: str, tools=None) -> dict:
        s = self.sessions.setdefault(session_id, {"steps": 0, "spend": 0.0, "version": version})
        if version in self.killed:
            self.events.append({"event": "refused: kill switch", "session": session_id})
            raise LimitExceeded(f"kill switch on for {version}")
        state = {"session_steps": s["steps"], "session_spend": s["spend"], "day_spend": self.day_spend, "version": version}
        why = self.policy(state)
        if why:
            self.events.append({"event": "refused", "session": session_id, "why": why})
            raise LimitExceeded(why)
        reply = chat(messages, model, tools)
        cost = token_cost(reply["usage"]["input_tokens"], reply["usage"]["output_tokens"])
        s["steps"] += 1
        s["spend"] += cost
        self.day_spend += cost
        return reply
