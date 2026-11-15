# %% [markdown]
# # Lab 2.1 · Merge to staging to production
#
# Day 2 · Session 1 (Continuous delivery for models) · 25 min.
#
# Until now every push to Wahaj's main branch went straight to production, built again each time with the tag
# `latest`. You turn that workflow into three jobs, build, staging and production, that promote **one** image
# digest, add a smoke check in staging and an approval before production, check the workflow against Wahaj's
# delivery rules, and simulate a release.
#
# **Reference state.** `data/delivery/release_start.yml` (the current workflow), the checker `K.check_workflow`
# and the simulator `K.simulate_release`. The workflow is GitHub Actions syntax; GitLab CI has the same parts.
#
# **AI policy.** An assistant may explain a log or a rule; it does not write the workflow for you.
#
# **Tasks**
# - [ ] 1 · Read the starting workflow (4')
# - [ ] 2 · Staging and production jobs that promote one digest (8')
# - [ ] 3 · The approval step and its reviewers (6')
# - [ ] 4 · Check it and simulate a release (7')
# - [ ] ✱ Stretch · A rollback job that redeploys the previous digest

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ae-305.git"
    if not Path("/content/ae-305").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/ae-305"], check=True)
    os.chdir("/content/ae-305/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("_tools").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())

import opskit as K
print("quick mode:", K.QUICK)

# %% [markdown]
# ## 1 · Read the starting workflow (4')

# %%
OUT = K.lab_dir("D2_1")
start = (K.DATA / "delivery" / "release_start.yml").read_text(encoding="utf-8")
print(start)
for ok, rule in K.check_workflow(start):
    print(("PASS " if ok else "FAIL ") + rule)

# %% [markdown]
# 🔍 Which failed rule would have let an untested model reach production? Which would make a rollback impossible
# to describe ("go back to `latest`" is not a version)?

# %% [markdown]
# ## 2 · Staging and production jobs that promote one digest (8')
#
# A container image is named by its **digest** (`sha256:…`), which is the hash of its content: the same idea as
# Lab 1.1's manifest. Build once, push once, and pass the digest to the later jobs as a job output, so that
# staging and production run exactly what was tested.
#
# ✏️ **Exercise** · Write `WORKFLOW`, a GitHub Actions workflow with three jobs:
# - `build`: tests, builds and pushes the image, and publishes `digest` as a job output
#   (`outputs: {digest: ${{ steps.push.outputs.digest }}}`)
# - `deploy-staging`: `needs: build`, `environment: staging`, deploys the digest and runs a smoke check
# - `deploy-production`: `needs: deploy-staging`, `environment: production`, deploys the same digest
#
# Neither deploy job builds again, and nothing uses the tag `latest`.

# %%
try:
    # BEGIN SOLUTION
    WORKFLOW = """name: release
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.push.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      - run: make test
      - run: docker build -t registry.wahaj.example/nabd:${{ github.sha }} .
      - id: push
        run: |
          docker push registry.wahaj.example/nabd:${{ github.sha }}
          echo "digest=$(docker inspect --format='{{index .RepoDigests 0}}' registry.wahaj.example/nabd:${{ github.sha }})" >> "$GITHUB_OUTPUT"
  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh staging ${{ needs.build.outputs.digest }}
      - run: ./smoke_check.sh staging
  deploy-production:
    needs: [build, deploy-staging]
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh production ${{ needs.build.outputs.digest }}
"""
    # END SOLUTION
except NotImplementedError:  # safety net: the reference workflow
    WORKFLOW = K.reference("D2_1_workflow")["yaml"]
K.save_reference("D2_1_workflow", {"yaml": WORKFLOW})
(OUT / "release.yml").write_text(WORKFLOW, encoding="utf-8")

# %% [markdown]
# ## 3 · The approval step and its reviewers (6')
#
# On GitHub the approval is not in the file: it is a protection rule of the `production` environment in the
# repository settings. Required reviewers (up to six people or teams) must approve before the job starts, and
# self-review can be blocked so that the person who merged cannot approve their own release. On the free plan
# these rules work on public repositories, which is what the capstone uses.
#
# ✏️ **Exercise** · Write Wahaj's rules in `ENVIRONMENTS`, then `can_approve(env, merged_by, approver)` returning
# `(ok, why)`: staging needs no approval; production needs an approver from its reviewer list who is not the
# person who merged.

# %%
try:
    # BEGIN SOLUTION
    ENVIRONMENTS = {
        "staging": {"required_reviewers": [], "prevent_self_review": False},
        "production": {"required_reviewers": ["Mutab Al-Shalhoub", "Dhafer Al-Hazzani"], "prevent_self_review": True},
    }

    def can_approve(env: str, merged_by: str, approver: str | None) -> tuple[bool, str]:
        rules = ENVIRONMENTS[env]
        if not rules["required_reviewers"]:
            return True, "no approval needed"
        if approver is None:
            return False, "waiting for a reviewer"
        if approver not in rules["required_reviewers"]:
            return False, f"{approver} is not a reviewer of {env}"
        if rules["prevent_self_review"] and approver == merged_by:
            return False, "the person who merged cannot approve their own release"
        return True, f"approved by {approver}"
    # END SOLUTION
except NotImplementedError:  # safety net
    ENVIRONMENTS = {"staging": {"required_reviewers": [], "prevent_self_review": False},
                    "production": {"required_reviewers": ["Mutab Al-Shalhoub", "Dhafer Al-Hazzani"], "prevent_self_review": True}}

    def can_approve(env, merged_by, approver):
        r = ENVIRONMENTS[env]
        if not r["required_reviewers"]:
            return True, "no approval needed"
        if approver is None:
            return False, "waiting for a reviewer"
        if approver not in r["required_reviewers"] or (r["prevent_self_review"] and approver == merged_by):
            return False, "not an allowed reviewer"
        return True, f"approved by {approver}"

for case in [("production", "Dhafer Al-Hazzani", None), ("production", "Dhafer Al-Hazzani", "Dhafer Al-Hazzani"),
             ("production", "Dhafer Al-Hazzani", "Saqer Al-Dossary"), ("production", "Dhafer Al-Hazzani", "Mutab Al-Shalhoub")]:
    print(case[2], "->", can_approve(*case))
assert can_approve("production", "Dhafer Al-Hazzani", "Dhafer Al-Hazzani")[0] is False
assert can_approve("production", "Dhafer Al-Hazzani", "Mutab Al-Shalhoub")[0] is True

# %% [markdown]
# ## 4 · Check it and simulate a release (7')
#
# The simulator walks the jobs in dependency order as a runner would, writes what each environment runs to
# `artifacts/D2_1/sim/environments/`, and stops at production until a reviewer approves.

# %%
results = K.check_workflow(WORKFLOW)
for ok, rule in results:
    print(("PASS " if ok else "FAIL ") + rule)
assert all(ok for ok, _ in results), "the workflow breaks a delivery rule"

merged_by = "Dhafer Al-Hazzani"
first = K.simulate_release(WORKFLOW, approvals={"production": None}, log_dir=OUT / "sim")
print("\nbefore approval:"); [print("  ", e) for e in first]
ok, why = can_approve("production", merged_by, "Mutab Al-Shalhoub")
second = K.simulate_release(WORKFLOW, approvals={"production": "Mutab Al-Shalhoub" if ok else None}, log_dir=OUT / "sim")
print("after approval:"); [print("  ", e) for e in second]
K.write_json(OUT / "deployment_log.json", {"merged_by": merged_by, "approval": why, "events": second})
stg = K.read_json(OUT / "sim" / "environments" / "staging.json")
prd = K.read_json(OUT / "sim" / "environments" / "production.json")
assert first[-1]["event"] == "waiting for approval"
assert stg["digest"] == prd["digest"]
K.check(True, f"staging and production run the same digest {prd['digest']}")

# %% [markdown]
# ## ✱ Stretch · A rollback job
#
# Add a workflow `rollback.yml` started by hand (`workflow_dispatch`) with an input `digest`, which redeploys that
# digest to production through the same environment, so the same reviewers approve it. It must not build.

# %%
try:
    # BEGIN SOLUTION
    ROLLBACK = """name: rollback
on:
  workflow_dispatch:
    inputs:
      digest:
        description: the image digest to restore, from the deployment log
        required: true
jobs:
  rollback-production:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh production ${{ inputs.digest }}
      - run: ./smoke_check.sh production
"""
    (OUT / "rollback.yml").write_text(ROLLBACK, encoding="utf-8")
    print("rollback builds nothing:", "docker build" not in ROLLBACK)
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. Why must production deploy the digest that staging tested, and not rebuild from the same commit?
#    <details><summary>Answer</summary>A rebuild can pull newer base images or packages, so it can differ from
#    what was tested. The digest is the content that passed.</details>
# 2. Where does the approval rule live on GitHub, and why is that safer than a step in the file?
#    <details><summary>Answer</summary>In the environment's protection rules in the repository settings: a pull
#    request cannot remove it by editing the workflow.</details>
# 3. What does the deployment log need so that a rollback is one command?
#    <details><summary>Answer</summary>The digest that ran before, per environment, with who approved it.</details>
#
# ## Carry forward
#
# `artifacts/D2_1/release.yml` and `rollback.yml` are the shape of the capstone repository's delivery workflows.
# The optional cluster path in `labs/cluster/` deploys the same digest with Argo Rollouts on kind.
