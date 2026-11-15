# <Your project name>: a release week at Wahaj

> One sentence: what this repository shows about operating three AI systems through one week.

[Operating Machine Learning and Language Model Systems, SDAIA Academy](https://github.com/SDAIAAcademy/ae-305)

**Author:** <name>
**Model:** <the scripted stand-in model / a free hosted model, and which one>
**Week:** 2 to 5 November 2026 (synthetic)

## How to run

```bash
cd labs
uv run python capstone/make_week.py
uv run python capstone/starter.py monday --approver "Lamya Al-Muqbil" --out <this repository>/out
# tuesday, wednesday, thursday likewise
```

No keys are committed. Put a model key in `.env` as `OPENROUTER_API_KEY` if you use one.

## Release log

| Day | System | Release | Decision | Decided on | Evidence (file) |
|---|---|---|---|---|---|
| Monday | classifier | | | | `out/runs/...` |
| Tuesday | classifier | | | | |
| Wednesday | Nabd | | | | |
| Thursday | Mubadir | | | | |

## Pipelines and gates

- Monday: which contract problems, how many rows, and what went to the SCADA team.
- Tuesday: the AUC table overall and by region, the gate's verdict, the noise test you ran on the closest region and
  its interval, and your decision with its reason.

## Delivery and rollback

| Setting | Value | Why this value |
|---|---|---|
| Latency objective | | |
| Quality trigger | | |
| Minimum sample | | |
| Stages and pauses | | |
| Rollback target and approver | | |

## Observability

The trace files, and the monitor or online check you added: what it measured, the numbers, and the threshold you
would alert on.

## Agent operations

**INC-0419 post-incident note.** What happened (from the recording), the cause, the fix, the regression evidence
(the rerun and the suite), and the owner.

**Limits for Mubadir.** Step limit, session spend limit, daily budget, and who may turn the kill switch on for a
version.

## Runbook

| System | Detect | Decide (who) | Roll back | Stop |
|---|---|---|---|---|
| Fault-risk classifier | | | | |
| Nabd | | | | |
| Mubadir | | | | |

## What I would change next

Three lines.

## Authorship

The assistants you used, and where their transcripts are. Every trace and run log keeps its timestamp.
