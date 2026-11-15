<!-- academy:title -->
# Operating Machine Learning and Language Model Systems

تشغيل أنظمة تعلم الآلة والنماذج اللغوية

AI Engineering Track · SDAIA Academy · AE-305 · Level 300

REPLACE: one line under the title: what participants can do after the course

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
| Capstone | Capstone project presentations |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**REPLACE: the name of the fictional organisation every lab works on.** REPLACE: two sentences on the case study and its synthetic data

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | Write a release manifest for the three systems and find the unrecorded change between two runs | [`D1_1_write_release_manifest.ipynb`](labs/D1_1_write_release_manifest.ipynb) |
| 1.2 | Day 1 · Session 2 | Reproduce a colleague's model from the registry and trace it to its data snapshot and commit | [`D1_2_reproduce_colleague_s.ipynb`](labs/D1_2_reproduce_colleague_s.ipynb) |
| 1.3 | Day 1 · Session 3 | Add a validation step that stops training on a corrupt monthly batch | [`D1_3_add_validation_step.ipynb`](labs/D1_3_add_validation_step.ipynb) |
| 1.4 | Day 1 · Session 4 | Compare a challenger with the champion overall and by region and promote only if both pass | [`D1_4_compare_challenger_champion.ipynb`](labs/D1_4_compare_challenger_champion.ipynb) |
| 2.1 | Day 2 · Session 1 | Wire merge to staging to production with an approval step | [`D2_1_wire_merge_staging.ipynb`](labs/D2_1_wire_merge_staging.ipynb) |
| 2.2 | Day 2 · Session 2 | Run a prompt edit, a model swap and an index refresh through a provided evaluation gate | [`D2_2_run_prompt_edit.ipynb`](labs/D2_2_run_prompt_edit.ipynb) |
| 2.3 | Day 2 · Session 3 | Canary a model swap on replayed traffic and let a quality and latency trigger roll it back | [`D2_3_canary_model_swap.ipynb`](labs/D2_3_canary_model_swap.ipynb) |
| 2.4 | Day 2 · Session 4 | Compute cost per successful outcome and utilisation per system and set a budget alert | [`D2_4_compute_cost_per.ipynb`](labs/D2_4_compute_cost_per.ipynb) |
| 3.1 | Day 3 · Session 1 | Add spans for model, retrieval and tool calls to the assistant and find the slowest step | [`D3_1_add_spans_model.ipynb`](labs/D3_1_add_spans_model.ipynb) |
| 3.2 | Day 3 · Session 2 | Detect two planted shifts in a replayed month and tune thresholds to remove false alarms | [`D3_2_detect_two_planted.ipynb`](labs/D3_2_detect_two_planted.ipynb) |
| 3.3 | Day 3 · Session 3 | Score sampled live traces with a provided calibrated grader and route failures to review | [`D3_3_score_sampled_live.ipynb`](labs/D3_3_score_sampled_live.ipynb) |
| 3.4 | Day 3 · Session 4 | Write a retraining trigger with a cost estimate and human approval and test it on a drifted batch | [`D3_4_write_retraining_trigger.ipynb`](labs/D3_4_write_retraining_trigger.ipynb) |
| 4.1 | Day 4 · Session 1 | Package the ticket agent's prompt, tools, harness settings and sandbox policy as one versioned bundle | [`D4_1_package_ticket_agent.ipynb`](labs/D4_1_package_ticket_agent.ipynb) |
| 4.2 | Day 4 · Session 2 | Crash the agent mid-task, resume from a checkpoint and fix a tool that duplicates tickets on retry | [`D4_2_crash_agent_mid.ipynb`](labs/D4_2_crash_agent_mid.ipynb) |
| 4.3 | Day 4 · Session 3 | Reproduce a recorded failure from stored tool responses and add it as a regression case | [`D4_3_reproduce_recorded_failure.ipynb`](labs/D4_3_reproduce_recorded_failure.ipynb) |
| 4.4 | Day 4 · Session 4 | Set step and spend limits at the gateway and stop a runaway agent without losing its sessions | [`D4_4_set_step_spend.ipynb`](labs/D4_4_set_step_spend.ipynb) |
<!-- /academy:labs -->

## Capstone

A simulated release week in which a corrupt batch, a provider model update and an agent incident arrive; the participant gates, ships or rolls back each and submits a public repository with pipeline logs, a release log and a runbook, then defends it for eight minutes while the assessor injects one further fault

**Submission:** REPLACE: what participants submit and how: a public repository link, or a shared folder for a course without code

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

- REPLACE: every source the course cites, with its address, in course.json under "sources"; this list is written from there
<!-- /academy:sources -->

### National references

- Personal Data Protection Law and its implementing regulations: REPLACE: the address of the official text
- NDMO Data Classification Policy: REPLACE: the address of the official text
- NDMO Data Management and Personal Data Protection Standards: REPLACE: the address of the official text
- National AI Risk Management Framework: REPLACE: the address of the official text
