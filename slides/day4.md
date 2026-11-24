---
course: "Operating Machine Learning and Language Model Systems"
code: "AE-305"
version: "2027.2.0"
deck: "day4"
day: 4
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-305/slides/day4.html"
---

# Operating Machine Learning and Language Model Systems

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
