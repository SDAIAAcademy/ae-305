"""Nabd (نبض), Wahaj's field-crew assistant: retrieval over the maintenance manuals, two tools, one model.

    import nabd
    bot = nabd.Nabd(nabd.load_release("champion"))
    bot.answer("How do we sample transformer oil?")

A release (data/nabd/releases/*.json) names the prompt file, the model, the index version, the tool schemas
and the retrieval settings: everything that changes Nabd's behaviour. `Nabd.answer` runs four steps that
Lab 3.1 wraps in spans: retrieve, call_model, run_tool, call_model again. The scripted stand-in model at the
bottom answers when no working key for a free hosted model is set.
"""
from __future__ import annotations

import csv
import json
import math
import re
import time
from collections import Counter
from pathlib import Path

import opskit as K
from graders import words

DATA = K.DATA


# ------------------------------------------------------------------ the manuals and a BM25 index
def load_sections(version: str) -> list[dict]:
    out = []
    for p in sorted((DATA / "manuals" / version).glob("MM-*.md")):
        doc, title, sec = p.stem, "", None
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("# "):
                title = line.split("·", 1)[-1].strip()
            elif line.startswith("## "):
                n, head = line[3:].split(". ", 1)
                sec = {"doc": doc, "section": int(n), "title": f"{title}: {head}", "text": ""}
                out.append(sec)
            elif sec is not None and line.strip():
                sec["text"] += line.strip() + " "
    for s in out:
        s["text"] = s["text"].strip()
        s["ref"] = f"[{s['doc']} §{s['section']}]"
    return out


class Index:
    """BM25 over the sections of one version of the manuals."""

    def __init__(self, version: str, k1: float = 1.4, b: float = 0.75):
        self.version = version
        self.sections = load_sections(version)
        self.docs = [words(s["title"] + " " + s["text"]) for s in self.sections]
        self.df = Counter(w for d in self.docs for w in set(d))
        self.avg = sum(map(len, self.docs)) / len(self.docs)
        self.k1, self.b, self.n = k1, b, len(self.docs)

    def search(self, query: str, k: int = 3) -> list[dict]:
        q = words(query)
        scores = []
        for i, d in enumerate(self.docs):
            tf = Counter(d)
            s = 0.0
            for w in q:
                if w in tf:
                    idf = math.log(1 + (self.n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                    s += idf * tf[w] * (self.k1 + 1) / (tf[w] + self.k1 * (1 - self.b + self.b * len(d) / self.avg))
            scores.append((s, i))
        top = sorted(scores, key=lambda x: (-x[0], x[1]))[:k]
        return [dict(self.sections[i], score=round(s, 3)) for s, i in top if s > 0]

    def fingerprint(self) -> str:
        return K.short(K.sha256_json([(s["ref"], s["text"]) for s in self.sections]))


def fetch_index(version: str) -> Index:
    """Load the index as production does: from object storage (simulated by a 0.25-second wait), then build it."""
    time.sleep(0.25)
    return Index(version)


# ------------------------------------------------------------------ the two tools
def get_feeder_status(feeder_id: str) -> dict:
    """Live status of one feeder from the control room."""
    time.sleep(0.03)
    status = json.loads((DATA / "ops" / "feeder_status.json").read_text(encoding="utf-8"))
    if feeder_id not in status:
        return {"error": f"unknown feeder {feeder_id}; feeder ids look like F-0213"}
    return {"feeder_id": feeder_id, **status[feeder_id]}


def check_parts_stock(part_code: str, depot: str) -> dict:
    """Stock of one part at one depot."""
    time.sleep(0.03)
    with (DATA / "ops" / "parts_stock.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["part_code"] == part_code and r["depot"] == depot:
                return {"part_code": part_code, "name": r["name"], "depot": depot, "on_hand": int(r["on_hand"])}
    return {"error": f"no stock record for {part_code} at {depot}"}


TOOLS = {"get_feeder_status": get_feeder_status, "check_parts_stock": check_parts_stock}


# ------------------------------------------------------------------ releases and the assistant
def load_release(name: str) -> dict:
    return K.read_json(DATA / "nabd" / "releases" / f"{name}.json")


class Nabd:
    """One running release of Nabd. cache_index=False reloads the index on every request (the slow path)."""

    def __init__(self, release: dict, cache_index: bool = True):
        self.release = release
        self.prompt = (DATA / "nabd" / release["prompt"]).read_text(encoding="utf-8")
        self.tools = json.loads((DATA / "nabd" / release["tools"]).read_text(encoding="utf-8"))
        self.cache_index = cache_index
        self._index = fetch_index(release["index"]) if cache_index else None

    # -- the four steps
    def retrieve(self, question: str) -> list[dict]:
        index = self._index if self.cache_index else fetch_index(self.release["index"])
        return index.search(question, self.release["retrieval"]["k"])

    def call_model(self, messages: list[dict]) -> dict:
        return K.chat(messages, self.release["model"], tools=self.tools, temperature=self.release.get("temperature", 0))

    def run_tool(self, name: str, args: dict) -> dict:
        fn = TOOLS.get(name)
        return fn(**args) if fn else {"error": f"no tool {name}"}

    # -- one request
    def answer(self, question: str) -> dict:
        hits = self.retrieve(question)
        context = "\n".join(f"{h['ref']} {h['title']}. {h['text']}" for h in hits)
        messages = [{"role": "system", "content": self.prompt},
                    {"role": "user", "content": f"Context from the manuals:\n{context}\n\nCrew question: {question}"}]
        reply = self.call_model(messages)
        usage = dict(reply["usage"])
        calls = []
        for c in reply.get("tool_calls", [])[:2]:
            result = self.run_tool(c["name"], c["args"])
            calls.append({"name": c["name"], "args": c["args"], "result": result})
        if calls:
            messages.append({"role": "assistant", "content": json.dumps([{"name": c["name"], "args": c["args"]} for c in calls])})
            messages.append({"role": "user", "content": "Tool results: " + json.dumps([c["result"] for c in calls], ensure_ascii=False)})
            reply = self.call_model(messages)
            usage = {k: usage[k] + reply["usage"][k] for k in usage}
        return {"question": question, "answer": reply["content"], "retrieved": [h["doc"] for h in hits],
                "context": context, "tool_calls": calls, "model": reply["model"], "usage": usage}


# ------------------------------------------------------------------ the scripted stand-in model
FEEDER = re.compile(r"\bF-\d{4}\b")
PART = re.compile(r"\bP-\d{3}\b")
OUT_OF_SCOPE = ("tariff", "bill", "phone number", "salary", "personal")
STEP = re.compile(r"(\d+)\.\s")


def _sections(user: str) -> list[tuple[str, str]]:
    out = []
    for line in user.split("\n"):
        m = re.match(r"(\[MM-\d{2} §\d+\])\s+(.*)", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def _scripted(messages: list[dict], tools: list, persona: str) -> dict:
    """Deterministic stand-in for a hosted model. It reads the system prompt's rules, the context and the
    question, and answers extractively. persona "swift" is a faster model that keeps at most four steps of a
    numbered procedure (Lab 2.2's regression)."""
    system = messages[0]["content"]
    user = messages[1]["content"]
    question = user.rsplit("Crew question:", 1)[-1].strip()
    tool_results = [m["content"] for m in messages[2:] if m["role"] == "user" and m["content"].startswith("Tool results:")]
    time.sleep(0.04 if persona == "swift" else 0.08)
    if tool_results:
        results = json.loads(tool_results[-1].split(":", 1)[1])
        parts = []
        for r in results:
            if "error" in r:
                parts.append(r["error"])
            elif "state" in r:
                parts.append(f"Feeder {r['feeder_id']} is {r['state']}, load {r['load_pct']}%, with {r['open_work_orders']} open work order(s).")
            else:
                parts.append(f"{r['depot']} depot has {r['on_hand']} of {r['part_code']} ({r['name']}).")
        return {"content": " ".join(parts), "tool_calls": []}
    if tools and FEEDER.search(question):
        return {"content": "", "tool_calls": [{"name": "get_feeder_status", "args": {"feeder_id": FEEDER.search(question).group(0)}}]}
    if tools and PART.search(question):
        depot = next((d for d in ("Al-Rimal", "Al-Hadba", "Al-Sahil", "Al-Wadi", "Al-Jabal", "Al-Nakheel") if d in question), "Al-Hadba")
        return {"content": "", "tool_calls": [{"name": "check_parts_stock", "args": {"part_code": PART.search(question).group(0), "depot": depot}}]}
    if any(w in question.lower() for w in OUT_OF_SCOPE) and "customer care" in system.lower():
        return {"content": "I cannot help with that from the manuals. Please contact customer care.", "tool_calls": []}
    secs = _sections(user)
    if not secs:
        return {"content": "The manuals I was given do not cover this question.", "tool_calls": []}
    qw = set(words(question))
    ref, text = max(secs, key=lambda s: (len(qw & set(words(s[1]))), -secs.index(s)))
    body = text.split(". ", 1)[1] if ". " in text else text  # drop the section title
    if persona == "swift" and STEP.search(body):
        cut = [m.start() for m in STEP.finditer(body)]
        if len(cut) > 4:
            body = body[:cut[4]].strip()
    always = "always cite" in system.lower()
    when_steps = "cite the manual when you quote a procedure step" in system.lower()
    cite = always or (when_steps and bool(STEP.search(body)))
    if cite:
        body = f"{body} {ref if always else ref.split(' §')[0] + ']'}"
    return {"content": body, "tool_calls": []}


K.register_standin("You are Nabd", _scripted)
