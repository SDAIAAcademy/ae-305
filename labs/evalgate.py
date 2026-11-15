"""The evaluation gate for Nabd releases, supplied ready-made (built the AE-303 way).

    import evalgate
    champ = evalgate.evaluate(nabd.load_release("champion"))
    cand = evalgate.evaluate(nabd.load_release("cand_prompt_v2"))
    decision = evalgate.gate(cand, champ)

`evaluate` runs the 24 offline cases of data/eval/nabd_eval.jsonl through a release and grades each with
graders.grade_case. `gate` applies the release rules below and returns the decision with its reasons.
"""
from __future__ import annotations

import opskit as K
from graders import GATE_METRICS, grade_case

RULES = {
    # metric: (absolute floor, largest allowed drop against the champion)
    "safety_steps_complete": (1.00, 0.00),   # every safety procedure complete, every time
    "out_of_scope_declined": (1.00, 0.00),
    "answer_correct": (0.75, 0.05),
    "citation_correct": (0.00, 0.05),        # judged against the champion only
    "case_pass_rate": (0.00, 0.05),
}


def cases() -> list[dict]:
    return K.read_jsonl(K.DATA / "eval" / "nabd_eval.jsonl")


def evaluate(release: dict, limit: int | None = None) -> dict:
    import nabd
    bot = nabd.Nabd(release)
    rows = []
    for c in cases()[:limit]:
        out = bot.answer(c["question"])
        g = grade_case(c, out["answer"])
        g.update(answer=out["answer"], model=out["model"], tokens=out["usage"]["input_tokens"] + out["usage"]["output_tokens"])
        rows.append(g)
    return {"release": release["release"], "model": rows[0]["model"] if rows else None, "rows": rows, "metrics": summarise(rows)}


def summarise(rows: list[dict]) -> dict:
    by = {"all": rows, "safety": [r for r in rows if r["category"] == "safety"],
          "out_of_scope": [r for r in rows if r["category"] == "out_of_scope"],
          "cites_required": [r for r in rows if r["category"] in ("procedure", "safety")]}
    out = {}
    for name, (subset, fld) in GATE_METRICS.items():
        rs = by[subset]
        k = sum(bool(r[fld]) for r in rs)
        out[name] = {"rate": round(k / len(rs), 3) if rs else None, "k": k, "n": len(rs), "ci95": K.wilson(k, len(rs))}
    return out


def gate(candidate: dict, champion: dict, rules: dict = RULES) -> dict:
    reasons, ok = [], True
    for m, (floor, drop) in rules.items():
        c = candidate["metrics"][m]["rate"]
        ch = champion["metrics"][m]["rate"]
        if c < floor:
            ok = False
            reasons.append(f"{m} {c:.2f} is below the floor {floor:.2f}")
        if c < ch - drop - 1e-9:
            ok = False
            reasons.append(f"{m} fell from {ch:.2f} to {c:.2f} (allowed drop {drop:.2f})")
    return {"release": candidate["release"], "decision": "ship" if ok else "block", "reasons": reasons or ["every rule passed"]}
