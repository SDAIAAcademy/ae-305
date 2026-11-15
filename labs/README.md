# Operating Machine Learning and Language Model Systems: labs

## Quick start

- Google Colab: open a notebook from the course page; its first cell clones this repository.
- Locally: clone the repository, then open the notebooks in `labs/` with Jupyter.

| Unit | Session | Notebook |
|---|---|---|
| Day 1 | Session 1 · What changes behaviour | [`D1_1_write_release_manifest.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D1_1_write_release_manifest.ipynb) |
| Day 1 | Session 2 · Registries and lineage | [`D1_2_reproduce_colleague_s.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D1_2_reproduce_colleague_s.ipynb) |
| Day 1 | Session 3 · Pipelines with validation | [`D1_3_add_validation_step.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D1_3_add_validation_step.ipynb) |
| Day 1 | Session 4 · Promotion gates | [`D1_4_compare_challenger_champion.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D1_4_compare_challenger_champion.ipynb) |
| Day 2 | Session 1 · Continuous delivery for models | [`D2_1_wire_merge_staging.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D2_1_wire_merge_staging.ipynb) |
| Day 2 | Session 2 · Language model releases | [`D2_2_run_prompt_edit.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D2_2_run_prompt_edit.ipynb) |
| Day 2 | Session 3 · Shadow and canary on evidence | [`D2_3_canary_model_swap.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D2_3_canary_model_swap.ipynb) |
| Day 2 | Session 4 · Cost and capacity signals | [`D2_4_compute_cost_per.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D2_4_compute_cost_per.ipynb) |
| Day 3 | Session 1 · Tracing requests end to end | [`D3_1_add_spans_model.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D3_1_add_spans_model.ipynb) |
| Day 3 | Session 2 · Drift, skew and delayed labels | [`D3_2_detect_two_planted.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D3_2_detect_two_planted.ipynb) |
| Day 3 | Session 3 · Online evaluation and review queues | [`D3_3_score_sampled_live.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D3_3_score_sampled_live.ipynb) |
| Day 3 | Session 4 · Retraining and refresh policies | [`D3_4_write_retraining_trigger.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D3_4_write_retraining_trigger.ipynb) |
| Day 4 | Session 1 · An agent is a bundle | [`D4_1_package_ticket_agent.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D4_1_package_ticket_agent.ipynb) |
| Day 4 | Session 2 · Durable execution and safe retries | [`D4_2_crash_agent_mid.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D4_2_crash_agent_mid.ipynb) |
| Day 4 | Session 3 · Replay to reproduce incidents | [`D4_3_reproduce_recorded_failure.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D4_3_reproduce_recorded_failure.ipynb) |
| Day 4 | Session 4 · Budgets, gateways and kill switches | [`D4_4_set_step_spend.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-305/blob/main/labs/D4_4_set_step_spend.ipynb) |

The notebooks are generated from the percent-format sources in `labs/_src/` by `labs/_tools/py2nb.py` (`uv run python _tools/py2nb.py` from `labs/`), which also writes the solutions to `labs/solutions/`. Edit the sources, not the notebooks.
