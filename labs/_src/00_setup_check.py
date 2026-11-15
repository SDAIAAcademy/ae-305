# %% [markdown]
# # Setup check
#
# Run this once before Day 1. It checks the packages, the data, the model registry and the language model
# connection. Every lab also runs without a model key, on the scripted stand-in model; a free OpenRouter key in
# `labs/.env` (or the Colab Secrets panel) makes the language model labs call a free hosted model instead.

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
    try:
        from google.colab import userdata
        os.environ.setdefault("OPENROUTER_API_KEY", userdata.get("OPENROUTER_API_KEY") or "")
    except Exception:  # no secret set: the stand-in model is used
        pass
else:
    while not Path("_tools").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import opskit as K
print("quick mode:", K.QUICK)

# %%
from importlib.metadata import version

for pkg in ["numpy", "pandas", "scipy", "scikit-learn", "mlflow", "pandera", "pyyaml", "opentelemetry-sdk",
            "langgraph", "langgraph-checkpoint-sqlite", "openai"]:
    try:
        print(f"{pkg:28} {version(pkg)}")
    except Exception:
        print(f"{pkg:28} MISSING: run uv sync (local) or the first cell again (Colab)")

# %%
batches = sorted(p.name for p in (K.DATA / "batches").glob("*.csv"))
K.check(len(batches) == 12, f"12 monthly feeder batches ({batches[0]} to {batches[-1]})")
K.check((K.DATA / "manuals" / "v4" / "MM-11.md").exists(), "the manuals, versions 3 and 4")
K.check((K.DATA / "replay" / "INC-0412.json").exists(), "the recorded agent sessions")

# %%
import nabd

bot = nabd.Nabd(nabd.load_release("champion"))
out = bot.answer("How far must palm fronds be cut back?")
print(out["model"], "|", out["answer"])
print("live hosted model" if K.live() else "scripted stand-in model (no working key): every lab still runs")
