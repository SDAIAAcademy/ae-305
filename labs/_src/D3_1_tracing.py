# %% [markdown]
# # Lab 3.1 · Spans for Nabd and the slowest step
#
# Day 3 · Session 1 (Tracing requests end to end) · 25 min.
#
# Saqer's crews say Nabd has become slow, and everyone blames the model. You instrument Nabd with OpenTelemetry:
# one trace per request, with a span for retrieval, each model call and each tool call, named and described with
# the GenAI semantic conventions. You run ten crew questions, read where the time goes, fix the slowest step and
# measure again.
#
# **Reference state.** `nabd.py` (the assistant, unchanged), the production release
# `data/nabd/releases/champion.json`, and the configuration production runs with: `cache_index=False`, set during
# an incident in September and never set back. Spans go to an in-memory exporter, so nothing leaves the laptop.
#
# **Tasks**
# - [ ] 1 · A tracer with an in-memory exporter (4')
# - [ ] 2 · Spans for retrieval, model and tool (9')
# - [ ] 3 · Ten requests and the slowest step (7')
# - [ ] 4 · Fix it and measure again (5')
# - [ ] ✱ Stretch · Redact phone numbers and account numbers in span attributes

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

# %%
import json
import statistics

import pandas as pd
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Status, StatusCode

import nabd

OUT = K.lab_dir("D3_1")
RELEASE = nabd.load_release("champion")
QUESTIONS = [json.loads(l)["question"] for l in (K.DATA / "eval" / "nabd_eval.jsonl").read_text(encoding="utf-8").splitlines()]
QUESTIONS = QUESTIONS[:8] + QUESTIONS[22:24]  # eight manual questions and the two tool questions
print(len(QUESTIONS), "crew questions, release", RELEASE["release"])

# %% [markdown]
# ## 1 · A tracer with an in-memory exporter (4')
#
# A **tracer provider** creates spans and hands each finished span to its span processors; an **exporter** sends
# them somewhere. In production the exporter sends them over OTLP to a collector (Jaeger, Tempo, Langfuse, Phoenix
# and others accept it). Here an in-memory exporter keeps them in a list.
#
# ✏️ **Exercise** · Create `exporter` (an `InMemorySpanExporter`), a `TracerProvider` with a `SimpleSpanProcessor`
# on that exporter, and `tracer = provider.get_tracer("wahaj.nabd")`.

# %%
try:
    # BEGIN SOLUTION
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("wahaj.nabd")
    # END SOLUTION
except NotImplementedError:  # safety net
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("wahaj.nabd")
with tracer.start_as_current_span("hello"):
    pass
print([s.name for s in exporter.get_finished_spans()])
exporter.clear()

# %% [markdown]
# ## 2 · Spans for retrieval, model and tool (9')
#
# The OpenTelemetry GenAI semantic conventions (status: Development, so names can still change) name a span
# `"{operation} {target}"` and describe it with `gen_ai.*` attributes. The operations Nabd uses:
#
# | Step | Span name | Attributes |
# |---|---|---|
# | the whole request | `invoke_agent Nabd` | `gen_ai.operation.name`, `gen_ai.agent.name`, and `wahaj.release` |
# | retrieval | `retrieval manuals` | `gen_ai.operation.name`, `wahaj.index`, `wahaj.hits` |
# | each model call | `chat {model}` | `gen_ai.operation.name`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens` |
# | each tool call | `execute_tool {name}` | `gen_ai.operation.name`, `gen_ai.tool.name`, and an error status when the tool returns an error |
#
# The question and the answer are **not** attributes: they can hold personal data (the stretch adds the question
# redacted).
#
# ✏️ **Exercise** · Complete `TracedNabd`, a subclass of `nabd.Nabd` whose four methods open the spans above
# around the parent's method (`super().retrieve(...)` and so on).

# %%
class TracedNabd(nabd.Nabd):
    def answer(self, question: str) -> dict:
        # BEGIN SOLUTION
        with tracer.start_as_current_span("invoke_agent Nabd") as span:
            span.set_attribute("gen_ai.operation.name", "invoke_agent")
            span.set_attribute("gen_ai.agent.name", "Nabd")
            span.set_attribute("wahaj.release", self.release["release"])
            return super().answer(question)
        # END SOLUTION

    def retrieve(self, question: str) -> list[dict]:
        # BEGIN SOLUTION
        with tracer.start_as_current_span("retrieval manuals") as span:
            span.set_attribute("gen_ai.operation.name", "retrieval")
            span.set_attribute("wahaj.index", self.release["index"])
            hits = super().retrieve(question)
            span.set_attribute("wahaj.hits", [h["ref"] for h in hits])
            return hits
        # END SOLUTION

    def call_model(self, messages: list[dict]) -> dict:
        # BEGIN SOLUTION
        with tracer.start_as_current_span(f"chat {self.release['model']}") as span:
            span.set_attribute("gen_ai.operation.name", "chat")
            span.set_attribute("gen_ai.request.model", self.release["model"])
            reply = super().call_model(messages)
            span.set_attribute("gen_ai.response.model", reply["model"])
            span.set_attribute("gen_ai.usage.input_tokens", reply["usage"]["input_tokens"])
            span.set_attribute("gen_ai.usage.output_tokens", reply["usage"]["output_tokens"])
            return reply
        # END SOLUTION

    def run_tool(self, name: str, args: dict) -> dict:
        # BEGIN SOLUTION
        with tracer.start_as_current_span(f"execute_tool {name}") as span:
            span.set_attribute("gen_ai.operation.name", "execute_tool")
            span.set_attribute("gen_ai.tool.name", name)
            result = super().run_tool(name, args)
            if "error" in result:
                span.set_status(Status(StatusCode.ERROR, result["error"]))
            return result
        # END SOLUTION


class ReferenceTracedNabd(nabd.Nabd):  # safety net: the reference spans
    def _span(self, name, op, **attrs):
        span = tracer.start_as_current_span(name, attributes={"gen_ai.operation.name": op, **attrs})
        return span

    def answer(self, question):
        with self._span("invoke_agent Nabd", "invoke_agent", **{"gen_ai.agent.name": "Nabd", "wahaj.release": self.release["release"]}):
            return super().answer(question)

    def retrieve(self, question):
        with self._span("retrieval manuals", "retrieval", **{"wahaj.index": self.release["index"]}):
            return super().retrieve(question)

    def call_model(self, messages):
        with self._span(f"chat {self.release['model']}", "chat", **{"gen_ai.request.model": self.release["model"]}) as s:
            reply = super().call_model(messages)
            s.set_attribute("gen_ai.response.model", reply["model"])
            s.set_attribute("gen_ai.usage.input_tokens", reply["usage"]["input_tokens"])
            s.set_attribute("gen_ai.usage.output_tokens", reply["usage"]["output_tokens"])
            return reply

    def run_tool(self, name, args):
        with self._span(f"execute_tool {name}", "execute_tool", **{"gen_ai.tool.name": name}):
            return super().run_tool(name, args)


def make_bot(cache_index: bool):
    bot = TracedNabd(RELEASE, cache_index=cache_index)
    try:
        bot.answer("probe")
    except NotImplementedError:
        bot = ReferenceTracedNabd(RELEASE, cache_index=cache_index)
    exporter.clear()
    return bot


bot = make_bot(cache_index=False)  # the production configuration
bot.answer(QUESTIONS[-2])
for s in exporter.get_finished_spans():
    print(f"{s.name:28} parent={s.parent.span_id % 10000 if s.parent else '-':>5}  {(s.end_time - s.start_time) / 1e6:7.1f} ms  "
          + ", ".join(f"{k}={v}" for k, v in s.attributes.items() if k != "gen_ai.operation.name"))
names = {s.name for s in exporter.get_finished_spans()}
assert {"invoke_agent Nabd", "retrieval manuals", "execute_tool get_feeder_status"} <= names, names
exporter.clear()

# %% [markdown]
# ## 3 · Ten requests and the slowest step (7')
#
# ✏️ **Exercise** · Answer the ten questions with the production configuration, then write `breakdown(spans)`
# returning a table with one row per operation (`gen_ai.operation.name`): the number of spans, the total and the
# median milliseconds, and the share of the total request time.

# %%
def run_ten(bot) -> list:
    exporter.clear()
    for q in QUESTIONS:
        bot.answer(q)
    return list(exporter.get_finished_spans())


def breakdown(spans) -> pd.DataFrame:
    # BEGIN SOLUTION
    rows = [{"operation": s.attributes.get("gen_ai.operation.name"), "ms": (s.end_time - s.start_time) / 1e6} for s in spans]
    df = pd.DataFrame(rows)
    out = df.groupby("operation").ms.agg(spans="count", total_ms="sum", median_ms="median")
    request_ms = out.loc["invoke_agent", "total_ms"]
    out["share_of_request"] = out.total_ms / request_ms
    return out.round(3).sort_values("total_ms", ascending=False)
    # END SOLUTION


def reference_breakdown(spans):
    df = pd.DataFrame([{"operation": s.attributes.get("gen_ai.operation.name"), "ms": (s.end_time - s.start_time) / 1e6} for s in spans])
    out = df.groupby("operation").ms.agg(spans="count", total_ms="sum", median_ms="median")
    out["share_of_request"] = out.total_ms / out.loc["invoke_agent", "total_ms"]
    return out.round(3).sort_values("total_ms", ascending=False)


spans_before = run_ten(bot)
try:
    before = breakdown(spans_before)
except NotImplementedError:  # safety net
    before = reference_breakdown(spans_before)
print(before.to_string())
slowest = before.drop(index="invoke_agent").share_of_request.idxmax()
print("slowest step:", slowest)
assert slowest == "retrieval"

# %% [markdown]
# 🔍 Retrieval takes more time than the model. Open `nabd.Nabd.retrieve`: what does `cache_index=False` do on every
# request? (The index is fetched from object storage and rebuilt each time.)

# %% [markdown]
# ## 4 · Fix it and measure again (5')
#
# ✏️ **Exercise** · Build the bot with `cache_index=True`, run the ten questions again and compare the median
# request time and the retrieval share before and after. Write both into `artifacts/D3_1/latency.json`.

# %%
try:
    # BEGIN SOLUTION
    fixed = make_bot(cache_index=True)
    spans_after = run_ten(fixed)
    after = breakdown(spans_after)
    # END SOLUTION
except NotImplementedError:  # safety net
    fixed = make_bot(cache_index=True)
    spans_after = run_ten(fixed)
    after = reference_breakdown(spans_after)
print(after.to_string())
result = {"median_request_ms": {"before": float(before.loc["invoke_agent", "median_ms"]), "after": float(after.loc["invoke_agent", "median_ms"])},
          "retrieval_share": {"before": float(before.loc["retrieval", "share_of_request"]), "after": float(after.loc["retrieval", "share_of_request"])},
          "fix": "cache the index once per process (cache_index=True); reload it when the release's index changes"}
K.write_json(OUT / "latency.json", result)
print(json.dumps(result, indent=1))
assert result["median_request_ms"]["after"] < result["median_request_ms"]["before"] / 2
K.check(True, f"median request {result['median_request_ms']['before']:.0f} ms -> {result['median_request_ms']['after']:.0f} ms")

# %% [markdown]
# 🔍 With the stand-in model a call takes about 80 ms; a free hosted model takes seconds. Would retrieval still be
# the slowest step with a hosted model? Would the fix still matter? (Yes: a quarter of a second on every request,
# for nothing.)

# %% [markdown]
# ## ✱ Stretch · Redact before recording
#
# Reviewers want the crew's question on the root span. Questions sometimes hold a customer's phone number, account
# number or national ID. Write `redact(text)` replacing Saudi mobile numbers (`05` and eight digits), account
# numbers (`ACC-` and eight digits) and ten-digit national IDs (starting with 1 or 2) with `[phone]`, `[account]`
# and `[national-id]`, and record `wahaj.question` redacted.

# %%
import re

try:
    # BEGIN SOLUTION
    PATTERNS = [(re.compile(r"\b05\d{8}\b"), "[phone]"), (re.compile(r"\bACC-\d{8}\b"), "[account]"),
                (re.compile(r"\b[12]\d{9}\b"), "[national-id]")]

    def redact(text: str) -> str:
        for rx, label in PATTERNS:
            text = rx.sub(label, text)
        return text

    q = "Outage on F-0213; customer called from 0551234567 about account ACC-40005754, ID 1098765432."
    exporter.clear()
    with tracer.start_as_current_span("invoke_agent Nabd") as span:
        span.set_attribute("wahaj.question", redact(q))
    print(exporter.get_finished_spans()[0].attributes["wahaj.question"])
    # END SOLUTION
except NotImplementedError:
    print("stretch not done")

# %% [markdown]
# ## Checkpoint
#
# 1. Why put the question in a span attribute only after redaction, and never the full prompt by default?
#    <details><summary>Answer</summary>Traces are copied to a collector and kept for weeks by people outside the
#    team; personal data in them is collected and stored without a purpose (PDPL).</details>
# 2. The median request fell, but the slowest requests are still the ones with tools. Which span tells you why?
#    <details><summary>Answer</summary>The second `chat` span: a tool call adds a tool span and a second model
#    call.</details>
# 3. Why use the GenAI semantic conventions rather than your own attribute names?
#    <details><summary>Answer</summary>Tracing back ends and dashboards understand them, so spans from Nabd,
#    Mubadir and a vendor library line up. They are still in Development: pin the version you follow.</details>
#
# ## Carry forward
#
# `TracedNabd` and `artifacts/D3_1/latency.json` go into the capstone's runbook as the latency evidence. Day 4
# reads Mubadir's recorded trace in the same shape.
