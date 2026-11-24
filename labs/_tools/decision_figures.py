"""Figures for three decision slides: evidence for a shadow-scored replacement while outcomes are late (Day 3,
session 2), a randomised live comparison of Mubadir's reply style (Day 2, session 3) and the retraining interval
(Day 3, session 4).

    uv run python _tools/decision_figures.py

Everything is synthetic, generated here with fixed seeds; nothing reads or changes the lab data. The costs and
the decay rates are course assumptions, stated below. Every number the slides quote is printed by this script.
"""
import hashlib
import math

import numpy as np
from sklearn.metrics import roc_auc_score

REGIONS = ["RIM", "HAD", "SAH", "WAD", "JAB", "NAK"]
NAMES = {"RIM": "Al-Rimal", "HAD": "Al-Hadba", "SAH": "Al-Sahil", "WAD": "Al-Wadi", "JAB": "Al-Jabal",
         "NAK": "Al-Nakheel"}


def sigmoid(z):
    return 1 / (1 + np.exp(-z))


# ---------------------------------------------------------------------------------------------------------------
# A. A replacement fault-risk model scored in shadow; outcomes arrive late
# ---------------------------------------------------------------------------------------------------------------
def feeders(rng, n=4800):
    region = rng.choice(REGIONS, size=n, p=[0.19, 0.18, 0.17, 0.16, 0.15, 0.15])
    jab = (region == "JAB").astype(float)
    risk = rng.normal(0, 1, n) + 0.4 * jab
    dust = rng.normal(0, 1, n)
    p = sigmoid(-2.6 + 0.9 * risk + 0.3 * dust + 1.1 * dust * jab)
    champion = 0.9 * risk + 0.3 * dust + rng.normal(0, 0.6, n)
    replacement = 0.9 * risk + 0.3 * dust + 1.1 * dust * jab + rng.normal(0, 0.6, n)
    fault = rng.random(n) < p
    return region, jab, p, champion, replacement, fault


def auc_pair(y, a, b):
    return round(roc_auc_score(y, a), 3), round(roc_auc_score(y, b), 3)


def shadow_evidence():
    rng = np.random.default_rng(30521)
    print("A. Shadow-scored replacement, outcomes late")
    # the last month whose labels are complete, scored by both models (a backtest)
    region, jab, p, ch, rep, fault = feeders(rng)
    allr = auc_pair(fault, ch, rep)
    m = jab == 1
    jabr = auc_pair(fault[m], ch[m], rep[m])
    print(f"  backtest on the last complete month: AUC all champion {allr[0]} replacement {allr[1]}; "
          f"Al-Jabal champion {jabr[0]} replacement {jabr[1]}")

    # the shadow fortnight on this month's feeders
    region, jab, p, ch, rep, fault = feeders(rng)
    n = len(region)
    # outcomes known after 14 days: most faults outside Al-Jabal are reported at once; Al-Jabal faults are
    # mostly found later by inspection, and the feeders not yet faulted are not yet known to be fault-free
    reported = fault & (rng.random(n) < np.where(jab == 1, 0.25, 0.80))
    known_neg = ~fault & (rng.random(n) < 0.45)
    early = reported | known_neg
    e = auc_pair(reported[early], ch[early], rep[early])
    print(f"  after 14 days: {int(reported.sum())} faults reported of {int(fault.sum())} that the month will have; "
          f"early AUC champion {e[0]} replacement {e[1]}; Al-Jabal share of reported faults "
          f"{reported[jab == 1].sum() / reported.sum():.2f}, of all faults {fault[jab == 1].sum() / fault.sum():.2f}")

    k = n // 10
    top_ch = set(np.argsort(-ch)[:k])
    top_rep = set(np.argsort(-rep)[:k])
    overlap = len(top_ch & top_rep) / k
    only_rep = np.array(sorted(top_rep - top_ch))
    only_ch = np.array(sorted(top_ch - top_rep))
    jab_share = (region[only_rep] == "JAB").mean()
    rho = np.corrcoef(np.argsort(np.argsort(ch)), np.argsort(np.argsort(rep)))[0, 1]
    print(f"  shadow agreement: rank correlation {rho:.2f}; top-decile ({k} feeders) overlap {overlap:.2f}; "
          f"{len(only_rep)} only in the replacement's list ({jab_share:.2f} of them in Al-Jabal), "
          f"{len(only_ch)} only in the champion's")

    # a random sample from each side of the disagreement is inspected now: an inspection finds the defect that
    # would cause the fault (synthetic: present with the feeder's fault probability)
    s_rep = rng.choice(only_rep, 40, replace=False)
    s_ch = rng.choice(only_ch, 40, replace=False)
    defect = rng.random(n) < p
    f_rep, f_ch = int(defect[s_rep].sum()), int(defect[s_ch].sum())
    print(f"  inspection of 40 random feeders from each side: defects {f_rep}/40 replacement-only, "
          f"{f_ch}/40 champion-only")
    final = auc_pair(fault, ch, rep)
    print(f"  (known only because the data is invented) AUC at day 60: champion {final[0]} replacement {final[1]}")


# ---------------------------------------------------------------------------------------------------------------
# B. Mubadir's new reply style: a pilot region against a randomised comparison
# ---------------------------------------------------------------------------------------------------------------
def two_prop(a_hits, a_n, b_hits, b_n):
    pa, pb = a_hits / a_n, b_hits / b_n
    se = math.sqrt(pa * (1 - pa) / a_n + pb * (1 - pb) / b_n)
    d = pa - pb
    return pa, pb, d, d - 1.96 * se, d + 1.96 * se


def live_comparison():
    rng = np.random.default_rng(30522)
    print("B. Mubadir reply style: outcome is a repeat contact within 24 hours")
    base = {"RIM": 0.27, "HAD": 0.25, "SAH": 0.16, "WAD": 0.29, "JAB": 0.31, "NAK": 0.26}
    contacts = {"RIM": 2600, "HAD": 2400, "SAH": 2300, "WAD": 1900, "JAB": 1500, "NAK": 1700}
    effect = -0.005        # the true effect of the new style on the repeat rate (planted)
    season = -0.010        # every region's rate moves this much from one month to the next

    def month(shift, treat_fn):
        rows = []
        for r in REGIONS:
            n = contacts[r]
            t = treat_fn(r, n)
            rate = base[r] + shift + effect * t
            rows.append((r, t, rng.random(n) < rate))
        return rows

    def rate(rows, cond):
        hits = sum(int(y[cond(r, t)].sum()) for r, t, y in rows)
        n = sum(int(cond(r, t).sum()) for r, t, y in rows)
        return hits, n

    none = lambda r, n: np.zeros(n, bool)  # noqa: E731
    pilot = lambda r, n: np.full(n, r == "SAH")  # noqa: E731
    before = month(0.0, none)
    after = month(season, pilot)
    sah = lambda r, t: np.full(t.shape, r == "SAH")  # noqa: E731
    rest = lambda r, t: np.full(t.shape, r != "SAH")  # noqa: E731
    for label, rows in (("month before", before), ("pilot month", after)):
        a, an = rate(rows, sah)
        b, bn = rate(rows, rest)
        print(f"  {label}: Al-Sahil {a / an:.3f} (n {an}), other regions {b / bn:.3f} (n {bn}), "
              f"difference {a / an - b / bn:+.3f}")

    # the next month: every account assigned by a hash of its number, half and half, in every region
    def by_hash(r, n):
        ids = (f"{r}-{i:05d}" for i in range(n))      # synthetic account numbers
        return np.array([int(hashlib.sha256(f"reply-style-1:{a}".encode()).hexdigest(), 16) % 2 == 1 for a in ids])

    rand = month(season, by_hash)
    new = lambda r, t: t  # noqa: E731
    old = lambda r, t: ~t  # noqa: E731
    a, an = rate(rand, new)
    b, bn = rate(rand, old)
    pa, pb, d, lo, hi = two_prop(a, an, b, bn)
    sah_new = sum(int(t.sum()) for r, t, y in rand if r == "SAH") / an
    sah_old = sum(int((~t).sum()) for r, t, y in rand if r == "SAH") / bn
    print(f"  randomised month: new style {pa:.3f} (n {an}), current style {pb:.3f} (n {bn}), "
          f"difference {d:+.3f}, 95% interval {lo:+.3f} to {hi:+.3f}; Al-Sahil share of each arm "
          f"{sah_new:.2f} and {sah_old:.2f}")
    # the minimum detectable difference at this size (80% power, two-sided 5%)
    p0 = pb
    n_arm = (an + bn) / 2
    mde = (1.96 + 0.84) * math.sqrt(2 * p0 * (1 - p0) / n_arm)
    print(f"  smallest difference this month can detect (80% power): {mde:.3f}")


# ---------------------------------------------------------------------------------------------------------------
# C. The retraining interval: the cost of runs against the loss from a model that ages
# ---------------------------------------------------------------------------------------------------------------
RUN_COST = 1500            # SAR per run: people's time for the gate and the approval, compute, the release (assumed)
MISSED_PER_POINT = 2       # extra missed faults a month for each 0.01 of AUC lost (assumed)
MISSED_COST = 1200         # SAR per fault that a planned inspection would have prevented (assumed)


def interval_table(decay, label):
    per_age = decay / 0.01 * MISSED_PER_POINT * MISSED_COST     # SAR lost in a month, per month of model age
    print(f"  {label}: AUC falls {decay} a month, so each month of age costs {per_age:,.0f} SAR a month")
    best = None
    for k in (1, 2, 3, 4, 6):
        runs = 12 / k * RUN_COST
        stale = 12 * per_age * (k - 1) / 2                        # mean age over a cycle of k months is (k-1)/2
        total = runs + stale
        print(f"    every {k} month(s): runs {runs:,.0f}  stale {stale:,.0f}  total {total:,.0f} SAR a year")
        if best is None or total < best[1]:
            best = (k, total)
    print(f"    cheapest: every {best[0]} month(s)")


def retraining_interval():
    print("C. Retraining interval (costs are course assumptions)")
    interval_table(0.008, "dusty months")
    interval_table(0.002, "cool months")


if __name__ == "__main__":
    shadow_evidence()
    live_comparison()
    retraining_interval()
