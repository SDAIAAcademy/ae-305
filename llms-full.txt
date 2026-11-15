---
course: "Operating Machine Learning and Language Model Systems"
code: "AE-305"
version: "2027.1.0"
scope: "course"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-305/"
---

# Operating Machine Learning and Language Model Systems

Run models, assistants and agents in production as versioned releases that are gated, observed and safe to roll back

Participants run three systems of a fictional electricity distribution company in production: a fault-risk classifier retrained on monthly batches with planted drift, a field-crew assistant with retrieval and two tools, and an outage-ticket agent. They version everything that changes behaviour as one release unit, build pipelines with validation and promotion gates, release through canary stages with automatic rollback, trace requests, monitor drift and online quality, and keep the agent alive through crashes and runaway loops. Evaluators come ready-made from AE-303.

- **Audience:** Practitioners. Engineers who have completed the level 200 set or can show equivalent work: a deployed model or language model application they built and can explain.
- **Prerequisites:** AE-205 Deploying AI Services: Containers, Serving and Monitoring; AE-203 Building Applications on Language Models; Builds a container image and a continuous-integration workflow; Reads an evaluation report with pass rates and intervals; Has built a tool-calling agent, as in AE-302 or equivalent; Setup: a laptop CPU with uv, or Google Colab; a free OpenRouter key is optional, since every lab also runs on a scripted stand-in model. Nothing downloads a model. Run 00_setup_check before Day 1; see labs/README.md.
- **Case study:** Wahaj Electricity Distribution Company: Wahaj is a fictional electricity distributor with six regions and 4,800 feeders that runs three systems: a feeder fault-risk classifier retrained on monthly batches, Nabd, a field-crew assistant over the maintenance manuals with two tools, and Mubadir, an outage-ticket agent. Participants version, gate, release, observe and repair all three on synthetic data generated with a fixed seed: twelve monthly batches with one corrupt and one drifted, two versions of the manuals, a replayed month of traffic with two planted shifts, recorded agent traces with one incident, and a month of cost logs.

## Outcomes

- LO1 (Applied): Prepare a release manifest that versions data, code, configuration, model, prompt, retrieval index and tool schemas as one unit, given two runs of the three systems that behave differently
- LO2 (Performance): Build a retraining pipeline, started by a drift or schedule trigger, with data validation and a promotion gate that compares challenger and champion overall and by region, given monthly feeder batches, one of them corrupt and one drifted
- LO3 (Performance): Deliver language model changes through an evaluation gate and a canary stage with an automatic rollback trigger, given a prompt edit, a model swap and an index refresh, one of which regresses
- LO4 (Applied): Configure request tracing, drift monitors and online evaluation with a review queue, and tune alert thresholds, given a replayed month of traffic with two planted shifts
- LO5 (Performance): Diagnose an agent incident by replaying recorded traces and fix it with idempotent tools, durable state or a budget, given a recorded failure of the ticket agent
- LO6 (Applied): Measure cost per successful outcome and resource use for each system and set budget alerts, given a month of token, compute and outcome logs

## Day 1: Version and build

One release unit, a reproducible model, a pipeline that stops on bad data, and a gate by region

#### [day1#title] Version and build

*SDAIA Academy · Operating Machine Learning and Language Model Systems*

Day 1: One release unit, a reproducible model, a pipeline that stops on bad data, and a gate by region

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-305

#### [day1#agenda] Version and build

*Today*

- **Session 1 · What changes behaviour**: Data, code, configuration, model, prompt, index and tool schemas move together as one release unit
- **Session 2 · Registries and lineage**: A registry entry is useful only if it leads back to the exact data, code and parameters
- **Session 3 · Pipelines with validation**: A data contract checked before training stops the run instead of training on a broken batch
- **Session 4 · Promotion gates**: A challenger replaces the champion only when it is better overall and not worse in any region

#### [day1#four-days-three-systems] Four days of operating three systems, then a release week as the capstone

*The course at a glance*

- **Day 1 · Version and build.** The release unit, the registry, validation, promotion gates.
- **Day 2 · Deliver.** Delivery with approval, language model releases, canary and rollback, cost.
- **Day 3 · Observe.** Traces, drift monitors, online evaluation, retraining policies.
- **Day 4 · Operate agents.** Bundles, durable execution, replay, budgets and kill switches.

> **Day 5 · Capstone.** A simulated release week: a corrupt batch, a provider model update and an agent incident arrive. You gate, ship or roll back each, then defend it with one more fault injected live.

#### [day1#wahaj-three-systems] Wahaj Electricity Distribution Company runs three systems in production

*One case study all week*

A fictional distributor: six regions, 4,800 feeders, crews in the field and a control room. You operate:

- **Fault-risk classifier.** Scores every feeder monthly; the top of the list is inspected first. Retrained on monthly batches.
- **Nabd نبض.** The field-crew assistant: retrieval over the maintenance manuals and two tools.
- **Mubadir مبادر.** The outage-ticket agent: finds the customer, checks the outage, opens or closes tickets.

#### [day1#ai-policy-and-models] Operate with evidence, on free hosted models, with AI as a tutor

*How this course works*

- **Evidence first.** Every release decision in the labs is taken on a log, a metric or a trace, and written down.
- **No model on your laptop.** Language model labs call a free hosted model, or a scripted stand-in when no key works. Training runs on a laptop processor or Colab.
- **AI as a tutor.** An assistant may explain logs and give hints. It does not write your pipeline or alert definitions.

> **Supervised checks.** The entry and exit checks are done without AI: reading a pipeline log and a trace, and choosing a rollback trigger.

#### [day1#setup-check] One notebook proves your setup: 00_setup_check

*Before Session 1*

```bash
# file: terminal
git clone https://github.com/SDAIAAcademy/ae-305
cd ae-305/labs
uv sync
uv run jupyter lab   # open 00_setup_check.ipynb
```

- It lists the packages, finds the twelve monthly batches, the manuals and the recorded agent sessions.
- It asks Nabd one question. "scripted stand-in" is a pass: every lab runs on it.
- In Colab, open the notebook from the course page; the first cell installs what Colab lacks.

### Session 1: What changes behaviour

#### [day1#s1] What changes behaviour

*Session 1*

- Name every part that changes the behaviour of a model, an assistant and an agent
- Pin a provider model to an identifier that does not move
- Write a release manifest and diff two of them

#### [day1#behaviour-changed-code-did-not] Nothing was deployed, yet two systems behave differently

*Two runs, two weeks apart*

- **212 → 268** feeders the classifier flagged for inspection
- **3** of Nabd's weekly probe answers changed

- **The question of the day.** What exactly was running on each date? If you cannot answer from a file, you cannot explain, reproduce or roll back.

#### [day1#what-changes-behaviour] Seven things change behaviour, and all seven are versioned together

*The release unit*

| Part | Classifier | Nabd | Mubadir |
| --- | --- | --- | --- |
| Data | training snapshot | the manuals | customer and outage services |
| Code | trainer, features | retrieval, tool code | harness |
| Configuration | threshold | k, temperature | step limit, retries |
| Model | registry version | provider model id | provider model id |
| Prompt |  | system prompt | system prompt |
| Retrieval index |  | index build |  |
| Tool schemas |  | two tools | six tools |

#### [day1#alias-is-a-pointer] An alias is a pointer that the provider can move

*Provider model identifiers*

- run A asked: `hosted/steady-latest`
- answered by: `hosted/steady-2026-09-12`
- run B asked: `hosted/steady-latest`
- answered by: `hosted/steady-2026-10-14`

- Release files that name the alias look identical on both dates.
- The response says which model answered: record that field on every call.
- Pin a dated identifier in the release, and change it only through a release.

#### [day1#manifest-by-hash] The manifest hashes every part; its own id is the hash of all of them

*Lab 1.1 · steps 2 and 3*

```python
# file: Lab 1.1
parts = {
  "classifier": {"registry": "fault-risk@champion v3", "threshold": 0.35, ...},
  "nabd": {"prompt": sha("prompt.txt"), "tools": sha("tools.json"),
           "index": "v3", "index_fingerprint": Index("v3").fingerprint(),
           "model_requested": rel["model"], "model_resolved": log["response_model"]},
  "mubadir": {f: sha(f) for f in bundle_files},
}
release_id = "wahaj-" + sha_json(parts)[:12]
```

#### [day1#diff-against-change-log] Diff the manifests, then ask the change log which changes were intended

*Lab 1.1 · step 4, from the course's run*

| Difference | Run A | Run B | In the change log? |
| --- | --- | --- | --- |
| `classifier.threshold` | 0.35 | 0.30 | yes: approved by Lamya |
| `nabd.model_resolved` | steady-2026-09-12 | steady-2026-10-14 | no |

> **The unrecorded change.** Nobody at Wahaj changed Nabd. The provider moved the alias between the runs.

#### [day1#maturity-manual-to-automated] Each level automates one more step and keeps the evidence of it

*Maturity from manual to automated*

1. **Manual**: a notebook and a copied file (no record)
2. **Versioned**: manifest, registry, snapshots (Day 1)
3. **Pipelined**: validation, gates, delivery (Days 1 and 2)
4. **Closed loop**: monitors trigger retraining (Day 3)

#### [day1#checkpoint-1] Same model name, different answers

*Checkpoint*

**Question:** Nabd's release file names `hosted/steady-latest` on both dates, and its answers changed. What should the release record so this cannot hide again?

- A. Nothing more: the model name is already in the release
- B. The identifier the provider answered with, and a pinned dated identifier in the release
- C. The date and time of every call
- D. A message to the team whenever answers look different

#### [day1#lab-1-1] A release manifest and the unrecorded change

Lab 1.1 · 25 min

Hash every part of two recorded runs of the three Wahaj systems into release manifests, diff them and find the change that no change log recorded.

[D1_1_release_manifest.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D1_1_release_manifest.ipynb)

- [ ] Read the two run folders (4 min)
- [ ] Hash every part that changes behaviour (7 min)
- [ ] Build the manifest for each run (6 min)
- [ ] Diff the manifests against the change log (8 min)
- [ ] ✱ Stretch: A check that refuses a manifest whose model is a moving alias

### Session 2: Registries and lineage

#### [day1#s2] Registries and lineage

*Session 2*

- Read a model version, its alias and its lineage tags
- Rebuild a data snapshot from its content hash
- Reproduce a colleague's model and prove it matches

#### [day1#registry-recap] A registry holds versions; an alias says which version does which job

*Recap from AE-205*

- **Version.** Immutable: one trained model, its run, its metrics.
- **Alias.** Mutable: `champion`, `challenger-b`. Serving loads `models:/fault-risk@champion`.
- **Tags.** The lineage: data snapshot, code hash, months, author, the reason for a promotion.

#### [day1#lineage-chain] Follow the champion back to the exact data and code

*Lineage*

1. **Alias** champion
2. **Version 3** registered in August
3. **Run** parameters and metrics
4. **Snapshot** de8fd6c3… (32,400 rows)
5. **Code** trainer hash

> **Reproduce before you trust.** A registry entry that cannot be rebuilt is a file with a name.

#### [day1#content-addressed-data] Name the data by its content, as DVC and lakeFS do

*Data versioning*

```python
# file: opskit.snapshot
data = df.to_csv(index=False).encode()
h = sha256(data)
path = store / h[:2] / f"{h}.csv"
if not path.exists():
    path.write_bytes(data)
```

- The same rows give the same name on any machine.
- A file called `training_latest.csv` says nothing about which rows it held last month.
- The tools add remote storage, branches and garbage collection; the idea is this one line.

#### [day1#params-come-back-as-strings] Parameters come back from the tracking store as text

*A trap in Lab 1.2*

- params: `{"max_iter": "150", "learning_rate": "0.05", "recent_weight": "4"}`
- retrain: `TypeError`, or worse, a silent change of meaning

- **Convert on purpose.** Keep a typed list of the training parameters and convert each one when you read it back.

#### [day1#reproduced-row-by-row] A reproduction matches on data hash, code hash and every prediction

*Lab 1.2 · step 4*

- **=** snapshot hash rebuilt from the months
- **=** training code hash
- **0.0** largest difference in predicted risk on 1,200 holdout feeders

The same code on "the latest training file" (up to August) gives another hash and predictions that differ by up to half the scale.

#### [day1#environment-is-part] The library versions are part of the release too

*What lineage still misses*

- The same code and data on another scikit-learn version can give different trees.
- `labs/uv.lock` pins every package; the capstone repository commits its own lock file.
- A container image digest pins the operating system and Python as well (AE-205).

> **In Colab** the libraries are Colab's, so a rebuild there can differ from your laptop's by a few thousandths: that difference is an environment change, and now you can name it.

#### [day1#checkpoint-2] Reproduced, or just similar?

*Checkpoint*

**Question:** You retrain Lamya's model from the shared training file and get the same AUC to three decimals, but the data hash differs from the registry tag. What do you conclude?

- A. It is reproduced: the AUC matches
- B. The hash function is unreliable across machines
- C. Update the registry tag to the new hash
- D. It is a different model: rebuild the snapshot from the months in the lineage

#### [day1#lab-1-2] Reproduce a model from the registry

Lab 1.2 · 25 min

Find the champion fault-risk model in the registry, follow its tags to the data snapshot and the trainer commit, retrain it and show that the metric and the predictions match.

[D1_2_registry_lineage.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D1_2_registry_lineage.ipynb)

- [ ] Find the champion and read its lineage (6 min)
- [ ] Rebuild the data snapshot and check its hash (6 min)
- [ ] Retrain with the recorded parameters (7 min)
- [ ] Compare metric and predictions (6 min)
- [ ] ✱ Stretch: Show why the latest training file does not reproduce the model

### Session 3: Pipelines with validation

#### [day1#s3] Pipelines with validation

*Session 3*

- Write a data contract as a schema with types, ranges and allowed values
- Add batch checks: row count and duplicate keys
- Make validation a pipeline step that stops the run with a report

#### [day1#corrupt-batch-trains-fine] A broken batch trains without an error

*The September batch*

- Al-Hadba's load arrived as a fraction: feeder F-0801 reads `0.815`, not 81.5.
- 36 rows arrived twice.
- 14 Al-Sahil rows carry the code `"SAH "`, with a trailing space.

- **Training does not complain.** Every value is a valid number or string. The model learns that Al-Hadba never has load, and its metric on the same broken data can look fine.

#### [day1#data-contract] A contract says what every row and every batch must be

*Data contracts*

- **Row rules.** Types, patterns (`^F-\d{4}$`), allowed values, physical ranges (load 20 to 150 percent of rating), no nulls.
- **Batch rules.** One row per feeder, every feeder present (within 2%), the month the file claims.

> **Agree it with the data owner.** The SCADA export team signs the contract; your pipeline enforces it on every delivery.

#### [day1#contract-as-schema] The contract as a pandera schema

*Lab 1.3 · step 1*

```python
# file: Lab 1.3
import pandera.pandas as pa
SCHEMA = pa.DataFrameSchema({
    "feeder_id": pa.Column(str, pa.Check.str_matches(r"^F-\d{4}$")),
    "region": pa.Column(str, pa.Check.isin(["RIM", "HAD", "SAH", "WAD", "JAB", "NAK"])),
    "load_peak_pct": pa.Column(float, pa.Check.in_range(20, 150)),
    "fault_30d": pa.Column(int, pa.Check.isin([0, 1])),
    ...
}, strict=True)
SCHEMA.validate(df, lazy=True)   # every failure, not the first
```

#### [day1#validation-step-stops-run] Validation is a step that can stop the run

*Lab 1.3 · step 3*

**load** the batch → **validate** contract and batch rules → **train** only if valid → **gate** Session 4

A failed validation raises a stop, writes a report, and leaves the champion untouched. An orchestrator (Prefect, Airflow, Kubeflow Pipelines) records the run as stopped, not failed.

#### [day1#three-batches-result] July and August train; September stops at validation

*Lab 1.3 · step 4, from the course's run*

- 2026-07: load ok · validate ok · train ok → SUCCEEDED
- 2026-08: load ok · validate ok · train ok → SUCCEEDED
- 2026-09: load ok · validate STOPPED: 3 contract problems
- report: 36 duplicate feeder_id rows · load_peak_pct: 807 rows outside 20 to 150 · region: 14 rows not an allowed code

#### [day1#report-dont-repair] Report the fault to the owner; do not quietly repair it

*What the pipeline must not do*

- **Quiet repairs.** Dropping duplicates, multiplying small loads by 100, stripping spaces: each hides a broken export that will break again.
- **Stop, quarantine, report.** Keep the failing rows apart, send the counts and one example, retrain when the corrected batch arrives.

#### [day1#checkpoint-3] Where does validation go?

*Checkpoint*

**Question:** A batch delivers one region's load as a fraction instead of a percentage. Where should the pipeline catch it?

- A. In a contract step before training, which stops the run and reports the column
- B. In the promotion gate, when the new model's AUC drops
- C. When crews complain about the inspection list
- D. In a cleaning step that multiplies values below 2 by 100

#### [day1#lab-1-3] A validation step that stops training

Lab 1.3 · 25 min

Write the feeder batch contract as a pandera schema, add batch checks and run the pipeline on three monthly batches: two train, the corrupt one stops with a report.

[D1_3_validation_step.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D1_3_validation_step.ipynb)

- [ ] The contract as a schema (8 min)
- [ ] Batch checks: row count and duplicates (5 min)
- [ ] The step that stops the run (7 min)
- [ ] Run the pipeline on three batches (5 min)
- [ ] ✱ Stretch: Quarantine the failing rows and write the report for the data owner

### Session 4: Promotion gates

#### [day1#s4] Promotion gates

*Session 4*

- Score champion and challengers on the same holdout
- Compare overall and by region with a stated tolerance
- Promote by moving the registry alias, with the reason logged

#### [day1#salt-fog-drift] Salt fog started tripping coastal lines, and the champion had never seen it

*August in Al-Sahil*

- From August, overhead feeders within 10 km of the coast fault far more often.
- The champion was trained on November to July: distance to the coast never mattered.
- Two challengers were trained in October on February to August.

**0.742** champion's AUC in Al-Sahil on the August holdout (0.830 overall)

#### [day1#champion-challenger-gate] A challenger is promoted only when it beats the champion on the same holdout

*Champion and challenger*

- **Same holdout.** The quarter of feeders no model trained on, in the newest month with complete labels.
- **Overall.** Better than the champion's AUC.
- **By region.** No region more than 0.03 worse.

> **Why regions.** Crews and customers live in regions. An average can hide a region that pays for everyone else's gain.

#### [day1#auc-by-region-table] Both challengers win overall; one loses Al-Jabal

*Lab 1.4 · step 2, from the course's run*

|  | all | RIM | HAD | SAH | WAD | JAB | NAK |
| --- | --- | --- | --- | --- | --- | --- | --- |
| champion | 0.830 | 0.889 | 0.814 | 0.742 | 0.774 | 0.879 | 0.748 |
| challenger-a | 0.851 | 0.888 | 0.812 | 0.917 | 0.784 | 0.810 | 0.809 |
| challenger-b | 0.872 | 0.890 | 0.815 | 0.919 | 0.779 | 0.873 | 0.811 |

#### [day1#first-cut-delayed-labels] Challenger A learned from labels that had not arrived yet

*The cause behind challenger A*

- The first cut of the August batch came before the inspections of the most wooded Al-Jabal feeders were entered.
- Their faults read 0, so A learned that wooded mountain feeders are safe.
- The complete batch came three weeks later; challenger B was trained on it.

- **A data problem, caught by a model gate.** No contract rule fails: 0 is a valid label. Only the regional comparison shows it.

#### [day1#promote-by-alias] Promotion moves an alias, and the old champion stays one move away

*Lab 1.4 · step 4*

```python
# file: Lab 1.4
old = client.get_model_version_by_alias("fault-risk", "champion").version
new = client.get_model_version_by_alias("fault-risk", "challenger-b").version
client.set_registered_model_alias("fault-risk", "previous-champion", old)
client.set_registered_model_alias("fault-risk", "champion", new)
client.set_model_version_tag("fault-risk", new, "promoted_reason",
    "passed overall and in every region (holdout 2026-08, tolerance 0.03)")
```

#### [day1#tolerance-is-noise] A rule with no tolerance rejects every challenger on noise

*The tolerance*

- 200 holdout feeders per region, 16 to 81 of them with a fault in August.
- Resample them and a region's AUC moves by a few hundredths.
- Challenger B is at most 0.006 worse in any region (Al-Jabal): noise. A is 0.069 worse there: not noise.

> **Stretch.** Bootstrap the Al-Wadi gap of challenger B and read whether its interval includes zero.

#### [day1#checkpoint-4] Better on average

*Checkpoint*

**Question:** Challenger A beats the champion overall (0.851 against 0.830) and is 0.069 worse in Al-Jabal. The tolerance is 0.03. What happens?

- A. Promote it: the overall gain is larger than one region's loss
- B. Raise the tolerance to 0.07 for this release
- C. Reject it, record the region and the cause, and look at challenger B
- D. Use A everywhere except Al-Jabal

#### [day1#lab-1-4] Champion, challenger and the regional gate

Lab 1.4 · 25 min

Compare the champion with two challengers overall and by region; one is better overall but worse in Al-Jabal, one passes both; promote only the one that passes.

[D1_4_promotion_gate.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D1_4_promotion_gate.ipynb)

- [ ] Score the champion and two challengers (6 min)
- [ ] AUC overall and by region (6 min)
- [ ] The gate rule (7 min)
- [ ] Promote by moving the alias (6 min)
- [ ] ✱ Stretch: A bootstrap interval for the regional gap

#### [day1#day-1-recap] Know what ran, rebuild it, stop bad data, and gate by region

*Day 1 recap*

- **One release unit.** Seven parts, hashed together; the served model recorded.
- **Lineage you can rebuild.** Alias, version, run, snapshot hash, code hash.
- **Two gates.** A contract before training; a regional comparison before promotion.

#### [day1#tomorrow-deliver] Deliver: the same artefact to production, language model releases, a canary that rolls back, and cost

*Tomorrow · Day 2*

The delivery workflow is written and simulated in a notebook, so nothing new is needed. Nabd's three candidate releases are waiting, and so is the model snapshot from today's unrecorded change.

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

In Argo Rollouts, `steps` hold `setWeight` and `pause`; a background `analysis` that fails aborts the rollout and traffic returns to the stable version.

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

## Day 3: Observe

Spans for every step, drift monitors that do not cry wolf, online evaluation with a review queue, and a retraining policy

#### [day3#title] Observe

*SDAIA Academy · Operating Machine Learning and Language Model Systems*

Day 3: Spans for every step, drift monitors that do not cry wolf, online evaluation with a review queue, and a retraining policy

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-305

#### [day3#agenda] Observe

*Today*

- **Session 1 · Tracing requests end to end**: One trace per request with spans for retrieval, the model and each tool
- **Session 2 · Drift, skew and delayed labels**: Monitors on inputs while labels are late, tuned so that a real shift alerts and a noisy day does not
- **Session 3 · Online evaluation and review queues**: Sample live traces, grade them with a calibrated grader, correct for its errors and send failures to people
- **Session 4 · Retraining and refresh policies**: Retrain on a trigger only when labels are ready, the cost is known and a person approves

#### [day3#review-day-2] Which evidence rolled the canary back?

*Review of Day 2*

**Question:** A new snapshot passed the offline gate and its shadow run, then the canary at 25% rolled back. What made the difference?

- A. The offline gate was run again with more cases
- B. Real traffic at 25% included the Arabic-heavy shift the earlier evidence never saw
- C. The shadow run had failed and was ignored
- D. A reviewer refused the release at 25%

### Session 1: Tracing requests end to end

#### [day3#s1] Tracing requests end to end

*Session 1*

- Add spans with attributes for retrieval, model and tool calls
- Find the slowest step from the traces
- Keep personal data out of span attributes

#### [day3#nabd-is-slow] Crews say Nabd is slow, and everyone blames the model

*The complaint*

- A request runs four kinds of step: retrieval, a model call, a tool call, a second model call.
- Logs say the request took long. They do not say which step.
- A trace records every step of one request as a span, with its parent, its duration and its attributes.

- **Guessing costs.** Swapping to a faster model would have cost a release, an evaluation and a gate, and fixed nothing.

#### [day3#trace-and-spans] One trace per request; one span per step, nested under the request

*Traces and spans*

- invoke_agent Nabd: 497 ms · release nabd-2026.10.1
- · retrieval manuals: 257 ms · index v3 · 3 hits
- · chat steady: 81 ms · 329 tokens in, 16 out
- · execute_tool get_feeder_status: 78 ms
- · chat steady: 80 ms · 369 tokens in, 15 out

"What is the status of feeder F-0213?", from the course's run with the production configuration and the scripted stand-in model.

#### [day3#genai-conventions] Name spans and attributes the way back ends already understand

*OpenTelemetry GenAI semantic conventions*

| Operation | Span name | Attributes |
| --- | --- | --- |
| invoke_agent | invoke_agent Nabd | gen_ai.agent.name |
| retrieval | retrieval manuals | the index version, the hits |
| chat | chat steady | gen_ai.request.model, gen_ai.response.model, gen_ai.usage.input_tokens and output_tokens |
| execute_tool | execute_tool get_feeder_status | gen_ai.tool.name, an error status |

> **Status: Development.** The conventions moved to their own repository and can still change. Pin the version you follow.

#### [day3#tracer-and-exporter] A provider, a processor, an exporter, then a span around each step

*Lab 3.1 · steps 1 and 2*

```python
# file: Lab 3.1
exporter = InMemorySpanExporter()           # production: OTLP to a collector
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(exporter))
tracer = provider.get_tracer("wahaj.nabd")

class TracedNabd(nabd.Nabd):
    def retrieve(self, question):
        with tracer.start_as_current_span("retrieval manuals") as span:
            span.set_attribute("gen_ai.operation.name", "retrieval")
            return super().retrieve(question)
```

#### [day3#time-breakdown] Retrieval took 71% of the request time, the model 27%

*Lab 3.1 · step 3, from the course's run*

| Item | Value |
| --- | --- |
| retrieval | 0.71 |
| chat | 0.27 |
| execute_tool | 0.02 |

Ten crew questions; median request 338 ms. The production configuration has `cache_index=False`: the index is fetched from storage and rebuilt on every request.

#### [day3#measure-again] Cache the index once per process, then measure again with the same spans

*Lab 3.1 · step 4*

- **338 → 82 ms** median request, ten questions
- **0.71 → 0.005** retrieval's share of request time

> **Same instrument, before and after.** A fix is shown by the measurement that found the problem, not by a feeling that it is faster.

#### [day3#no-pii-in-spans] Spans travel far: keep questions and answers out, or redact them first

*What not to record*

- Traces are copied to a collector and kept for weeks, read by people outside the team.
- Crew questions sometimes hold a customer's phone, account number or national ID.
- Record content only when a purpose needs it, and redact before it is recorded.

```text
# file: stretch
Outage on F-0213; customer called from [phone]
about account [account], ID [national-id].
```

#### [day3#checkpoint-1] Where the time goes

*Checkpoint*

**Question:** A trace of a slow Nabd request shows the retrieval span at 260 ms and each model span at 80 ms. The team proposes a faster model. What do you say?

- A. Agree: model calls are usually the slow part
- B. Collect a month of traces before deciding
- C. Add more replicas of Nabd
- D. Fix retrieval first, then measure again with the same spans

#### [day3#lab-3-1] Spans for Nabd and the slowest step

Lab 3.1 · 25 min

Instrument Nabd with OpenTelemetry spans for retrieval, model and tool calls, run ten crew questions, find the slowest step, fix it and measure again.

[D3_1_tracing.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D3_1_tracing.ipynb)

- [ ] A tracer with an in-memory exporter (4 min)
- [ ] Spans for retrieval, model and tool (9 min)
- [ ] Ten requests and the slowest step (7 min)
- [ ] Fix it and measure again (5 min)
- [ ] ✱ Stretch: Redact phone numbers and account numbers in span attributes

### Session 2: Drift, skew and delayed labels

#### [day3#s2] Drift, skew and delayed labels

*Session 2*

- Compute a drift statistic per feature per day
- Tell drift from training and serving skew
- Tune thresholds and persistence to remove false alarms

#### [day3#labels-arrive-late] A fault is known 30 days after the score, and later in the mountains

*Why watch inputs*

**Day 0** the feeder is scored → **Day 30** most labels known → **About day 60** Al-Jabal inspections entered

Until the labels arrive, the only signals are the inputs and the scores. A first cut of the labels is not the truth: Lab 1.4's challenger A learned from one.

#### [day3#psi] The population stability index compares a day's distribution with a reference

*A drift statistic*

```python
# file: Lab 3.2
edges = quantiles(reference, deciles)
ref = share of reference per bin
cur = share of today per bin
psi = sum((cur - ref) * ln(cur / ref))
```

| PSI | Rule of thumb |
| --- | --- |
| below 0.1 | stable |
| 0.1 to 0.25 | a moderate move |
| above 0.25 | a large move |

#### [day3#naive-alerts] PSI above 0.1 against the first week: 51 alerts in 23 days

*Lab 3.2 · steps 1 and 2, from the course's run*

| Item | Value |
| --- | --- |
| temperature | 20 |
| load | 20 |
| dust | 11 |

The heat spike of day 8, the quiet day 17 (120 feeders) and October's seasonal cooling all alert, next to the two real shifts.

#### [day3#three-tuning-rules] Each tuning rule removes one kind of false alarm

*Lab 3.2 · step 3*

- **Rolling reference.** The previous seven days: the season is absorbed, a step is not.
- **Minimum sample.** Fewer than 200 feeders: not judged.
- **Persistence.** Above 0.2 on three judged days in a row.

**51 → 2** alerts: load from day 12 (fired day 14), dust from day 22 (fired day 24)

#### [day3#drift-or-skew] Load stepped up about 10% overnight while temperatures fell: the meters changed, not the grid

*Drift or skew*

- **Skew.** Serving computes a feature differently from training. Here: recalibrated meters read high from day 12. Fix the data; retraining would learn the error.
- **Drift.** The world changes. Here: dust rises from day 21. Watch the labels and consider retraining when they arrive.

Stretch: the median ratio of serving load to the same feeder's batch load steps by about 10% on day 12.

#### [day3#rolling-blind-spot] A rolling reference absorbs a slow drift, so keep one fixed comparison too

*What the tuned monitor cannot see*

- Daily: rolling seven-day reference, for steps and fast changes.
- Monthly: against the training snapshot, for slow moves that matter.
- When labels arrive: the model's own metrics by region, which inputs cannot replace.

> **Three files leave the lab.** The dashboard (PSI per feature per day, with the threshold and the alerts), the alert rules, and the note: shifts found, alarms removed and by which rule, what is no longer visible. Lamya signs the note.

#### [day3#checkpoint-2] One hot day

*Checkpoint*

**Question:** Temperature's PSI is 1.56 on day 8, then below 0.1 the next day. The monitor needs three days in a row above 0.2. What happens, and is it right?

- A. An alert fires: 1.56 is far above 0.2
- B. No alert: a one-day heat spike is weather, and it is logged
- C. The monitor is broken and must be retuned
- D. Retrain to include the hot day

#### [day3#lab-3-2] Two shifts in a replayed month

Lab 3.2 · 25 min

Replay a month of classifier inputs with two planted shifts, alert naively and count the false alarms, then tune the threshold and persistence until only the two shifts alert.

[D3_2_drift_monitors.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D3_2_drift_monitors.ipynb)

- [ ] Drift per feature per day (7 min)
- [ ] Naive alerts and their false alarms (5 min)
- [ ] Tune threshold and persistence (8 min)
- [ ] The note: shifts found, alarms removed (5 min)
- [ ] ✱ Stretch: Measure skew between the training snapshot and serving for one feature

### Session 3: Online evaluation and review queues

#### [day3#s3] Online evaluation and review queues

*Session 3*

- Redact traces before storage and apply a retention rule
- Grade a sample with a calibrated grader and correct the rate
- Route failures and uncertain cases to a review queue

#### [day3#offline-and-online] The gate checks 24 cases once; Nabd answers hundreds of questions a day

*Online evaluation*

1. **Record** traces, redacted
2. **Sample** a fixed number, seeded
3. **Grade** the calibrated grader
4. **Correct** for the grader's errors
5. **Review** failures and a few passes

#### [day3#redact-before-storage] Redact before the trace is stored, not before it is displayed

*Lab 3.3 · step 1*

```python
# file: Lab 3.3
"The customer [name] called from [phone]."
"Account [account], national ID [national-id]."
```

- 87 of 400 questions held personal data.
- Grading needs the answer and the context, not the customer.
- Data never stored needs no access control and no deletion.

#### [day3#raw-rate] The grader fails 29 of 100 sampled answers

*Lab 3.3 · steps 2 and 3, from the course's run*

**0.29** raw failure rate, 95% interval 0.21 to 0.39

- Some failures are good answers with a polite closing sentence the grader cannot find in the manual.
- Some passes are bad: the right words with a wrong number.

#### [day3#rogan-gladen] Correct the raw rate with the grader's sensitivity and specificity

*Lab 3.3 · step 4*

```text
# file: Rogan-Gladen
true = (raw + sp - 1) / (se + sp - 1)
     = (0.29 + 0.817 - 1) / (0.90 + 0.817 - 1)
     = 0.15
```

| On 150 labelled traces | value |
| --- | --- |
| sensitivity: bad answers failed | 0.90 |
| specificity: good answers passed | 0.82 |
| corrected failure rate | 0.15 |
| true rate in the sample | 0.17 |

#### [day3#review-queue] Every failure and one pass in ten go to the reviewers' queue

*Routing*

**32** traces for review from a sample of 100

- Failures: confirm or overturn; each overturn is a calibration label.
- Random passes: what the grader lets through.
- Each review returns to the calibration set, so the grader's numbers stay current.

#### [day3#retention] Keep traces for a stated time, longer only while a reviewer needs them

*Stretch · retention*

- Wahaj's rule in the lab: redacted traces kept 3 days for debugging; those in the review queue held until reviewed.
- On day 7: 221 traces deleted, 179 kept, 32 of them held for review.
- PDPL Article 18: personal data is destroyed once it is no longer needed for its purpose.

#### [day3#checkpoint-3] A grader's rate

*Checkpoint*

**Question:** The grader fails 29% of a sample. On labelled traces it fails 90% of bad answers and passes 82% of good ones. What do you report?

- A. 29% of Nabd's answers are wrong
- B. About 32%: the grader misses a tenth of the bad answers
- C. About 15% after correction, with the raw rate and the sample sizes
- D. Nothing until every trace is reviewed by hand

#### [day3#lab-3-3] Online evaluation and a review queue

Lab 3.3 · 25 min

Redact a week of Nabd traces, sample them, score them with the provided calibrated grader, correct the failure rate for the grader's error and route failures to review.

[D3_3_online_eval.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D3_3_online_eval.ipynb)

- [ ] Redact before storage (6 min)
- [ ] Sample the week (4 min)
- [ ] Grade with the calibrated grader (6 min)
- [ ] Route to review and correct the rate (9 min)
- [ ] ✱ Stretch: A retention rule that deletes traces past their limit

### Session 4: Retraining and refresh policies

#### [day3#s4] Retraining and refresh policies

*Session 4*

- Write a trigger from drift or a schedule that waits for labels
- Estimate the cost of a retraining run
- Require human approval and log the decision

#### [day3#retrain-script] A script retrains on a fixed day each month, whatever the data says

*What Wahaj does today*

- It trained challenger A on August's first cut of labels, before the Al-Jabal inspections.
- It would retrain on the load skew of day 12 if it ran then.
- It promotes without anyone reading the evidence.

- **A policy says.** when to consider retraining, whether the data is ready, what it costs, and who approves.

#### [day3#trigger-and-labels] A trigger proposes; complete labels and the triage decide

*Lab 3.4 · step 1, from the course's run*

| Date | Signal | Decision | Why |
| --- | --- | --- | --- |
| 20 Sep | drift: dust | wait | August labels complete on 2 October |
| 14 Oct | drift: load | no | skew: fix the data with its owner |
| 3 Oct | schedule | retrain | August labels complete |
| 3 Nov | schedule | retrain | September labels complete |

#### [day3#retrain-cost] One retraining run costs 14 node-hours: about 6.3 riyals, of 25.8 left in the budget

*Lab 3.4 · step 2*

**6.31 SAR** extra node-hours on 3 October at the assumed price

- Compute is the small part here.
- The larger costs: the reviewer's hour, a worse model in one region, a rollback.
- For a fine-tuned language model the compute line can dominate: estimate before running.

#### [day3#human-approval] The pipeline trains and gates on its own; a person approves the promotion

*Lab 3.4 · step 3*

- retrain pipeline: refused: the requester cannot approve its own request
- Saqer Al-Dossary: refused: not an approver of fault-risk
- Lamya Al-Muqbil: approved, with the batch, the trigger, the cost and the gate result

#### [day3#end-to-end] August promotes v4; September stops at validation, before any training

*Lab 3.4 · step 4, from the course's run*

- 2026-08: load · validate · train · gate · approve · promote: v3 → v4
- 2026-09: load · validate: 36 duplicates, 807 loads out of range, 14 bad region codes

| AUC | all | Al-Sahil | Al-Jabal |
| --- | --- | --- | --- |
| champion v3 | 0.837 | 0.738 | 0.877 |
| challenger v4 | 0.866 | 0.902 | 0.863 |

#### [day3#index-refresh-policy] An index refresh needs a trigger, a ready evaluation, a cost and an approver too

*Stretch · the same policy for Nabd's index*

- Trigger: the manuals' fingerprint changed (v3 to v4).
- Ready: every changed manual (MM-02, MM-11) has a case in the evaluation set.
- Then the gate of Lab 2.2, and Saqer approves for field operations.

#### [day3#checkpoint-4] A drift alert on the 20th

*Checkpoint*

**Question:** On 20 September a drift alert fires on dust for August's feeders. August's labels are complete on 2 October; a first cut exists. What does the policy do?

- A. Retrain now on the first cut
- B. Ignore the alert: the schedule will retrain anyway
- C. Lower the champion's threshold until labels arrive
- D. Wait for the complete labels, then retrain and gate

#### [day3#lab-3-4] A retraining trigger with a cost and an approval

Lab 3.4 · 25 min

Write the retraining trigger with a cost estimate and a human approval, and test it end to end: the drifted batch promotes a new champion, the corrupt batch stops, both with registry lineage.

[D3_4_retraining_policy.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D3_4_retraining_policy.ipynb)

- [ ] Drift or schedule, and labels ready (6 min)
- [ ] The cost estimate (5 min)
- [ ] Human approval (5 min)
- [ ] Test on the drifted and the corrupt batch (9 min)
- [ ] ✱ Stretch: Treat the manuals index refresh as a release under the same policy

#### [day3#day-3-recap] Traces find the slow step, tuned monitors find real shifts, a calibrated sample measures quality, a policy decides retraining

*Day 3 recap*

- **Traces.** 338 → 82 ms
- **Monitors.** 51 → 2 alerts
- **Online evaluation.** 0.29 raw, 0.15 corrected
- **Retraining.** labels, cost, approval

#### [day3#tomorrow-agents] Operate agents: one versioned bundle, durable state, a replayed incident and a kill switch

*Tomorrow · Day 4*

Tomorrow Mubadir closes a ticket on stale data, creates duplicates after a crash and loops on a pending outage. You replay, fix and stop it.

## Day 4: Operate agents

The agent as a versioned bundle, durable and idempotent, replayed when it fails and stopped when it runs away

#### [day4#title] Operate agents

*SDAIA Academy · Operating Machine Learning and Language Model Systems*

Day 4: The agent as a versioned bundle, durable and idempotent, replayed when it fails and stopped when it runs away

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-305

#### [day4#agenda] Operate agents

*Today*

- **Session 1 · An agent is a bundle**: Prompt, tools, harness settings and sandbox policy are versioned together, apart from the session log
- **Session 2 · Durable execution and safe retries**: Checkpoints let a crashed run resume; idempotency keys make a retry safe
- **Session 3 · Replay to reproduce incidents**: Recorded model and tool responses make an incident reproducible and turn it into a regression case
- **Session 4 · Budgets, gateways and kill switches**: Step and spend limits at the gateway, a kill switch per agent version, and sessions that survive the stop

#### [day4#review-day-3] Which alarm should stay?

*Review of Day 3*

**Question:** Three input alerts fired last week: dust high for one day, load 10% higher every day since Tuesday's meter recalibration, temperature slowly falling over a month. Which one needs action today?

- A. Dust, because its PSI was the largest
- B. Temperature, because it moved for a month
- C. Load: a step since a known change, likely skew, so call the data owner
- D. None: inputs do not matter until labels arrive

### Session 1: An agent is a bundle

#### [day4#s1] An agent is a bundle

*Session 1*

- Separate the session log, the harness and the sandbox
- Version an agent as one bundle with a content hash
- Run the agent only from a released bundle

#### [day4#meet-mubadir] Mubadir is a model in a loop that reads a report, calls tools and writes tickets

*The agent*

1. **Report** "no power, account ACC-…"
2. **find_customer** feeder, region
3. **get_outage** active, restored, pending, none
4. **Write** link, open a ticket and notify, or close

Each turn the model returns one JSON action; the harness runs it through the services and logs every event.

#### [day4#harness-sandbox-log] The harness runs the loop, the sandbox limits it, the session log records it

*Three things people mix up*

- **Harness.** Steps, retries, timeouts, guards: `harness.yaml` and its code.
- **Sandbox.** Allowed tools, readable fields, no network: `sandbox.yaml`.
- **Session log.** What one session did. Produced by a run, never released.

#### [day4#bundle-version] Four files, one content version: the bundle

*Lab 4.1 · step 2*

```json
// file: releases/mubadir-13ba248db039/manifest.json
{"version": "mubadir-13ba248db039",
 "files": {"harness.yaml": "58774e13…", "prompt.md": "21280ad4…",
           "sandbox.yaml": "30f31ccf…", "tools.json": "ad9380b7…"},
 "released_by": "Dhafer Al-Hazzani"}
```

The version is a hash of the four file hashes, the same idea as Day 1's release manifest.

#### [day4#one-tool-schema] Adding one property to one tool moves the version

*Lab 4.1 · step 3*

**13ba248 → fe28888** after adding `customer_words` to create_ticket

- Only `tools.json` differs between the manifests.
- The model now sees a different tool list: a behaviour change with no prompt edit.
- So it replays the regression suite before release (Session 3).

#### [day4#run-from-release] Run from the released folder, and write the bundle version into every session log

*Lab 4.1 · step 4, from the course's run*

- find_customer: ACC-40000137 → feeder F-2414, Al-Wadi
- get_outage: F-2414 → none
- create_ticket: → OT-31001
- notify_crew: OT-31001 → notified
- final: I opened ticket OT-31001 for your feeder F-2414 and sent it to the duty crew. · bundle mubadir-13ba248db039

#### [day4#bundle-in-manifest] The bundle version is Mubadir's line in the release manifest

*Closing the loop with Day 1*

| System | What names its release |
| --- | --- |
| Fault-risk classifier | registry version behind the champion alias, data snapshot, code hash |
| Nabd | release file: prompt, model, index fingerprint, tool schemas |
| Mubadir | bundle version: prompt, tools, harness, sandbox |

#### [day4#checkpoint-1] A setting, not a prompt

*Checkpoint*

**Question:** A developer raises Mubadir's `max_steps` from 10 to 30 in `harness.yaml` and says no release is needed because the prompt did not change. What do you answer?

- A. Agree: only the prompt changes what the agent does
- B. It is a new bundle version: harness settings change behaviour and cost
- C. It is enough to note it in the session log
- D. Only a sandbox change needs a release

#### [day4#lab-4-1] Mubadir as one versioned bundle

Lab 4.1 · 25 min

Package Mubadir's prompt, tool schemas, harness settings and sandbox policy as one bundle with a content version, change one tool and watch the version move, then run the agent from the bundle.

[D4_1_agent_bundle.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D4_1_agent_bundle.ipynb)

- [ ] What changes Mubadir's behaviour (5 min)
- [ ] Build the bundle and its version (8 min)
- [ ] Change one tool schema (6 min)
- [ ] Run the agent from the bundle (6 min)
- [ ] ✱ Stretch: Refuse to start when the running bundle is not the released one

### Session 2: Durable execution and safe retries

#### [day4#s2] Durable execution and safe retries

*Session 2*

- Resume a crashed agent run from its last checkpoint
- Explain why a retry after a timeout can repeat a write
- Make a write tool idempotent with a key

#### [day4#two-complaints] A crew sent twice to one feeder, and a session that started again from the beginning

*What reached Dhafer this month*

- **Restart.** A deployment restarted the pod between creating the ticket and notifying the crew. The session started over and opened a second ticket.
- **Retry.** The ticket service committed, then timed out. The harness retried and wrote again.

#### [day4#checkpointed-graph] A checkpointer saves the state after every step, under a thread id

*Durable execution*

```python
# file: Lab 4.2
g = StateGraph(Ticket)
g.add_node("find_customer", find_customer)   # ... get_outage, create_ticket, notify_crew
g.add_edge(START, "find_customer")
graph = g.compile(checkpointer=SqliteSaver(sqlite3.connect("checkpoints.db")))

graph.invoke({"account": "ACC-40000137"}, {"configurable": {"thread_id": "S-4202"}})
graph.invoke(None, {"configurable": {"thread_id": "S-4202"}})   # resume after a crash
```

#### [day4#restart-vs-resume] Restarting opened a second ticket; resuming ran only the missing step

*Lab 4.2 · step 2, from the course's run*

| After the crash before notify_crew | Tickets | Notified |
| --- | --- | --- |
| restart from the beginning | 2 | OT-31001 no, OT-31002 yes |
| resume the saved thread | 1 | OT-31001 yes |

On resume, the saved state's next step was `notify_crew`.

#### [day4#timeout-is-not-failure] A timeout does not say whether the write happened

*Lab 4.2 · step 3*

- create_ticket: the service commits OT-31001
- timeout: ticket service did not answer within 5 s
- retry: create_ticket → OT-31002
- notify_crew: OT-31002 · OT-31001 is never notified

#### [day4#idempotency-key] An idempotency key names one intended write; a repeat returns the first result

*Lab 4.2 · step 4*

```python
# file: Lab 4.2
key = hash(session_id, "create_ticket", args)
# same intent, same key, on every retry
# a different report gets a different key
```

- timeout: after the commit
- retry: OT-31001, replayed: true
- tickets: one, notified

#### [day4#two-fixes] Checkpoints protect the steps between calls; keys protect the call itself

*Which fix for which failure*

- **Checkpoint.** The process dies between steps. Resume from the saved state; finished steps do not run again.
- **Idempotency key.** The answer to one write is lost. Retry with the same key; the service does not write twice.

> **Both, for every agent that writes.** The capstone's agent incident is a duplicate write.

#### [day4#checkpoint-2] Checkpointed, still duplicated

*Checkpoint*

**Question:** Mubadir's flow now has a checkpointer. A ticket service timeout still produced two tickets for one report. Why?

- A. The checkpointer was not saving
- B. The ticket database lost the first ticket
- C. The retry ran inside one step, and the service had no key to recognise it
- D. The model asked for two tickets

#### [day4#lab-4-2] Crash, resume, and no duplicate tickets

Lab 4.2 · 25 min

Run Mubadir's ticket flow as a checkpointed graph, crash it mid-task and resume, then reproduce the duplicate ticket a retry creates and fix the tool with an idempotency key.

[D4_2_durable_retries.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D4_2_durable_retries.ipynb)

- [ ] The ticket graph with a checkpointer (6 min)
- [ ] Crash mid-task and resume (6 min)
- [ ] A retry after a timeout: two tickets (6 min)
- [ ] An idempotency key: one ticket (7 min)
- [ ] ✱ Stretch: Resume the session from a second process

### Session 3: Replay to reproduce incidents

#### [day4#s3] Replay to reproduce incidents

*Session 3*

- Replay a recorded session deterministically
- Find the cause of an incident in the replayed trace
- Add the incident to the regression suite

#### [day4#inc-0412] Mubadir told a customer in Al-Jabal that power was back; it never was

*INC-0412 · invented for the course*

**Customer:** Salam, my house has had no power for two hours. Account ACC-40005754.

**Mubadir (weak example):** Power is restored on your feeder F-3350. If you are still without power, reply to this message.

- **40 minutes later.** The customer calls again. The control room confirms the outage never ended. The report had been closed.

#### [day4#read-the-trace] Step 2 returned "restored", 140 minutes old, and the agent closed the report on it

*Lab 4.3 · step 1*

- 1 find_customer: → F-3350, Al-Jabal
- 2 get_outage: → restored, ticket OT-30412, age 140 minutes
- 3 close_report: → closed
- 4 final: Power is restored on your feeder F-3350.

#### [day4#replay-not-rerun] Replay from the recording, not a rerun against today's services

*Lab 4.3 · step 2*

- The recording holds every model output and every tool response.
- Replay feeds them back through today's harness code: no model, no services.
- The same wrong answer comes back every time.

- **A rerun would not.** The replica has caught up and a hosted model can answer differently: the failure would hide.

#### [day4#freshness-guard] A guard in the harness blocks a close on a stale status

*Lab 4.3 · step 3*

```python
# file: Lab 4.3
def freshness_guard(action, history):
    if action["tool"] != "close_report":
        return None
    last = latest get_outage result in history
    if last["status"] != "restored":
        return "not restored"
    if last["age_minutes"] > 15:
        return f"status is {last['age_minutes']} minutes old: confirm with the control room"
```

Replayed with the guard: blocked at step 3, "status is 140 minutes old (limit 15)".

#### [day4#regression-suite] The incident becomes a sixth case; the fix keeps the other five passing

*Lab 4.3 · step 4, from the course's run*

| Case | Without the guard | With the guard |
| --- | --- | --- |
| new outage, known outage, record change, unknown account | pass | pass |
| restored 6 minutes ago | pass | pass |
| INC-0412: restored 140 minutes ago | fail | pass |

#### [day4#suite-new-bundle] A bundle without close_report changes exactly one case, as intended

*Stretch · the suite against a new bundle*

- The sandbox no longer allows `close_report`: closing goes to a person.
- Replayed suite: "restored 6 minutes ago" now fails, everything else passes.
- Update that case's expectation in the same change, with the reason.

#### [day4#checkpoint-3] Reproduce it

*Checkpoint*

**Question:** The team wants to reproduce INC-0412 by sending the same customer report to Mubadir today. Why will that probably not show the failure?

- A. The replica has caught up and the model may answer differently: only the recording holds what happened
- B. The customer's account has been deleted
- C. The new guard will block it
- D. Agents never behave the same way twice

#### [day4#lab-4-3] Replay incident INC-0412

Lab 4.3 · 25 min

Replay the recorded session in which Mubadir told a customer that power was back while the outage was live, find the cause in the trace, fix the harness and add the case to the regression suite.

[D4_3_replay_incident.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D4_3_replay_incident.ipynb)

- [ ] Read the recorded trace (5 min)
- [ ] Replay it: the same wrong answer (7 min)
- [ ] Fix the harness (7 min)
- [ ] The new regression case and the suite (6 min)
- [ ] ✱ Stretch: Replay the whole suite against a new bundle

### Session 4: Budgets, gateways and kill switches

#### [day4#s4] Budgets, gateways and kill switches

*Session 4*

- Set step and spend limits at a gateway
- Stop a runaway agent with a kill switch
- Keep the stopped sessions and hand them to a person

#### [day4#runaway-session] The outage service answered "pending" and Mubadir asked again 79 times

*14 October*

**80 calls · 0.169 SAR** one session with no limits, from the course's run

- Input tokens per call grew from 127 to 3,609: each call resends the conversation.
- The cost of a loop grows with the square of its length.
- This is Day 2's expensive days for Mubadir.

#### [day4#gateway-policy] Every model call passes the gateway, which checks steps, session spend and the day's budget

*Lab 4.4 · step 2*

```python
# file: Lab 4.4
def policy(state):
    if state["session_steps"] >= 12:      return "step limit"
    if state["session_spend"] >= 0.01:    return "session spend limit"
    if state["day_spend"] >= 2.90:        return "daily budget"   # 90 SAR / 31 days
```

The same runaway session: stopped by the gateway after 12 calls, 0.0057 SAR.

#### [day4#kill-switch] After two sessions hit the step limit, one switch stopped the version

*Lab 4.4 · step 3, from the course's run*

- S-4411: stopped: step limit, 12 calls
- S-4412: stopped: step limit, 12 calls
- kill switch: mubadir-2026.10.2, by Dhafer Al-Hazzani
- S-4413 to S-4416: refused before the first call

24 model calls instead of 72: the switch saved 48.

#### [day4#sessions-kept] Stopping the agent must not drop the customers it was serving

*Lab 4.4 · step 4*

- Every session is in the store with its messages and status.
- Six stopped sessions go to customer care with the account, steps, spend and last tool result.
- The same sessions can be replayed for the post-incident note.

**6 of 6** stopped sessions handed over, none lost

#### [day4#litellm-budgets] LiteLLM puts budgets on keys, users and teams; one key per version makes the switch a deletion

*Stretch · the same limits in a proxy*

```json
// file: POST /key/generate
{"models": ["steady"], "max_budget": 2.9, "budget_duration": "1d",
 "metadata": {"agent": "mubadir", "version": "mubadir-2026.10.2"}}
```

Budgets need the proxy's database (PostgreSQL); rate limits answer HTTP 429. Per-session step limits stay in the harness and the gateway policy.

#### [day4#agent-runbook] A runbook says how to detect, who decides, how to roll back and how to stop

*Runbooks · recap from AE-205, now for three systems*

| System | Detect | Decide | Roll back | Stop |
| --- | --- | --- | --- | --- |
| Classifier | contract report, drift alert, AUC by region | Lamya | move the champion alias back | pause the retraining trigger |
| Nabd | canary analysis, online evaluation, spans | Dhafer, with Saqer | abort the rollout, redeploy the last digest | pin the previous release |
| Mubadir | gateway stops, spend per resolved report | Dhafer or Mutab | release the previous bundle | kill switch for the version, then the handover |

> **Written before the incident.** Each cell names a signal or a command from this week's labs. The capstone's runbook has this shape.

#### [day4#checkpoint-4] Six sessions looping

*Checkpoint*

**Question:** Every session of Mubadir's new version loops on the same pending status. Each stops at the step limit. What does the duty engineer do?

- A. Nothing: the step limit already stops each session
- B. Stop all of Mubadir, every version
- C. Raise the step limit so sessions can finish
- D. Turn on the kill switch for that version and hand its sessions to people

#### [day4#lab-4-4] Limits and a kill switch at the gateway

Lab 4.4 · 25 min

Let a runaway Mubadir session loop without limits, then set step and spend limits at the gateway, stop the agent version with the kill switch and hand its sessions to a person without losing them.

[D4_4_budgets_killswitch.ipynb](https://sdaiaacademy.github.io/ae-305/labs/D4_4_budgets_killswitch.ipynb)

- [ ] The runaway session without limits (4 min)
- [ ] Step and spend limits (8 min)
- [ ] The kill switch (7 min)
- [ ] Sessions kept and handed over (6 min)
- [ ] ✱ Stretch: The same limits as a LiteLLM proxy configuration

#### [day4#day-4-recap] A bundle you can name, a run that survives a crash, an incident you can replay, an agent you can stop

*Day 4 recap*

- **Bundle.** four files, one version
- **Durable.** checkpoint and key
- **Replay.** guard and case
- **Stop.** limits, switch, handover

#### [day4#capstone-kickoff] A release week at Wahaj: each event stopped, shipped or rolled back on evidence

*Capstone kickoff*

- **Monday and Tuesday.** The scheduled retrain meets the corrupt September batch, then the corrected re-delivery: valid, and does it pass the gate?
- **Wednesday.** The provider updates Nabd's model: gate, canary, ship or roll back.
- **Thursday.** A Mubadir incident: replay, fix, add the case, keep the sessions.

The events, their data and a starter are in `labs/capstone/`. Submit a public repository with the pipeline logs, the release log, the runbook and timestamped traces.

#### [day4#tomorrow-capstone] Capstone: defend your release week for eight minutes

*Tomorrow · Day 5*

Show the release log and the runbook, then diagnose one fault the assessor injects, live, from your traces and logs.

## Capstone: Capstone: a release week and its defence

Eight minutes per participant: the release log, the runbook and one injected fault diagnosed live; questions are inside the eight minutes

#### [capstone#title] Capstone: a release week and its defence

*SDAIA Academy · Operating Machine Learning and Language Model Systems*

Capstone: Eight minutes per participant: the release log, the runbook and one injected fault diagnosed live; questions are inside the eight minutes

AI Engineering Track · 4 teaching days + capstone day · 8 min talk and demo · AE-305

#### [capstone#agenda] How the presentations run

*Capstone*

- **Expectations and final prep**: the rubric, a last rehearsal, then the first presentations
- **Presentations**: eight minutes each, questions included
- **Review and closing**: peer feedback, the trainer's review, what next

#### [capstone#rubric] The rubric

*How presentations are scored*

| Item | Value |
| --- | --- |
| Pipelines and gates | 25% |
| Delivery and rollback | 20% |
| Observability | 20% |
| Agent operations | 20% |
| Runbook and reproducibility | 15% |

> **Show results from at least two measured runs.** A claim without a number is a plan, not a result.

#### [capstone#format] 8 minutes for each defence, questions included

*Format*

- **1 · The release log · 2 min.** Each decision of the week, the metric it was taken on, the evidence file.
- **2 · The injected fault · 5 min.** Find it from traces and logs, say what you would do and who decides, do the first step.
- **3 · The runbook · 1 min.** What this week would change in it.

> **Peer feedback.** After each defence, everyone writes one strength, one question and one suggestion.

#### [capstone#release-week] Four events, four decisions, each on a stated metric

*What every repository shows*

| Day | Event | The reference run decided |
| --- | --- | --- |
| Monday | scheduled retrain on the corrupt September batch | stopped at validation: duplicates, Al-Hadba load as fractions, bad region codes |
| Tuesday | the corrected re-delivery | gate rejects: Al-Hadba 0.037 below the champion, tolerance 0.03 |
| Wednesday | the provider's new snapshot for Nabd | shipped: offline gate, then 5%, 25% and 50% passed |
| Thursday | INC-0419, two tickets for one report | open until the participant's fix gives one ticket |

#### [capstone#running-order] Who presents when

*Running order*

| # | Presenter | Project |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |
| 4 |  |  |
| 5 |  |  |
| 6 |  |  |
| 7 |  |  |
| 8 |  |  |

#### [capstone#final-prep] Final prep · 20 minutes

*Before the first presentation*

Rehearse once, record a backup, try the demo on this screen.

#### [capstone#now-presenting] Talk and demo

*Now presenting*

#### [capstone#review] What the presentations showed

*Trainer review*

- **Strongest patterns.** What several projects got right.
- **Common gaps.** What most projects would fix next.
- **One surprise.** Something nobody expected.

#### [capstone#what-next] Keep going

*After the course*

- **Your project stays yours:** keep it reproducible and add the next improvement you named today
- **The follow-up task, within 30 days:** write a release manifest and one gate for a system you run, and send the evidence
- **Next Academy course:** AE-404 Harness Engineering for Long-Running and Multi-Agent Systems

#### [capstone#thanks] Thank you

*SDAIA Academy*

Operating Machine Learning and Language Model Systems
