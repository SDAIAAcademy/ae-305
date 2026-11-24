---
course: "Operating Machine Learning and Language Model Systems"
code: "AE-305"
version: "2027.2.0"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-305/index.html"
---

# Operating Machine Learning and Language Model Systems

تشغيل أنظمة تعلّم الآلة والنماذج اللغوية

AI Engineering Track · 4 teaching days + capstone day · 26 hours · Level 300

Run models, assistants and agents in production as versioned releases that are gated, observed and safe to roll back

Participants run three systems of a fictional electricity distribution company in production: a fault-risk classifier retrained on monthly batches with planted drift, a field-crew assistant with retrieval and two tools, and an outage-ticket agent. They version everything that changes behaviour as one release unit, build pipelines with validation and promotion gates, release through canary stages with automatic rollback, trace requests, monitor drift and online quality, and keep the agent alive through crashes and runaway loops. Evaluators come ready-made from AE-303.

**Who it is for:** Practitioners. Engineers who have completed the level 200 set or can show equivalent work: a deployed model or language model application they built and can explain.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

## The case study

**Wahaj Electricity Distribution Company.** Wahaj is a fictional electricity distributor with six regions and 4,800 feeders that runs three systems: a feeder fault-risk classifier retrained on monthly batches, Nabd, a field-crew assistant over the maintenance manuals with two tools, and Mubadir, an outage-ticket agent. Participants version, gate, release, observe and repair all three on synthetic data generated with a fixed seed: twelve monthly batches with one corrupt and one drifted, two versions of the manuals, a replayed month of traffic with two planted shifts, recorded agent traces with one incident, and a month of cost logs.

## The course

### Day 1: Version and build

Slides: https://sdaiaacademy.github.io/ae-305/slides/day1.md

- **Session 1: What changes behaviour**
  - Name every part that changes the behaviour of a model, an assistant and an agent
  - Pin a provider model to an identifier that does not move
  - Write a release manifest and diff two of them
  - [Lab 1.1: A release manifest and the unrecorded change (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D1_1_release_manifest.ipynb)
- **Session 2: Registries and lineage**
  - Read a model version, its alias and its lineage tags
  - Rebuild a data snapshot from its content hash
  - Reproduce a colleague's model and prove it matches
  - [Lab 1.2: Reproduce a model from the registry (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D1_2_registry_lineage.ipynb)
- **Session 3: Pipelines with validation**
  - Write a data contract as a schema with types, ranges and allowed values
  - Add batch checks: row count and duplicate keys
  - Make validation a pipeline step that stops the run with a report
  - [Lab 1.3: A validation step that stops training (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D1_3_validation_step.ipynb)
- **Session 4: Promotion gates**
  - Score champion and challengers on the same holdout
  - Compare overall and by region with a stated tolerance
  - Promote by moving the registry alias, with the reason logged
  - [Lab 1.4: Champion, challenger and the regional gate (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D1_4_promotion_gate.ipynb)

### Day 2: Deliver

Slides: https://sdaiaacademy.github.io/ae-305/slides/day2.md

- **Session 1: Continuous delivery for models**
  - Promote one artefact by digest instead of rebuilding it
  - Add a staging check and an approval step before production
  - Keep a deployment log a reviewer can audit
  - [Lab 2.1: Merge to staging to production (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D2_1_delivery_pipeline.ipynb)
- **Session 2: Language model releases**
  - Describe each language model change as a change to the release unit
  - Run a provided evaluation gate on a champion and three candidates
  - Block a release on the metric that matters, not on the average
  - [Lab 2.2: Three changes through the evaluation gate (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D2_2_llm_release_gate.ipynb)
- **Session 3: Shadow and canary on evidence**
  - Compare a candidate in shadow without user impact
  - Analyse a canary window with a minimum sample
  - Roll back automatically on a quality or latency trigger
  - [Lab 2.3: A canary that rolls itself back (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D2_3_canary_rollback.ipynb)
- **Session 4: Cost and capacity signals**
  - Price a month of token and compute usage
  - Compute cost per successful outcome and utilisation per system
  - Show cost back by team and set a budget alert
  - [Lab 2.4: Cost per successful outcome (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D2_4_cost_signals.ipynb)

### Day 3: Observe

Slides: https://sdaiaacademy.github.io/ae-305/slides/day3.md

- **Session 1: Tracing requests end to end**
  - Add spans with attributes for retrieval, model and tool calls
  - Find the slowest step from the traces
  - Keep personal data out of span attributes
  - [Lab 3.1: Spans for Nabd and the slowest step (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D3_1_tracing.ipynb)
- **Session 2: Drift, skew and delayed labels**
  - Compute a drift statistic per feature per day
  - Tell drift from training and serving skew
  - Tune thresholds and persistence to remove false alarms
  - [Lab 3.2: Two shifts in a replayed month (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D3_2_drift_monitors.ipynb)
- **Session 3: Online evaluation and review queues**
  - Redact traces before storage and apply a retention rule
  - Grade a sample with a calibrated grader and correct the rate
  - Route failures and uncertain cases to a review queue
  - [Lab 3.3: Online evaluation and a review queue (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D3_3_online_eval.ipynb)
- **Session 4: Retraining and refresh policies**
  - Write a trigger from drift or a schedule that waits for labels
  - Estimate the cost of a retraining run
  - Require human approval and log the decision
  - [Lab 3.4: A retraining trigger with a cost and an approval (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D3_4_retraining_policy.ipynb)

### Day 4: Operate agents

Slides: https://sdaiaacademy.github.io/ae-305/slides/day4.md

- **Session 1: An agent is a bundle**
  - Separate the session log, the harness and the sandbox
  - Version an agent as one bundle with a content hash
  - Run the agent only from a released bundle
  - [Lab 4.1: Mubadir as one versioned bundle (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D4_1_agent_bundle.ipynb)
- **Session 2: Durable execution and safe retries**
  - Resume a crashed agent run from its last checkpoint
  - Explain why a retry after a timeout can repeat a write
  - Make a write tool idempotent with a key
  - [Lab 4.2: Crash, resume, and no duplicate tickets (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D4_2_durable_retries.ipynb)
- **Session 3: Replay to reproduce incidents**
  - Replay a recorded session deterministically
  - Find the cause of an incident in the replayed trace
  - Add the incident to the regression suite
  - [Lab 4.3: Replay incident INC-0412 (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D4_3_replay_incident.ipynb)
- **Session 4: Budgets, gateways and kill switches**
  - Set step and spend limits at a gateway
  - Stop a runaway agent with a kill switch
  - Keep the stopped sessions and hand them to a person
  - [Lab 4.4: Limits and a kill switch at the gateway (25 min)](https://sdaiaacademy.github.io/ae-305/labs/D4_4_budgets_killswitch.ipynb)

### Capstone: Capstone: a release week and its defence

Slides: https://sdaiaacademy.github.io/ae-305/slides/capstone.md

## Capstone

A simulated release week in which a corrupt batch, a provider model update and an agent incident arrive; the participant gates, ships or rolls back each and submits a public repository with pipeline logs, a release log and a runbook, then defends it for eight minutes while the assessor injects one further fault

**What you submit:** A public GitHub repository with the pipeline logs, the release log, the runbook and timestamped trace files of the release week, built from the starter in labs/capstone/. Then an eight-minute live defence in which the assessor injects one further fault and the participant diagnoses it from traces and logs.

**Rubric:**

- Pipelines and gates: 25%
- Delivery and rollback: 20%
- Observability: 20%
- Agent operations: 20%
- Runbook and reproducibility: 15%

## Outcomes

- **LO1** Prepare a release manifest that versions data, code, configuration, model, prompt, retrieval index and tool schemas as one unit, given two runs of the three systems that behave differently (Applied) Evidence: a manifest and the unrecorded change found between the runs
- **LO2** Build a retraining pipeline, started by a drift or schedule trigger, with data validation and a promotion gate that compares challenger and champion overall and by region, given monthly feeder batches, one of them corrupt and one drifted (Performance) Evidence: a triggered run that promotes on the drifted batch and stops on the corrupt one, with registry lineage
- **LO3** Deliver language model changes through an evaluation gate and a canary stage with an automatic rollback trigger, given a prompt edit, a model swap and an index refresh, one of which regresses (Performance) Evidence: logs showing two releases shipped and one rolled back on a stated metric
- **LO4** Configure request tracing, drift monitors and online evaluation with a review queue, and tune alert thresholds, given a replayed month of traffic with two planted shifts (Applied) Evidence: a dashboard, alert rules and a note on shifts found and false alarms removed
- **LO5** Diagnose an agent incident by replaying recorded traces and fix it with idempotent tools, durable state or a budget, given a recorded failure of the ticket agent (Performance) Evidence: the failure reproduced, a fix and a new regression case
- **LO6** Measure cost per successful outcome and resource use for each system and set budget alerts, given a month of token, compute and outcome logs (Applied) Evidence: a cost table by system and team, with alert rules

## Tools

- **Experiment tracking and model registry:** MLflow, Kubeflow Model Registry
- **Data versioning:** DVC, lakeFS
- **Pipeline orchestration:** Prefect, Apache Airflow, Kubeflow Pipelines
- **Validation and drift detection:** pandera, Evidently, SciPy
- **Continuous integration and progressive delivery:** Argo Rollouts, Argo CD, GitLab CI or GitHub Actions
- **Tracing, metrics and dashboards:** OpenTelemetry with Langfuse, Arize Phoenix, Prometheus and Grafana
- **Model and agent gateway:** LiteLLM, Agent Router, agentgateway
- **Durable execution:** Temporal, a state-graph framework with a checkpointer
- **Single-node local cluster:** kind, k3d

## Prerequisites

- AE-205 Deploying AI Services: Containers, Serving and Monitoring
- AE-203 Building Applications on Language Models
- Builds a container image and a continuous-integration workflow
- Reads an evaluation report with pass rates and intervals
- Has built a tool-calling agent, as in AE-302 or equivalent
- Setup: a laptop CPU with uv, or Google Colab; a free OpenRouter key is optional, since every lab also runs on a scripted stand-in model. Nothing downloads a model. Run 00_setup_check before Day 1; see labs/README.md.

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

---

SDAIA Academy · AI Engineering Track · Operating Machine Learning and Language Model Systems

Course version 2027.2.0 · engine 1.0.0 · built 2026-11-24 · commit fd96777
