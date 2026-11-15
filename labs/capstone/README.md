# Capstone · A release week at Wahaj and its defence

The capstone is individual. You operate Wahaj Electricity Distribution Company's three systems through one
**release week**, from Monday 2 November to Thursday 5 November 2026. Four events arrive. For each one you decide, on
evidence, whether to stop, ship or roll back. You publish the result in a **public repository**: pipeline logs, a
release log, a runbook and timestamped traces. Then you defend it in an **eight-minute live defence**. During the
defence the assessor injects one more fault, and you diagnose it from your traces and logs.

Everything is synthetic. Use the course's data, or data you generate yourself. Do not use personal data or any
internal document from your entity.

## The week

| Day | System | What arrives | The question |
|---|---|---|---|
| Monday | fault-risk classifier | the scheduled retrain on September (`data/batches/feeders_2026-09.csv`) | Does the pipeline stop, and what goes to the data owner? |
| Tuesday | fault-risk classifier | the SCADA team's corrected export (`capstone/week/feeders_2026-09_redelivered.csv`) | Does the challenger pass the gate overall and in every region? If not, what do you do? |
| Wednesday | Nabd | the provider moves the alias `steady` to the snapshot `steady-2026-11-03` (`capstone/week/nabd_release_2026.11.5.json`, `canary_week.jsonl`) | Does it pass the offline gate and every canary stage? |
| Thursday | Mubadir | incident INC-0419: two crews paged for one report (`capstone/week/INC-0419.json`) | What caused it, what fixes it, and how do you prove it is fixed? |

## Minimum requirements

1. **Pipelines and gates.** Run the retraining pipeline on Monday and on Tuesday. Keep both run logs. For each one, say
   which step decided the outcome and why. Monday's report must list every contract problem. On Tuesday, test whether
   a regional difference near the tolerance is noise, for example with a bootstrap interval as in Lab 1.4. Decide
   with that evidence, and do not change the rule in the middle of a release.
2. **Delivery and rollback.** Gate Wednesday's model update offline, then canary it. State the objective, the
   triggers, the minimum sample and the stages, each with a reason. Show the rollback path even if you do not need
   it: which digest or alias you would return to, and who approves.
3. **Observability.** Produce a timestamped trace of every day, as the starter does. Add one monitor or online check
   of your own from Day 3: a drift monitor on the week's inputs, a calibrated sample of Nabd answers, or spans with a
   latency breakdown. Report its numbers.
4. **Agent operations.** Diagnose INC-0419 from the recording. Fix it so that a retry cannot open a second ticket.
   Prove the fix with the rerun and with the regression suite. Write the post-incident note: cause, fix, regression
   evidence, owner. Name the step and spend limits and the kill-switch rule you would set for Mubadir.
5. **Runbook and reproducibility.** The runbook says, for each system, how to detect, decide, roll back and stop it,
   and who decides. A clean clone with `uv run` reproduces every number in your README. Every number is backed by a
   committed file.

## Rubric

| Criterion | Points |
|---|---|
| Pipelines and gates | 25 |
| Delivery and rollback | 20 |
| Observability | 20 |
| Agent operations | 20 |
| Runbook and reproducibility | 15 |

**AI policy.** Coding assistants are allowed for the repository. Keep their transcripts, and keep the timestamps on
every trace and run log: they are part of the evidence of authorship, together with the defence. During the defence
you diagnose the injected fault yourself.

## Getting started

```bash
cd labs
uv run python capstone/make_week.py                                  # once: writes capstone/week/
uv run python capstone/starter.py monday --approver "Lamya Al-Muqbil"
uv run python capstone/starter.py tuesday --approver "Lamya Al-Muqbil"
uv run python capstone/starter.py wednesday
uv run python capstone/starter.py thursday
uv run python capstone/starter.py status                             # the release log so far
```

The starter writes into `capstone/out/`. Pass `--out` or set `CAPSTONE_OUT` to write into your own repository. It
writes `runs/` (pipeline run logs and validation reports), `release_log.jsonl` (one line per decision) and
`traces/<day>.jsonl` (everything each command did, with UTC timestamps).

The week always runs at full size, so everyone's numbers agree. Tuesday builds a model registry first, which takes
a few minutes on a laptop. Without a working model key, Nabd's offline gate runs on the course's scripted stand-in
model. Say so in your README. With a key in `.env` (`OPENROUTER_API_KEY`), the same code calls a free hosted model.
Free models limit requests per day, so run the offline gate once.

Search the starter for `CAPSTONE:` to find the parts you own: the gate's tolerance, the canary's objective and
triggers, and the fix for INC-0419. As shipped, Thursday reports `open` until you write that fix.

The labs closest to each part:

| You need | Start from |
|---|---|
| a release manifest for the three systems | Lab 1.1 |
| registry lineage and an alias promotion | Labs 1.2 and 1.4 |
| a data contract that stops a run | Lab 1.3, `contracts.py` |
| a delivery workflow that promotes one digest | Lab 2.1 |
| the offline gate and the release log | Lab 2.2, `evalgate.py` |
| a canary with triggers | Lab 2.3 |
| cost per successful outcome and budget alerts | Lab 2.4 |
| spans, drift monitors, online evaluation | Labs 3.1, 3.2, 3.3 |
| the retraining policy with approval | Lab 3.4 |
| bundle versions, checkpoints, idempotency keys | Labs 4.1, 4.2 |
| replay, guards, the regression suite | Lab 4.3 |
| limits, the kill switch, the handover | Lab 4.4 |

## Timeline

| When | What |
|---|---|
| Day 4, after Session 4 | Run `make_week.py` and Monday's command once, so environment problems show up now. Copy `TEMPLATE_README.md` as your README. |
| Day 4, evening | Run the rest of the week. Read every trace. Write the INC-0419 fix and the post-incident note. Draft the runbook. |
| Day 5, morning | Add your own monitor or online check. Test a clean clone. Finish the README and the runbook, then publish the repository. |
| Day 5 | Defend it for eight minutes. |

## The defence (eight minutes)

1. **Two minutes.** Your release log: each decision of the week, the metric it was taken on, the evidence.
2. **Five minutes.** The assessor injects one fault into a copy of your setup, such as a changed file, a new batch or
   a new recording, and asks what happened. Find it from your traces and logs, say what you would do and who
   decides, then do the first step.
3. **One minute.** What your runbook would change after this week.

The assessor may ask about any decision in the README. The questions are part of the eight minutes.
