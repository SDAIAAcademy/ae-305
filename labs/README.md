# Operating Machine Learning and Language Model Systems: labs

Hands-on notebooks for the SDAIA Academy course **AE-305 Operating Machine Learning and Language Model Systems
(تشغيل أنظمة تعلم الآلة والنماذج اللغوية)**. Every lab operates one of the three systems of **Wahaj Electricity
Distribution Company**, a fictional distributor with six regions and 4,800 feeders:

- a **fault-risk classifier**, retrained on monthly feeder batches;
- **Nabd (نبض)**, the field-crew assistant, with retrieval over the maintenance manuals and two tools;
- **Mubadir (مبادر)**, the outage-ticket agent.

Each lab starts from a supplied reference state, so none depends on an earlier one.

Nothing runs a model on your machine. A laptop processor or a Colab CPU runtime is enough. **Every lab runs without a
model key**: the language model steps then use a scripted stand-in model that answers from the same data. With a free
OpenRouter key the same code calls a free hosted model.

## Quick start

**Google Colab**
1. Open a notebook from the [course page](https://sdaiaacademy.github.io/ae-305/), or directly:
   `https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/<notebook>.ipynb`.
2. Optional: in the 🔑 **Secrets** panel add `OPENROUTER_API_KEY` and turn on notebook access.
3. Run the first cell. It clones this repository and installs `requirements-colab.txt`.

**Local**
```bash
git clone https://github.com/SDAIAAcademy/ae-305
cd ae-305/labs
cp .env.example .env              # optional: paste a free OpenRouter key
uv sync                           # creates the environment from pyproject.toml (uv.lock pins every version)
uv run jupyter lab
```
Run `00_setup_check.ipynb` once before Day 1.

## Settings (`.env`)

| Setting | Default | Notes |
|---|---|---|
| `OPENROUTER_API_KEY` | empty | a free key from <https://openrouter.ai/keys>; without it, the scripted stand-in model answers |
| `OPS_MODEL_STEADY` | `google/gemma-4-31b-it:free` | the hosted model behind the release name `steady` |
| `OPS_MODEL_SWIFT` | `google/gemma-4-26b-a4b-it:free` | the hosted model behind `swift`, the cheaper candidate of Lab 2.2 |
| `OPS_MODEL` | empty | `scripted` forces the stand-in model even with a key |
| `OPS_QUICK` | `0` | `1` trains smaller models, for slow machines and for the course's own test runs |

Free models change often. If a default disappears, pick another free model with tool calling.

## Notebooks

| Day | Session | Notebook |
|---|---|---|
| 0 | Setup | [`00_setup_check.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/00_setup_check.ipynb) |
| 1 | A release manifest and the unrecorded change | [`D1_1_release_manifest.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D1_1_release_manifest.ipynb) |
| 1 | Reproduce a model from the registry | [`D1_2_registry_lineage.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D1_2_registry_lineage.ipynb) |
| 1 | A validation step that stops training | [`D1_3_validation_step.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D1_3_validation_step.ipynb) |
| 1 | Champion, challenger and the regional gate | [`D1_4_promotion_gate.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D1_4_promotion_gate.ipynb) |
| 2 | Merge to staging to production | [`D2_1_delivery_pipeline.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D2_1_delivery_pipeline.ipynb) |
| 2 | Three changes through the evaluation gate | [`D2_2_llm_release_gate.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D2_2_llm_release_gate.ipynb) |
| 2 | A canary that rolls itself back | [`D2_3_canary_rollback.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D2_3_canary_rollback.ipynb) |
| 2 | Cost per successful outcome | [`D2_4_cost_signals.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D2_4_cost_signals.ipynb) |
| 3 | Spans for Nabd and the slowest step | [`D3_1_tracing.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D3_1_tracing.ipynb) |
| 3 | Two shifts in a replayed month | [`D3_2_drift_monitors.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D3_2_drift_monitors.ipynb) |
| 3 | Online evaluation and a review queue | [`D3_3_online_eval.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D3_3_online_eval.ipynb) |
| 3 | A retraining trigger with a cost and an approval | [`D3_4_retraining_policy.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D3_4_retraining_policy.ipynb) |
| 4 | Mubadir as one versioned bundle | [`D4_1_agent_bundle.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D4_1_agent_bundle.ipynb) |
| 4 | Crash, resume, and no duplicate tickets | [`D4_2_durable_retries.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D4_2_durable_retries.ipynb) |
| 4 | Replay incident INC-0412 | [`D4_3_replay_incident.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D4_3_replay_incident.ipynb) |
| 4 | Limits and a kill switch at the gateway | [`D4_4_budgets_killswitch.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D4_4_budgets_killswitch.ipynb) |

Exercises are marked **✏️ Exercise** and raise `NotImplementedError` until you fill them in. An unfinished exercise
does not stop the notebook: a safety net loads the reference result, so later steps still run. Complete reference
versions are in `solutions/`. Cells marked **✱ Stretch** are optional. Self-checks print ✅.

Each lab writes into `artifacts/<lab>/` and resets that folder when it starts. The shared data in `data/` is never
changed. `artifacts/` is ignored by git.

The notebooks are generated from the percent-format sources in `_src/` by `_tools/py2nb.py`
(`uv run python _tools/py2nb.py`), which also writes `solutions/`. Edit the sources, not the notebooks.

## The case study data

Synthetic and deterministic (`prepare_data.py`, standard library only, seed 305). The labs' "today" is mid-November
2026. Customer names, phone numbers and account numbers are invented.

| Data | File | Contents |
|---|---|---|
| Feeders and monthly batches | `data/feeders.csv`, `data/batches/feeders_<month>.csv` | 4,800 feeders in six regions; twelve batches from 2025-11 to 2026-10 with the label `fault_30d` |
| Late labels | `data/late_labels/feeders_2026-08_first_cut.csv` | August as first delivered, before the Al-Jabal inspections |
| Manuals | `data/manuals/v3`, `v4` | ten maintenance manuals; v4 revises MM-02 and adds MM-11 |
| Nabd | `data/nabd/` | two prompts, tool schemas, four release files (champion and three candidates) |
| Offline evaluation | `data/eval/nabd_eval.jsonl` | 24 cases: procedures, safety steps, out of scope, tools |
| Mubadir | `data/mubadir/`, `data/ops/customers.csv` | the bundle (prompt, tools, harness, sandbox); 300 customers |
| Two runs | `data/runs/run_A`, `run_B` | the same three systems a week apart, with a changelog (Lab 1.1) |
| Delivery | `data/delivery/release_start.yml` | the workflow Wahaj starts from (Lab 2.1) |
| Replays | `data/replay/` | four hours of canary traffic (Lab 2.3); INC-0412 and five regression cases (Lab 4.3) |
| Reference states | `data/reference/` | a replayed month of inputs, a week of Nabd traces with reviewers' labels, October's cost log, the runaway report, and the safety-net results of the labs |
| Prices and budgets | `data/prices.json`, `data/budgets.json` | course assumptions in Saudi riyals, to replace with a provider's price list |

**Planted problems, for the trainer.**
- Between run A and run B, the provider alias `steady-latest` moved from `steady-2026-09-12` to `steady-2026-10-14`
  and nobody recorded it. The threshold change from 0.35 to 0.30 was recorded.
- The September batch has 36 duplicate rows, Al-Hadba load written as fractions (807 rows) and 14 region codes with a
  trailing space.
- August is drifted: hotter, dustier, and Al-Sahil's coastal overhead feeders fault more. Challenger A was trained on
  August's first cut and is worse in Al-Jabal. Challenger B passes.
- Nabd's cheaper model drops the last two steps of the isolation procedure (E02).
- The October snapshot is slow and weaker on Arabic text, which the Arabic-heavy shift from minute 70 reveals.
- From 18 October a date at the top of Nabd's prompt breaks the prompt cache. Mubadir loops on 14 to 16 October.
- Production Nabd reloads its index on every request (`cache_index=False`).
- The replayed month has a load skew from day 12 and a dust rise from day 21, next to a heat spike on day 8, a quiet
  day 17 and October's cooling.
- About 16% of the week's Nabd answers are bad, and 87 of 400 questions hold personal data.
- INC-0412: a lagging replica says "restored", 140 minutes old, and Mubadir closes the report.

## Helpers

| Module | What it holds |
|---|---|
| `opskit.py` | paths and quick mode; batches, training and the registry (`seed_registry`, `register_fault_model`, `load_registered`, `auc_by_region`); a small flow runner (`run_flow`, `StopRun`); the delivery checker and simulator; `run_rollout` with Argo Rollouts step semantics; `chat` (hosted model or stand-in); prices, `Gateway`, `SessionStore` |
| `contracts.py` | the data contract of a monthly batch (pandera) and `validate_step` |
| `graders.py`, `evalgate.py` | the provided graders and the offline evaluation gate, built the AE-303 way |
| `nabd.py` | Nabd: the BM25 index, the two tools, the four steps of a request, its stand-in model |
| `mubadir.py` | Mubadir: the services on SQLite, the harness, the session log, `replay`, its stand-in model |

## Optional: a single-node cluster

`cluster/` holds a kind configuration, a Rollout and an AnalysisTemplate for Argo Rollouts, with the same steps and
triggers as Lab 2.3. It needs Docker and kind. It is not needed for any lab, and it was not run when the course was
built: try it before offering it to a cohort.

## Capstone

`capstone/` holds the release week (`make_week.py`), the starter and the README template. See
`capstone/README.md`.

**Windows and long folder paths.** If an import fails with "The filename or extension is too long", keep the
virtual environment in a short folder: set `UV_PROJECT_ENVIRONMENT` to a short path before `uv sync`.
