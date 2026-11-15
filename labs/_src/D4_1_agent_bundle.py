# %% [markdown]
# # Lab 4.1 · Mubadir as one versioned bundle
#
# Day 4 · Session 1 (An agent is a bundle) · 25 min.
#
# Mubadir, Wahaj's outage-ticket agent, is a model in a loop. Its behaviour depends on four files that four people
# edit: the prompt, the tool schemas, the harness settings (steps, retries, timeouts) and the sandbox policy (which
# tools, which fields). You package them as one bundle with a content version, release it to a folder nobody
# edits, change one tool schema and watch the version move, and run the agent from the released bundle so every
# session log names the bundle it ran.
#
# **Reference state.** `data/mubadir/` (prompt.md, tools.json, harness.yaml, sandbox.yaml), the services in
# `mubadir.py` and the scripted stand-in model, which follows the prompt's procedure.
#
# **Tasks**
# - [ ] 1 · What changes Mubadir's behaviour (5')
# - [ ] 2 · Build the bundle and its version (8')
# - [ ] 3 · Change one tool schema (6')
# - [ ] 4 · Run the agent from the bundle (6')
# - [ ] ✱ Stretch · Refuse to start when the running bundle is not the released one

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
import shutil

import mubadir as M

OUT = K.lab_dir("D4_1")
SOURCE = K.DATA / "mubadir"
for p in sorted(SOURCE.iterdir()):
    print(f"--- {p.name}\n{p.read_text(encoding='utf-8')[:300]}")

# %% [markdown]
# ## 1 · What changes Mubadir's behaviour (5')
#
# Three things are easy to mix up:
#
# - the **harness**: the loop that calls the model, runs tools, retries and stops (code plus `harness.yaml`);
# - the **sandbox**: what the agent may touch (`sandbox.yaml`: allowed tools, readable fields, no network);
# - the **session log**: what happened in one session. It is produced by a run, never part of a release.
#
# ✏️ **Exercise** · Fill `ROLES`: for each file of the bundle, one of `"prompt"`, `"tools"`, `"harness"`,
# `"sandbox"`. Then answer in `NOT_IN_BUNDLE` which of these is not part of the bundle: the session log, the
# customer database, the model's weights. (All three.)

# %%
try:
    # BEGIN SOLUTION
    ROLES = {"prompt.md": "prompt", "tools.json": "tools", "harness.yaml": "harness", "sandbox.yaml": "sandbox"}
    NOT_IN_BUNDLE = ["session log", "customer database", "model weights"]
    # END SOLUTION
except NotImplementedError:  # safety net
    ROLES = {"prompt.md": "prompt", "tools.json": "tools", "harness.yaml": "harness", "sandbox.yaml": "sandbox"}
    NOT_IN_BUNDLE = ["session log", "customer database", "model weights"]
settings = M.load_settings(SOURCE)
print("model:", settings["harness"]["model"], "| max steps:", settings["harness"]["max_steps"],
      "| retries:", settings["harness"]["retries_on_timeout"], "| allowed tools:", settings["sandbox"]["allowed_tools"])
assert set(ROLES) == {p.name for p in SOURCE.iterdir()}

# %% [markdown]
# 🔍 The bundle names the model `steady`, an alias at the provider. What else must the session log record so a
# provider update shows up? (The served model name, as in Lab 1.1.)

# %% [markdown]
# ## 2 · Build the bundle and its version (8')
#
# ✏️ **Exercise** · Write `bundle_version(folder)`: the SHA-256 of a JSON list of `[file name, SHA-256 of its
# bytes]` for the four files in name order, returned as `"mubadir-" + K.short(hash)`. Then write `release(folder)`:
# copy the four files to `artifacts/D4_1/releases/<version>/` with a `manifest.json` (version, files and their
# hashes, released_by). In production the release store refuses overwrites (an object store with versioning or
# object lock); here the folder name is the version.

# %%
FILES = sorted(ROLES)


def bundle_version(folder) -> str:
    # BEGIN SOLUTION
    folder = Path(folder)
    parts = [[name, K.sha256_file(folder / name)] for name in FILES]
    return "mubadir-" + K.short(K.sha256_json(parts))
    # END SOLUTION


def release(folder, released_by: str = "Dhafer Al-Hazzani") -> Path:
    # BEGIN SOLUTION
    folder = Path(folder)
    version = bundle_version(folder)
    target = OUT / "releases" / version
    target.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in FILES:
        shutil.copyfile(folder / name, target / name)
        files[name] = K.sha256_file(target / name)
    K.write_json(target / "manifest.json", {"version": version, "files": files, "released_by": released_by})
    return target
    # END SOLUTION


def reference_version(folder):
    return "mubadir-" + K.short(K.sha256_json([[n, K.sha256_file(Path(folder) / n)] for n in FILES]))


def reference_release(folder, released_by="Dhafer Al-Hazzani"):
    v = reference_version(folder)
    target = OUT / "releases" / v
    target.mkdir(parents=True, exist_ok=True)
    for n in FILES:
        shutil.copyfile(Path(folder) / n, target / n)
    K.write_json(target / "manifest.json", {"version": v, "files": {n: K.sha256_file(target / n) for n in FILES}, "released_by": released_by})
    return target


try:
    v1 = bundle_version(SOURCE)
    released = release(SOURCE)
except NotImplementedError:  # safety net
    bundle_version, release = reference_version, reference_release
    v1 = bundle_version(SOURCE)
    released = release(SOURCE)
print(v1, "->", released.relative_to(K.LABS))
print(json.dumps(K.read_json(released / "manifest.json"), indent=1))
assert bundle_version(released) == v1

# %% [markdown]
# ## 3 · Change one tool schema (6')
#
# Customer care wants tickets to carry the customer's words. A developer adds a `customer_words` property to
# `create_ticket` in a working copy.
#
# ✏️ **Exercise** · Make a working copy in `artifacts/D4_1/work/`, add the property to `create_ticket`'s schema,
# and compute the new version. Then list which files differ between the two manifests.

# %%
work = OUT / "work"
shutil.copytree(SOURCE, work, dirs_exist_ok=True)
try:
    # BEGIN SOLUTION
    tools = json.loads((work / "tools.json").read_text(encoding="utf-8"))
    ct = next(t for t in tools if t["name"] == "create_ticket")
    ct["parameters"]["properties"]["customer_words"] = {"type": "string", "description": "the customer's own words, without personal data"}
    (work / "tools.json").write_text(json.dumps(tools, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    # END SOLUTION
except NotImplementedError:  # safety net
    tools = json.loads((work / "tools.json").read_text(encoding="utf-8"))
    next(t for t in tools if t["name"] == "create_ticket")["parameters"]["properties"]["customer_words"] = {"type": "string"}
    (work / "tools.json").write_text(json.dumps(tools, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
v2 = bundle_version(work)
changed = [n for n in FILES if K.sha256_file(work / n) != K.sha256_file(released / n)]
print(v1, "->", v2, "| changed:", changed)
assert v2 != v1 and changed == ["tools.json"]

# %% [markdown]
# 🔍 Nobody touched the prompt, yet the model now sees a different tool list. Why is that a behaviour change that
# needs the replay suite of Lab 4.3 before release?

# %% [markdown]
# ## 4 · Run the agent from the bundle (6')
#
# ✏️ **Exercise** · Run one report through Mubadir with the **released** folder's settings and the bundle version
# as `version`, and save the session log with `M.save_recording(..., meta={"bundle": v1})`. The customer's feeder
# has no known outage, so the agent should open a ticket and notify the crew.

# %%
report = "My power went off twenty minutes ago. Account ACC-40000137."
svc = M.Services(OUT / "svc")
try:
    # BEGIN SOLUTION
    result = M.run_session(report, svc, settings=M.load_settings(released), session_id="S-4101", version=v1)
    log_path = M.save_recording(result, OUT / "sessions" / "S-4101.json", meta={"bundle": v1})
    # END SOLUTION
except NotImplementedError:  # safety net
    result = M.run_session(report, svc, settings=M.load_settings(released), session_id="S-4101", version=v1)
    log_path = M.save_recording(result, OUT / "sessions" / "S-4101.json", meta={"bundle": v1})
for e in result["events"]:
    if e["type"] == "tool":
        print(f"step {e['step']}: {e['tool']}({e['args']}) -> {e['result']}")
print("final:", result["final"])
print("tickets:", svc.tickets())
svc.close()
assert K.read_json(log_path)["bundle"] == v1 and "I opened ticket" in result["final"]
K.check(True, f"session S-4101 ran bundle {v1} and its log says so")

# %% [markdown]
# ## ✱ Stretch · Refuse a bundle that is not the released one
#
# Write `start(folder, released_version)` that computes the folder's version and raises `RuntimeError` if it is
# not the released one. Try it on the working copy.

# %%
try:
    # BEGIN SOLUTION
    def start(folder, released_version: str) -> dict:
        v = bundle_version(folder)
        if v != released_version:
            raise RuntimeError(f"bundle {v} is not the released {released_version}: release it first")
        return M.load_settings(folder)

    start(released, v1)
    try:
        start(work, v1)
    except RuntimeError as e:
        print("refused:", e)
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. Why is the session log not part of the bundle?
#    <details><summary>Answer</summary>The bundle is what you release; the log is what one run produced. Logs
#    change every second and hold customer data; they are kept, redacted and deleted under their own rules.</details>
# 2. A teammate raises `max_steps` from 10 to 30 in the harness settings. Is that a new release?
#    <details><summary>Answer</summary>Yes: the version moves, because harness settings change behaviour (and cost)
#    as much as the prompt does.</details>
# 3. Why run from the released folder instead of the working copy?
#    <details><summary>Answer</summary>So that what runs is exactly what was versioned and tested; an edit in place
#    would change behaviour without a new version.</details>
#
# ## Carry forward
#
# The bundle version goes into Day 1's release manifest as Mubadir's part, and into every session log. Lab 4.4's
# kill switch stops one bundle version.
