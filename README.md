<!-- academy:title -->
# Operating Machine Learning and Language Model Systems

تشغيل أنظمة تعلم الآلة والنماذج اللغوية

AI Engineering Track · SDAIA Academy · AE-305 · Level 300

Run models, assistants and agents in production as versioned releases that are gated, observed and safe to roll back

Participants run three systems of a fictional electricity distribution company in production: a fault-risk classifier retrained on monthly batches with planted drift, a field-crew assistant with retrieval and two tools, and an outage-ticket agent. They version everything that changes behaviour as one release unit, build pipelines with validation and promotion gates, release through canary stages with automatic rollback, trace requests, monitor drift and online quality, and keep the agent alive through crashes and runaway loops. Evaluators come ready-made from AE-303.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

**Course page:** https://sdaiaacademy.github.io/ae-305/
<!-- /academy:title -->

## Outcomes

| | Outcomes | Level | Evidence |
|---|---|---|---|
| LO1 | Prepare a release manifest that versions data, code, configuration, model, prompt, retrieval index and tool schemas as one unit, given two runs of the three systems that behave differently | Applied | a manifest and the unrecorded change found between the runs |
| LO2 | Build a retraining pipeline, started by a drift or schedule trigger, with data validation and a promotion gate that compares challenger and champion overall and by region, given monthly feeder batches, one of them corrupt and one drifted | Performance | a triggered run that promotes on the drifted batch and stops on the corrupt one, with registry lineage |
| LO3 | Deliver language model changes through an evaluation gate and a canary stage with an automatic rollback trigger, given a prompt edit, a model swap and an index refresh, one of which regresses | Performance | logs showing two releases shipped and one rolled back on a stated metric |
| LO4 | Configure request tracing, drift monitors and online evaluation with a review queue, and tune alert thresholds, given a replayed month of traffic with two planted shifts | Applied | a dashboard, alert rules and a note on shifts found and false alarms removed |
| LO5 | Diagnose an agent incident by replaying recorded traces and fix it with idempotent tools, durable state or a budget, given a recorded failure of the ticket agent | Performance | the failure reproduced, a fix and a new regression case |
| LO6 | Measure cost per successful outcome and resource use for each system and set budget alerts, given a month of token, compute and outcome logs | Applied | a cost table by system and team, with alert rules |

<!-- academy:units -->
## Units

| Unit | Title | Sessions | Slides |
|---|---|---|---|
| Day 1 | Version and build | What changes behaviour; Registries and lineage; Pipelines with validation; Promotion gates | [`slides/day1.html`](slides/day1.html) |
| Day 2 | Deliver | Continuous delivery for models; Language model releases; Shadow and canary on evidence; Cost and capacity signals | [`slides/day2.html`](slides/day2.html) |
| Day 3 | Observe | Tracing requests end to end; Drift, skew and delayed labels; Online evaluation and review queues; Retraining and refresh policies | [`slides/day3.html`](slides/day3.html) |
| Day 4 | Operate agents | An agent is a bundle; Durable execution and safe retries; Replay to reproduce incidents; Budgets, gateways and kill switches | [`slides/day4.html`](slides/day4.html) |
| Capstone | Capstone: a release week and its defence |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**Wahaj Electricity Distribution Company.** Wahaj is a fictional electricity distributor with six regions and 4,800 feeders that runs three systems: a feeder fault-risk classifier retrained on monthly batches, Nabd, a field-crew assistant over the maintenance manuals with two tools, and Mubadir, an outage-ticket agent. Participants version, gate, release, observe and repair all three on synthetic data generated with a fixed seed: twelve monthly batches with one corrupt and one drifted, two versions of the manuals, a replayed month of traffic with two planted shifts, recorded agent traces with one incident, and a month of cost logs.

The people of the case: Dhafer Al-Hazzani (MLOps platform lead, owns releases), Lamya Al-Muqbil (owner of the fault-risk model), Saqer Al-Dossary (field operations supervisor), Mutab Al-Shalhoub (control-room duty engineer, approves risky agent actions) and Nouf Al-Sadhan (data protection officer). They and the company are invented.

## Before the course

The guided pre-work takes about two hours:

1. Run `labs/00_setup_check.ipynb` in Google Colab or locally with `uv`. It checks the packages, asks Nabd one
   question and says whether a free hosted model key works. Without a key every lab still runs, on a scripted stand-in
   model.
2. Refresh two things from the prerequisite courses: building a container image with a CI workflow (AE-205), and
   reading an evaluation report with pass rates and intervals (AE-203). The checkpoints of Day 1 assume both.
3. Read the case study above and bring one question about how your own entity releases a model or an assistant
   today.

## After the course

The tracked follow-up task is due 30 days after the capstone. Pick one system you run or support. Write its release
manifest: data, code, configuration, model, prompt, index and tools, whichever apply. Add one gate it does not have
yet, such as a data contract, an evaluation floor, a canary trigger or a step limit. Send the trainer a link to
synthetic or anonymised evidence that the gate ran. Nothing internal leaves your entity.

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | A release manifest and the unrecorded change | [`D1_1_release_manifest.ipynb`](labs/D1_1_release_manifest.ipynb) |
| 1.2 | Day 1 · Session 2 | Reproduce a model from the registry | [`D1_2_registry_lineage.ipynb`](labs/D1_2_registry_lineage.ipynb) |
| 1.3 | Day 1 · Session 3 | A validation step that stops training | [`D1_3_validation_step.ipynb`](labs/D1_3_validation_step.ipynb) |
| 1.4 | Day 1 · Session 4 | Champion, challenger and the regional gate | [`D1_4_promotion_gate.ipynb`](labs/D1_4_promotion_gate.ipynb) |
| 2.1 | Day 2 · Session 1 | Merge to staging to production | [`D2_1_delivery_pipeline.ipynb`](labs/D2_1_delivery_pipeline.ipynb) |
| 2.2 | Day 2 · Session 2 | Three changes through the evaluation gate | [`D2_2_llm_release_gate.ipynb`](labs/D2_2_llm_release_gate.ipynb) |
| 2.3 | Day 2 · Session 3 | A canary that rolls itself back | [`D2_3_canary_rollback.ipynb`](labs/D2_3_canary_rollback.ipynb) |
| 2.4 | Day 2 · Session 4 | Cost per successful outcome | [`D2_4_cost_signals.ipynb`](labs/D2_4_cost_signals.ipynb) |
| 3.1 | Day 3 · Session 1 | Spans for Nabd and the slowest step | [`D3_1_tracing.ipynb`](labs/D3_1_tracing.ipynb) |
| 3.2 | Day 3 · Session 2 | Two shifts in a replayed month | [`D3_2_drift_monitors.ipynb`](labs/D3_2_drift_monitors.ipynb) |
| 3.3 | Day 3 · Session 3 | Online evaluation and a review queue | [`D3_3_online_eval.ipynb`](labs/D3_3_online_eval.ipynb) |
| 3.4 | Day 3 · Session 4 | A retraining trigger with a cost and an approval | [`D3_4_retraining_policy.ipynb`](labs/D3_4_retraining_policy.ipynb) |
| 4.1 | Day 4 · Session 1 | Mubadir as one versioned bundle | [`D4_1_agent_bundle.ipynb`](labs/D4_1_agent_bundle.ipynb) |
| 4.2 | Day 4 · Session 2 | Crash, resume, and no duplicate tickets | [`D4_2_durable_retries.ipynb`](labs/D4_2_durable_retries.ipynb) |
| 4.3 | Day 4 · Session 3 | Replay incident INC-0412 | [`D4_3_replay_incident.ipynb`](labs/D4_3_replay_incident.ipynb) |
| 4.4 | Day 4 · Session 4 | Limits and a kill switch at the gateway | [`D4_4_budgets_killswitch.ipynb`](labs/D4_4_budgets_killswitch.ipynb) |
<!-- /academy:labs -->

## Capstone

A simulated release week in which a corrupt batch, a provider model update and an agent incident arrive; the participant gates, ships or rolls back each and submits a public repository with pipeline logs, a release log and a runbook, then defends it for eight minutes while the assessor injects one further fault

**Submission:** A public GitHub repository with the pipeline logs, the release log, the runbook and timestamped trace files of the release week, built from the starter in labs/capstone/. Then an eight-minute live defence in which the assessor injects one further fault and the participant diagnoses it from traces and logs.

The week runs from Monday 2 to Thursday 5 November 2026. On Monday the scheduled retrain meets the corrupt September
batch. On Tuesday the corrected batch arrives. On Wednesday the provider moves Nabd's model alias to a new snapshot.
On Thursday Mubadir opens two tickets for one report. `labs/capstone/README.md` gives the requirements, the rubric
(pipelines and gates 25, delivery and rollback 20, observability 20, agent operations 20, runbook and
reproducibility 15), the starter commands and the timeline. `labs/capstone/TEMPLATE_README.md` is the shape of the
participant's README.

## Prerequisites

- AE-205 Deploying AI Services: Containers, Serving and Monitoring
- AE-203 Building Applications on Language Models
- Builds a container image and a continuous-integration workflow
- Reads an evaluation report with pass rates and intervals
- Has built a tool-calling agent, as in AE-302 or equivalent

<!-- academy:tools -->
## Tools

Each line is a capability; the examples are interchangeable.

- **Experiment tracking and model registry:** MLflow, Kubeflow Model Registry
- **Data versioning:** DVC, lakeFS
- **Pipeline orchestration:** Prefect, Apache Airflow, Kubeflow Pipelines
- **Validation and drift detection:** pandera, Evidently, SciPy
- **Continuous integration and progressive delivery:** Argo Rollouts, Argo CD, GitLab CI or GitHub Actions
- **Tracing, metrics and dashboards:** OpenTelemetry with Langfuse, Arize Phoenix, Prometheus and Grafana
- **Model and agent gateway:** LiteLLM, Agent Router, agentgateway
- **Durable execution:** Temporal, a state-graph framework with a checkpointer
- **Single-node local cluster:** kind, k3d
<!-- /academy:tools -->

<!-- academy:sources -->
## Sources

### Registries, pipelines and delivery

- [MLflow: Model Registry (aliases, tags, models:/name@alias)](https://mlflow.org/docs/latest/ml/model-registry/)
- [Argo Rollouts: Canary strategy (setWeight, pause, analysis, abort)](https://argo-rollouts.readthedocs.io/en/stable/features/canary/)
- [GitHub Docs: Deployments and environments (required reviewers)](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)

### Observation and gateways

- [OpenTelemetry: Semantic conventions for generative AI spans](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md)
- [LiteLLM: Budgets and rate limits for keys, users and teams](https://docs.litellm.ai/docs/proxy/users)

### National references

- [SDAIA: Personal Data Protection Law](https://sdaia.gov.sa/en/SDAIA/about/Documents/PersonalDataProtectionLaw.pdf)
- [SDAIA (NDMO): Data Classification Policy](https://sdaia.gov.sa/en/SDAIA/about/Documents/DataClassificationPolicy.pdf)
- [SDAIA (NDMO): Data Management and Personal Data Protection Standards](https://sdaia.gov.sa/en/SDAIA/about/Documents/DataManagementPersonalDataProtectionStandards.pdf)
<!-- /academy:sources -->

### National references

- Personal Data Protection Law and its implementing regulations: https://sdaia.gov.sa/en/SDAIA/about/Documents/PersonalDataProtectionLaw.pdf (implementing regulation: https://sdaia.gov.sa/en/SDAIA/about/Documents/ImplementingRegulationPersonalDataProtectionLaw.pdf)
- NDMO Data Classification Policy: https://sdaia.gov.sa/en/SDAIA/about/Documents/DataClassificationPolicy.pdf
- NDMO Data Management and Personal Data Protection Standards: https://sdaia.gov.sa/en/SDAIA/about/Documents/DataManagementPersonalDataProtectionStandards.pdf
- National AI Risk Management Framework: issued by SDAIA; no official address was found on SDAIA's regulations page when this course was built, so it is cited by name only
