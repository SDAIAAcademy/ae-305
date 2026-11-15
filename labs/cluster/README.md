# The optional cluster path

Labs 2.1 and 2.3 run in a notebook on any laptop or in Colab: the delivery workflow is checked and simulated, and
the canary is replayed through `K.run_rollout`, which follows the step semantics of Argo Rollouts. The catalog
entry also offers the same labs on a single-node local cluster for laptops that can run one. These files are that
path. They were not run when the course was built (no cluster tool was installed); try them before a cohort.

| File | What it is |
|---|---|
| `kind-config.yaml` | a one-node kind cluster named `wahaj` (k3d works the same way) |
| `rollout.yaml` | Nabd as an Argo Rollouts `Rollout` with the canary steps of Lab 2.3 |
| `analysis-template.yaml` | the latency and quality triggers of Lab 2.3 as an `AnalysisTemplate` on Prometheus |

Steps, on a laptop with Docker:

1. `kind create cluster --config kind-config.yaml`
2. Install Argo Rollouts from its official installation page, into the namespace `argo-rollouts`.
3. `kubectl apply -f analysis-template.yaml -f rollout.yaml`
4. Change the image, then watch the steps with the Argo Rollouts kubectl plugin (`kubectl argo rollouts get rollout nabd --watch`).

Without a traffic router, `setWeight` is approximated by the number of canary pods; the official canary page
explains the difference. The analysis needs a Prometheus that scrapes Nabd's metrics; the trainer can run the
notebook path instead when no cluster is available. A provided cloud workspace is the fallback for laptops that
cannot run a cluster.
