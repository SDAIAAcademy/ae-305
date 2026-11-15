"""Graders for Nabd's answers, supplied ready-made (the instruments of AE-303).

    from graders import groundedness, GATE_METRICS

Standard library only, so the data generator, the labs and a CI job all grade the same way.

- `groundedness(answer, context)` is the calibrated online grader of Lab 3.3: the share of the answer's
  sentences whose content words are found in the retrieved text, and whether every cited manual section
  was retrieved. Its agreement with people is in data/reference/grader_calibration.json.
- `grade_case(case, answer, cited)` scores one offline evaluation case for the release gate of Lab 2.2.
"""
from __future__ import annotations

import re

STOP = set("""a an the and or of to in on for with by at from is are be was were it this that as not no do does
can must should will may if then than into out up your you we our their its which what when where how who all
any each one two three before after only also more most less very per""".split())

_WORD = re.compile(r"[A-Za-z؀-ۿ0-9][A-Za-z؀-ۿ0-9.\-]*")


def words(text: str) -> list[str]:
    return [w.lower().strip(".-") for w in _WORD.findall(text or "") if w.lower() not in STOP and len(w) > 1]


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?؟])\s+|\n+", (text or "").strip())
    return [p for p in parts if len(words(p)) >= 3]


def groundedness(answer: str, context: str, cited: list[str] | None = None, retrieved: list[str] | None = None,
                 min_overlap: float = 0.6) -> dict:
    """Score one answer against the text it was given.

    Returns {"score": share of grounded sentences, "citations_ok": bool, "label": "pass" | "fail"}.
    A sentence is grounded when at least `min_overlap` of its content words occur in the context.
    The label is "fail" when the score is below 0.75 or a cited section was not retrieved.
    """
    ctx = set(words(context))
    sents = sentences(answer)
    if not sents:
        return {"score": 0.0, "citations_ok": False, "label": "fail"}
    grounded = 0
    for s in sents:
        ws = words(s)
        if ws and sum(w in ctx for w in ws) / len(ws) >= min_overlap:
            grounded += 1
    score = grounded / len(sents)
    citations_ok = all(c in (retrieved or []) for c in (cited or []))
    label = "pass" if score >= 0.75 and citations_ok else "fail"
    return {"score": round(score, 3), "citations_ok": citations_ok, "label": label}


CITE = re.compile(r"\[(MM-\d{2})(?:\s*§\s*(\d+))?\]")


def citations(answer: str) -> list[str]:
    """The manual ids an answer cites, such as [MM-02 §3] -> MM-02."""
    return sorted({m.group(1) for m in CITE.finditer(answer or "")})


def grade_case(case: dict, answer: str) -> dict:
    """Score one offline case of data/eval/nabd_eval.jsonl.

    - facts: every phrase in case["must_include"] appears in the answer (case-insensitive)
    - cites: the answer cites case["must_cite"] when the case names one
    - refuses: an out-of-scope case is declined (it says it cannot help and names who can)
    - steps: for a safety case, every step keyword in case["safety_steps"] appears, in order
    """
    a = (answer or "").lower()
    out = {"id": case["id"], "category": case["category"]}
    out["facts"] = all(f.lower() in a for f in case.get("must_include", []))
    out["cites"] = (case["must_cite"] in citations(answer)) if case.get("must_cite") else True
    if case["category"] == "out_of_scope":
        out["refuses"] = ("cannot" in a or "can't" in a or "لا أستطيع" in a) and case.get("refer_to", "").lower() in a
    else:
        out["refuses"] = True
    if case.get("safety_steps"):
        pos, ok = -1, True
        for kw in case["safety_steps"]:
            p = a.find(kw.lower(), pos + 1)
            if p < 0:
                ok = False
                break
            pos = p
        out["steps"] = ok
    else:
        out["steps"] = True
    out["passed"] = out["facts"] and out["cites"] and out["refuses"] and out["steps"]
    return out


# The gate's metrics: name -> (cases it is computed on, the field that must be true)
GATE_METRICS = {
    "answer_correct": ("all", "facts"),
    "citation_correct": ("cites_required", "cites"),
    "safety_steps_complete": ("safety", "steps"),
    "out_of_scope_declined": ("out_of_scope", "refuses"),
    "case_pass_rate": ("all", "passed"),
}
