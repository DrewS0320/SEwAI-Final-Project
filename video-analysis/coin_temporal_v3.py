
"""Mario Kart coin temporal decoding V3.1.

Drop-in replacement for coin_temporal_v3.py.
Compatible with the existing V4 analyzer.py.

Improves acceptance of strongly recognized coin values during
transitions without changing the underlying state model.
"""

import argparse
import csv
import json
import re
from bisect import bisect_left, bisect_right
from collections import Counter
from pathlib import Path

import numpy as np


PATTERN = re.compile(
    r"template:(?:uncertain best=)?(\d+)"
    r"\s+sim=([0-9.]+)\s+gap=([0-9.]+)"
)


def _read_coin(text):
    try:
        value = int(float(text))
        return value if 0 <= value <= 10 else None
    except (TypeError, ValueError):
        return None


def get_evidence(row):
    """Extract image candidate, similarity, margin, and strength."""

    observed = _read_coin(row.get("coins"))

    match = PATTERN.search(
        str(row.get("coins_ocr") or "")
    )

    if not match:
        return None, 0.0, 0.0, 0.0

    value = int(match[1])
    sim = float(match[2])
    gap = float(match[3])

    if not 0 <= value <= 10:
        return None, 0.0, 0.0, 0.0

    # The white '00' display sometimes has lower similarity.
    if (
        observed == value == 0
        and sim >= 0.54
        and gap >= 0.4
    ):
        strength = 0.85 + max(0, sim - 0.54) * 3
        return 0, sim, gap, strength

    if sim < 0.58:
        return None, sim, gap, 0.0

    if observed is None and sim < 0.78:
        return None, sim, gap, 0.0

    strength = min(
        4.8,
        (sim - 0.58) * 8
        + (0.65 if observed == value else 0)
        + min(0.8, gap * 4),
    )

    return value, sim, gap, strength


def decode(rows):
    """
    Decode coin counts using visual and temporal evidence.

    Returns:
        records, evidence

    Each record contains:
        accepted_count
        source
        local_support
        unverified_state
        image_guess
        similarity
        margin
    """

    n = len(rows)

    if n == 0:
        return [], []

    ts = [
        float(row["video_seconds"])
        for row in rows
    ]

    if any(
        ts[i] <= ts[i - 1]
        for i in range(1, n)
    ):
        raise ValueError(
            "Rows must be sorted by video_seconds"
        )

    observed = [
        _read_coin(row.get("coins"))
        for row in rows
    ]

    evidence = [
        get_evidence(row)
        for row in rows
    ]

    # --------------------------------------------------------
    # PART 1: TEMPORAL STATE MODEL
    # --------------------------------------------------------

    # Keep the original V3 model unchanged.
    emission = np.zeros(
        (n, 11),
        dtype=np.float32
    )

    for i, (value, sim, gap, strength) in enumerate(
        evidence
    ):
        if value is not None:
            emission[i, value] = -strength

    penalty = np.zeros(
        (11, 11),
        dtype=np.float32
    )

    for old in range(11):
        for new in range(11):

            if new == old:
                continue

            if new > old:
                penalty[old, new] = (
                    1.5 + (new - old - 1)
                )

            else:
                penalty[old, new] = (
                    2.1
                    + 0.85 * max(
                        0, old - new - 3
                    )
                )

    back = np.zeros(
        (n, 11),
        dtype=np.int8
    )

    cost = emission[0].copy()

    for i in range(1, n):
        dt = ts[i] - ts[i - 1]

        transitions = (
            cost[:, None]
            + penalty * min(1.0, 0.20 / dt)
        )

        back[i] = np.argmin(
            transitions,
            axis=0
        )

        cost = (
            emission[i]
            + np.min(transitions, axis=0)
        )

    states = [0] * n
    states[-1] = int(np.argmin(cost))

    for i in range(n - 1, 0, -1):
        states[i - 1] = int(
            back[i, states[i]]
        )

    # --------------------------------------------------------
    # PART 2: CONFIDENCE-AWARE ACCEPTANCE
    # --------------------------------------------------------

    results = []

    left = 0
    right = 0

    for i in range(n):
        now = ts[i]

        guess, sim, gap, strength = evidence[i]

        chosen = states[i]

        # Inspect nearby frames within 0.65 seconds.
        while (
            left < n
            and ts[left] < now - 0.65
        ):
            left += 1

        if right < i:
            right = i

        while (
            right < n
            and ts[right] <= now + 0.65
        ):
            right += 1

        neighbors = range(left, right)

        support = sum(
            evidence[j][3]
            for j in neighbors
            if evidence[j][0] == chosen
        )

        opposition = sum(
            evidence[j][3]
            for j in neighbors
            if evidence[j][0] not in (
                None, chosen
            )
        )

        total = support + opposition

        ratio = (
            support / total
            if total > 0
            else 0.0
        )

        supported_left = any(
            j < i
            and evidence[j][0] == chosen
            and evidence[j][3] >= 1.3
            for j in neighbors
        )

        supported_right = any(
            j > i
            and evidence[j][0] == chosen
            and evidence[j][3] >= 1.3
            for j in neighbors
        )

        # ----------------------------------------------------
        # NEW FIX 1:
        # Preserve a strong direct reading during a pickup.
        #
        # The image and the temporal model must agree.
        # This avoids accepting isolated false 8s among 0s.
        # ----------------------------------------------------

        strong_direct = (
            observed[i] == chosen
            and guess == chosen
            and sim >= 0.94
            and gap >= 0.025
        )

        # ----------------------------------------------------
        # NEW FIX 2:
        # Recover a strong but previously rejected reading
        # when another nearby frame supports the same value.
        #
        # Particularly useful around 8-9 coins.
        # ----------------------------------------------------

        lookback = bisect_left(
            ts, now - 1.2
        )

        lookahead = bisect_right(
            ts, now + 1.2
        )

        corroborated_weak = (
            observed[i] is None
            and guess == chosen
            and sim >= 0.92
            and gap >= 0.012
            and any(
                j != i
                and abs(ts[j] - now) <= 1.2
                and states[j] == chosen
                and evidence[j][0] == chosen
                and evidence[j][1] >= 0.88
                for j in range(
                    lookback, lookahead
                )
            )
        )

        # ----------------------------------------------------
        # PART 3: ACCEPT OR REJECT
        # ----------------------------------------------------

        if (
            guess == chosen
            and strength >= 0.8
            and ratio >= 0.6
        ):
            source = "observed_supported"

        elif strong_direct:
            source = "strong_transition_observed"

        elif corroborated_weak:
            source = "strong_weak_guess_confirmed"

        elif (
            supported_left
            and supported_right
            and ratio >= 0.72
        ):
            source = (
                "corrected_raw"
                if observed[i] is not None
                else "inferred_gap"
            )

        else:
            source = "unresolved"

        accepted = (
            chosen
            if source != "unresolved"
            else None
        )

        results.append((
            accepted,
            source,
            round(ratio, 3),
            chosen,
            guess,
            round(sim, 3),
            round(gap, 3),
        ))

    return results, evidence


# ============================================================
# OPTIONAL STANDALONE TEST
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Mario Kart temporal coin decoder V3.1"
        )
    )

    parser.add_argument(
        "samples_csv",
        type=Path
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=Path("results_coins_v3_1"),
    )

    args = parser.parse_args()

    with args.samples_csv.open(
        newline="",
        encoding="utf-8-sig"
    ) as f:
        rows = list(csv.DictReader(f))

    required = {
        "video_seconds",
        "coins",
        "coins_ocr",
    }

    if (
        not rows
        or not required.issubset(rows[0])
    ):
        raise ValueError(
            "CSV must contain video_seconds, "
            "coins, and coins_ocr"
        )

    records, evidence = decode(rows)

    for row, record in zip(rows, records):
        (
            coin,
            source,
            ratio,
            state,
            guess,
            sim,
            gap,
        ) = record

        row.update({
            "coins_v3": (
                "" if coin is None else coin
            ),
            "coins_v3_source": source,
            "coins_v3_support": ratio,
            "coins_v3_state_unverified": state,
            "coins_v3_raw_best": (
                "" if guess is None else guess
            ),
            "coins_v3_raw_similarity": sim,
            "coins_v3_raw_margin": gap,
        })

    args.out.mkdir(
        parents=True,
        exist_ok=True
    )

    output_csv = args.out / "coins_v3.csv"

    with output_csv.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(rows)

    resolved = [
        record[0]
        for record in records
        if record[0] is not None
    ]

    report = {
        "total_samples": len(rows),
        "coverage": round(
            len(resolved) / len(rows), 3
        ),
        "source_counts": dict(
            Counter(
                record[1]
                for record in records
            )
        ),
        "provisional_average": (
            round(
                sum(resolved) / len(resolved),
                3
            )
            if resolved else None
        ),
        "coin_losses_verified": False,
    }

    (
        args.out / "coins_v3_summary.json"
    ).write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8"
    )

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
