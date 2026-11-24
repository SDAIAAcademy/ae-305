---
course: "Operating Machine Learning and Language Model Systems"
code: "AE-305"
version: "2027.2.0"
deck: "capstone"
day: 5
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-305/slides/capstone.html"
---

# Operating Machine Learning and Language Model Systems

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
