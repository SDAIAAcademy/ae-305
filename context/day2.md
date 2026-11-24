---
course: "Operating Machine Learning and Language Model Systems"
code: "AE-305"
version: "2027.2.0"
deck: "day2"
day: 2
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-305/slides/day2.html"
---

# Operating Machine Learning and Language Model Systems

## Day 2: Deliver

The same artefact from merge to production, language model changes through a gate, a canary that rolls back, and the cost of each outcome

#### [day2#title] Deliver

*SDAIA Academy · Operating Machine Learning and Language Model Systems*

Day 2: The same artefact from merge to production, language model changes through a gate, a canary that rolls back, and the cost of each outcome

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-305

#### [day2#agenda] Deliver

*Today*

- **Session 1 · Continuous delivery for models**: Merge, staging and production promote one artefact by digest, with a person approving the last step
- **Session 2 · Language model releases**: A prompt edit, a model swap and an index refresh are releases, each through the same evaluation gate
- **Session 3 · Shadow and canary on evidence**: Shadow first, then canary stages that advance only on enough evidence and roll back on a stated trigger
- **Session 4 · Cost and capacity signals**: Cost per successful outcome, cache hit rate and utilisation for each system, shown back by team

#### [day2#review-day-1] Which part of the release unit changed?

*Review of Day 1*

**Question:** The fault-risk model's registry version, threshold and code hash are unchanged, but its predictions on the same feeders differ from last week's. What do you check first?

- A. Nothing: the model version is the same, so it is noise
- B. Retrain and compare the AUC
- C. The input data and environment the predictions were made with
- D. Lower the promotion tolerance

### Session 1: Continuous delivery for models

#### [day2#s1] Continuous delivery for models

*Session 1*

- Promote one artefact by digest instead of rebuilding it
- Add a staging check and an approval step before production
- Keep a deployment log a reviewer can audit

#### [day2#push-to-production] Every push to main goes straight to production, rebuilt with the tag latest

*Where Wahaj starts*

```yaml
# file: data/delivery/release_start.yml
jobs:
  deploy:
    steps:
      - run: make test
      - run: docker build -t registry.wahaj.example/nabd:latest .
      - run: docker push registry.wahaj.example/nabd:latest
      - run: ./deploy.sh production registry.wahaj.example/nabd:latest
```

Lab 2.1's checker fails it on six of seven rules: no digest published, no staging, no approval, a moving tag, nothing promoted, no smoke check.

#### [day2#promote-one-digest] Build once; promote the same digest through every environment

*Continuous delivery for models*

1. **Merge to main** tests run
2. **Build** push, publish the digest
3. **Staging** deploy the digest, smoke check
4. **Approval** a reviewer, not the author
5. **Production** the same digest

> **A rebuild is a new artefact.** The same commit can pull a newer base image or package. Only the digest that passed staging goes on.

#### [day2#digest-as-output] The build job hands its digest to the jobs that deploy

*Lab 2.1 · step 2*

```yaml
# file: release.yml
build:
  outputs:
    digest: ${{ steps.push.outputs.digest }}
deploy-staging:
  needs: build
  environment: staging
  steps:
    - run: ./deploy.sh staging ${{ needs.build.outputs.digest }}
    - run: ./smoke_check.sh staging
deploy-production:
  needs: [build, deploy-staging]
  environment: production
```

#### [day2#approval-is-a-rule] The approval lives in the environment's protection rules, not in the file

*The approval step*

- Required reviewers: up to six people or teams; one approval lets the job start.
- Self-review can be blocked: Dhafer merged, so Mutab approves.
- A pull request cannot remove the rule by editing the workflow.

- **Plan limits.** On GitHub's free plans, required reviewers work on public repositories only. The capstone repository is public.

#### [day2#simulated-release] The release waits at production until a reviewer who did not merge approves

*Lab 2.1 · step 4, from the course's run*

- build: built sha256:ce56953fe2d35ec1
- staging: deployed the digest · smoke check passed
- production: waiting for approval
- approval: Dhafer Al-Hazzani: refused, he merged the change
- production: approved by Mutab Al-Shalhoub · deployed the same digest

#### [day2#rollback-is-a-redeploy] A rollback redeploys a recorded digest through the same gate

*The other direction*

```yaml
# file: rollback.yml
on:
  workflow_dispatch:
    inputs:
      digest: {required: true}
jobs:
  rollback-production:
    environment: production
    steps:
      - run: ./deploy.sh production ${{ inputs.digest }}
```

- No build: the digest already passed once.
- The same reviewers approve it, so a rollback is also recorded.
- On a cluster, Argo CD or Argo Rollouts keep the previous revision for the same purpose.

#### [day2#checkpoint-1] Approved, then rebuilt

*Checkpoint*

**Question:** The production job checks out the approved commit, builds the image again and deploys it. Staging tested an image built from the same commit an hour earlier. What is wrong?

- A. Production may run an artefact nobody tested: it should deploy the digest staging tested
- B. Nothing: the same commit gives the same image
- C. Nothing: a reviewer approved the commit
- D. Only the build time: run both builds at once

#### [day2#lab-2-1] Merge to staging to production

Lab 2.1 · 25 min

Turn a single-job workflow into merge, staging and production jobs that promote one digest, add the approval step, check the workflow and simulate a release.

[D2_1_delivery_pipeline.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D2_1_delivery_pipeline.ipynb)

- [ ] Read the starting workflow (4 min)
- [ ] Staging and production jobs that promote one digest (8 min)
- [ ] The approval step and its reviewers (6 min)
- [ ] Check it and simulate a release (7 min)
- [ ] ✱ Stretch: A rollback job that redeploys the previous digest

### Session 2: Language model releases

#### [day2#s2] Language model releases

*Session 2*

- Describe each language model change as a change to the release unit
- Run a provided evaluation gate on a champion and three candidates
- Block a release on the metric that matters, not on the average

#### [day2#three-llm-changes] A prompt, a model and an index are each a release of Nabd

*Language model releases*

| Candidate | Release | Part changed | Why someone wants it |
| --- | --- | --- | --- |
| Prompt edit | nabd-2026.11.1 | prompt v1 to v2 | always cite manual and section |
| Model swap | nabd-2026.11.2 | steady to swift | cheaper and faster |
| Index refresh | nabd-2026.11.3 | manuals v3 to v4 | MM-02 revised, MM-11 added |

> **One part each.** When a release changes one part, the gate's result says which part caused it.

#### [day2#provided-eval-gate] 24 cases, graded by code, with hard floors and allowed drops

*The evaluation gate, ready-made from AE-303*

| Metric | Floor | Allowed drop |
| --- | --- | --- |
| Safety procedures complete, steps in order | 1.00 | 0.00 |
| Out-of-scope questions declined | 1.00 | 0.00 |
| Answer has the required facts | 0.75 | 0.05 |
| Citation correct | none | 0.05 |
| Case pass rate | none | 0.05 |

#### [day2#gate-results] Two candidates ship; the model swap is blocked on one metric

*Lab 2.2 · step 3, from the course's run (scripted stand-in model)*

|  | champion | prompt v2 | model swap | index v4 |
| --- | --- | --- | --- | --- |
| answer correct | 0.917 | 0.917 | 0.917 | 1.000 |
| citation correct | 0.150 | 0.950 | 0.150 | 0.150 |
| safety steps complete | 1.000 | 1.000 | 0.833 | 1.000 |
| case pass rate | 0.250 | 0.917 | 0.208 | 0.292 |
| **decision** |  | ship | block | ship |

#### [day2#missing-safety-steps] The cheaper model dropped the last two steps of the isolation procedure

*Lab 2.2 · step 4*

**Crew:** Give me the isolation steps before I work on the feeder conductor.

**Nabd, model swap (weak example):** 1. Obtain the switching programme. 2. Open the breaker and the load-break switch. 3. Lock and tag every isolation point. 4. Prove dead with an approved tester.

- **Missing.**
  5. Apply earths on both sides. 6. Record the permit number. An average score hides it; a floor on safety does not.

#### [day2#index-refresh-is-release] An index refresh changes what the model reads, so it is gated like a model

*The change people underestimate*

- A new manual can outrank the right section for an old question.
- A changed chunking can split a procedure across two chunks, and the answer loses half.
- Here it helped: version 4 answers the R-24 interlock and salt fog questions that version 3 could not.

> **Refresh as a release.** Rebuild, fingerprint, gate, then switch the alias the assistant reads. Day 3 Session 4 adds a policy for when to refresh.

#### [day2#release-log] Every decision is written down with the metric it was taken on

*Lab 2.2 · the release log*

```json
// file: release_log.jsonl
{"release": "nabd-2026.11.1", "changed": ["prompt"], "decision": "ship", ...}
{"release": "nabd-2026.11.2", "changed": ["model"], "decision": "block",
 "decided_on": "safety_steps_complete",
 "reasons": ["safety_steps_complete 0.83 is below the floor 1.00"]}
{"release": "nabd-2026.11.3", "changed": ["index"], "decision": "ship", ...}
```

#### [day2#checkpoint-2] Same score, blocked

*Checkpoint*

**Question:** The model swap scores the same as the champion on answer correctness and costs half as much. It fails one of six safety cases. What does the release owner do?

- A. Ship it: the average score did not fall
- B. Run the gate again until it passes
- C. Ship it with a warning in the release notes
- D. Block it, log the metric and the case, and raise it with the model's owner

#### [day2#lab-2-2] Three changes through the evaluation gate

Lab 2.2 · 25 min

Run Nabd's prompt edit, model swap and index refresh through the provided evaluation gate, read the result by category and write the release log: two pass, one is blocked.

[D2_2_llm_release_gate.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D2_2_llm_release_gate.ipynb)

- [ ] The release unit of each candidate (4 min)
- [ ] Run the gate on the champion (6 min)
- [ ] Run the three candidates (8 min)
- [ ] Read by category and write the release log (7 min)
- [ ] ✱ Stretch: Run one candidate on a live free model and compare

### Session 3: Shadow and canary on evidence

#### [day2#s3] Shadow and canary on evidence

*Session 3*

- Compare a candidate in shadow without user impact
- Analyse a canary window with a minimum sample
- Roll back automatically on a quality or latency trigger

#### [day2#offline-gate-not-enough] The offline set is fixed; real traffic changes through the day

*Why a canary after a gate*

- The provider's snapshot `steady-2026-10-14` passed Nabd's offline gate.
- The offline cases are mostly in English. Crews ask in both languages, and the mix moves with the shift.
- A canary lets real traffic decide, a slice at a time, with a trigger that undoes it.

- **Recap from AE-205.** Canary and rollback for a web service. Today: for a language model change, with quality as a trigger, not only errors and latency.

#### [day2#shadow-then-canary] Shadow risks nobody; a canary risks a few, on purpose

*Two ways to expose a candidate*

- **Shadow.** The candidate answers a copy of every request; users see only the stable answer. Double the tokens, no user impact.
- **Canary.** A share of real users get the candidate: 5%, then 25%, then 50%. Each step waits for an analysis to pass.

**2,190 ms · 0.920** the candidate in 30 minutes of shadow: p95 latency and share graded ok (stable 2,170 ms, 0.907; Arabic 9% of requests)

#### [day2#canary-analysis] An analysis needs a minimum sample, a paired comparison and stated triggers

*Lab 2.3 · step 2*

```python
# file: Lab 2.3
if n < MIN_SAMPLE:                       # 50
    return "inconclusive", f"{n} requests"
if p95 > SLO_P95_MS:                      # 2,500 ms
    return "fail", "latency trigger: ..."
if ok < ok_stable_same_requests - 0.05:   # paired
    return "fail", "quality trigger: ..."
return "pass", why
```

#### [day2#argo-style-steps] Steps in the Argo Rollouts style: set a weight, pause, analyse

*Lab 2.3 · step 3*

**setWeight 5** pause 60 min → **setWeight 25** pause 30 min → **setWeight 50** pause 30 min → **100** promote

A failed `analysis` aborts the rollout; traffic returns to the stable version.

#### [day2#rolled-back-at-25] 5% passed; at 25% the latency trigger rolled the canary back

*Lab 2.3 · step 4, from the course's run*

- minute 0: setWeight 5
- minute 60: pass: n=70, p95 2,123 ms, ok 0.900 against stable 0.914, Arabic 4%
- minute 60: setWeight 25
- minute 90: fail, latency trigger: n=157, p95 3,115 ms, ok 0.803 against stable 0.873, Arabic 43%
- minute 90: abort: rolled back to stable

#### [day2#traffic-decides] A candidate is only tested on the traffic it has seen

*What the canary saw that nothing else did*

- **Offline gate.** Fixed cases, mostly English: passed.
- **Shadow, 30 minutes.** 9% Arabic: looked better than stable.
- **Canary at 25%.** 43% Arabic: failed on latency and quality.

> **Fix the instruments too.** Add Arabic cases to the offline set and run the shadow across a shift change before the next canary.

#### [day2#pilot-region-not-evidence] Mubadir's pilot region repeats 12.8 points less, and it already did before the change

*When the outcome comes later than the answer*

| Repeat contact within 24 h | Al-Sahil | other regions | gap |
| --- | --- | --- | --- |
| month before, old replies everywhere | 0.167 | 0.271 | -0.104 |
| pilot month, new replies in Al-Sahil | 0.135 | 0.263 | -0.128 |

- Graders preferred the new reply style offline. The outcome that matters, a customer calling again, cannot be graded on the same request.
- Al-Sahil's customers differ: shorter outages, a different mix of calls. The gap is mostly the region, not the replies.

#### [day2#randomise-assignment] Assign accounts at random, so the two groups differ only by the reply style

*A randomised live comparison*

```python
# file: Assignment
h = int(sha256(salt + account), 16)
arm = "new" if h % 2 else "current"
# every region and account, fixed in advance
# outcome: repeat contact within 24 hours
```

| Next month, randomised | value |
| --- | --- |
| new style, n 6,133 | 0.233 |
| current style, n 6,267 | 0.243 |
| difference, 95% interval | -0.010 (-0.025 to +0.004) |
| Al-Sahil share of each arm | 0.18 and 0.19 |

The interval includes zero: no gain of the 2 points this month could detect. Keep the current style, or run longer if 1 point is worth it.

#### [day2#checkpoint-3] A clean first window

*Checkpoint*

**Question:** At 5% the canary served 40 requests in its first pause, with no latency or quality problem. The analysis's minimum sample is 50. What should the rollout do?

- A. Advance to 25%: nothing went wrong
- B. Report inconclusive and extend the pause before deciding
- C. Roll back: the sample is too small
- D. Lower the minimum sample to 40 for this release

#### [day2#lab-2-3] A canary that rolls itself back

Lab 2.3 · 25 min

Replay a day of Nabd traffic through a canary of a new model snapshot, analyse each stage for quality and latency and let the trigger roll it back.

[D2_3_canary_rollback.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D2_3_canary_rollback.ipynb)

- [ ] Shadow first (5 min)
- [ ] Analyse one canary window (8 min)
- [ ] Stages and triggers (7 min)
- [ ] Read where and why it rolled back (5 min)
- [ ] ✱ Stretch: Write the same analysis as an Argo Rollouts AnalysisTemplate

### Session 4: Cost and capacity signals

#### [day2#s4] Cost and capacity signals

*Session 4*

- Price a month of token and compute usage
- Compute cost per successful outcome and utilisation per system
- Show cost back by team and set a budget alert

#### [day2#cost-per-success] Divide what a system cost by the outcomes it delivered, not by its calls

*Cost signals*

- Failed attempts are paid for too; the work still has to be done.
- Each system needs an outcome someone agrees on: a confirmed fault, an accepted answer, a resolved report.
- Prices in the lab are stated assumptions in riyals; replace them with your provider's list.

- **The trap.** A model with half the price per call and twice the retries costs more per success.

#### [day2#october-cost-table] Per call, Mubadir looks cheap; per resolved report, it is the most expensive

*Lab 2.4 · step 2, from the course's run*

| System | Cost (SAR) | Per request | Success rate | Per success |
| --- | --- | --- | --- | --- |
| classifier | 40.55 | 0.0005 | 0.34 | 0.0635 |
| Nabd | 106.05 | 0.0034 | 0.85 | 0.0041 |
| Mubadir | 112.92 | 0.0110 | 0.70 | 0.0156 |

The classifier's outcome is a flagged feeder that inspection confirmed; its requests are feeder scores, so its cost per request is not comparable with the others.

#### [day2#cache-hit-rate] A date at the top of the prompt cut Nabd's cache hit rate from 0.62 to 0.12

*Lab 2.4 · step 3*

| Item | Value |
| --- | --- |
| before 18 Oct | 0.62 |
| from 18 Oct | 0.12 |

- Provider prompt caches match the beginning of a request.
- Stable text first (instructions, tools), changing text last (date, question).
- Cached input tokens are priced at a tenth here: the change raised Nabd's daily cost.

#### [day2#utilisation] Utilisation shows what you pay for and do not use

*Resource use*

| Item | Value |
| --- | --- |
| classifier | 0.12 |
| Mubadir | 0.22 |
| Nabd | 0.28 |

The classifier keeps 24 node-hours a day provisioned for one daily batch and a monthly retrain. Scale it to zero between runs, or share the nodes.

#### [day2#showback-and-alerts] Show each team its cost, and alert before the budget is gone

*Lab 2.4 · step 4*

| Team | SAR |
| --- | --- |
| customer-care (Mubadir) | 112.92 |
| field-operations (Nabd) | 84.75 |
| asset-management (classifier) | 40.55 |
| control-room (Nabd) | 21.29 |

- **Burn rate, from day 7.** Month-to-date spend above the budget's share by 20%: Mubadir alerted on 15 October.
- **Forecast.** Projected month-end above budget: Mubadir on the 14th, but also the classifier on the 7th, because of its planned retrain.

#### [day2#checkpoint-4] Cheaper per call

*Checkpoint*

**Question:** A new configuration of Mubadir halves the cost per model call, but the share of reports resolved without a person drops from 0.70 to 0.40. What happens to the cost per resolved report?

- A. It halves, like the cost per call
- B. It stays the same: the work is the same
- C. It falls only slightly, and every unresolved report adds a person's time on top
- D. It cannot be known without the token counts

#### [day2#lab-2-4] Cost per successful outcome

Lab 2.4 · 25 min

Price a month of Wahaj's token, compute and outcome logs, compute cost per successful outcome, cache hit rate and utilisation per system, show it back by team and set budget alerts.

[D2_4_cost_signals.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D2_4_cost_signals.ipynb)

- [ ] Price the month (6 min)
- [ ] Cost per successful outcome by system (6 min)
- [ ] Utilisation and cache hit rate (5 min)
- [ ] Showback by team and a budget alert (8 min)
- [ ] ✱ Stretch: Alert on the month-end forecast, not on the spend so far

#### [day2#day-2-recap] One artefact to production, a gate and a canary for model changes, and cost per outcome

*Day 2 recap*

- **Delivery.** Build once, promote the digest, a reviewer who did not merge.
- **Releases on evidence.** Offline gate with floors, then a canary with stated triggers.
- **Cost signals.** Per successful outcome, cache hit rate, utilisation, alerts.

#### [day2#tomorrow-observe] Observe: traces, drift monitors that do not cry wolf, online evaluation and a retraining policy

*Tomorrow · Day 3*

Tomorrow you find out why Nabd is slow, replay a month of inputs with two hidden shifts, and grade a week of live answers.
