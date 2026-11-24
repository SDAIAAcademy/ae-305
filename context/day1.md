---
course: "Operating Machine Learning and Language Model Systems"
code: "AE-305"
version: "2027.2.0"
deck: "day1"
day: 1
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-305/slides/day1.html"
---

# Operating Machine Learning and Language Model Systems

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
