
"""Mario Kart 8 Deluxe / SNES Rainbow Road Time Trial analyzer V0.4.

Requires:
    opencv-python, numpy
    hud_templates.py
    coin_temporal_v3.py
    rois.json
    go_reference.png
    finish_reference.png
    templates/*.png

V4 adds conservative coin gap filling and time-weighted statistics.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from coin_temporal_v3 import decode as decode_coins_v3
from hud_templates import classify as recognize_hud
from analysis_enhancements import enhance_analysis


ROI_NAMES = ("coins", "lap", "timer")
SCREEN_SIZE = (640, 360)
BANNER_THRESHOLD = 0.70

BANNER_BOXES = {
    "go": (0.358, 0.323, 0.636, 0.514),
    "finish": (0.241, 0.329, 0.765, 0.519),
}


@dataclass
class Sample:
    video_seconds: float
    coins: int | None
    lap: int | None
    race_timer_seconds: float | None
    coins_ocr: str
    lap_ocr: str
    timer_ocr: str
    race_elapsed_seconds: float | None = None


# ============================================================
# BASIC HELPERS
# ============================================================

def parse_timer(text: str) -> float | None:
    text = text.replace(" ", "").replace(",", ".").replace(";", ":")

    match = re.search(
        r"(?<!\d)(\d{1,2}):(\d{2})\.(\d{3})(?!\d)",
        text,
    )

    if match is None:
        return None

    minutes, seconds, millis = map(int, match.groups())

    if seconds >= 60:
        return None

    return round(minutes * 60 + seconds + millis / 1000, 3)


def load_rois(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))

    for name in ROI_NAMES:
        box = data.get(name) if isinstance(data, dict) else None

        if not isinstance(box, list) or len(box) != 4:
            raise ValueError(f"Invalid or missing ROI: {name}")

        if not all(isinstance(v, (int, float)) for v in box):
            raise ValueError(f"Invalid ROI coordinates: {name}")

        x, y, w, h = box

        if (
            min(x, y) < 0
            or min(w, h) <= 0
            or x + w > 1.001
            or y + h > 1.001
        ):
            raise ValueError(f"ROI outside the frame: {name}")

    return data


def crop_roi(frame: np.ndarray, box: list[float]) -> np.ndarray:
    height, width = frame.shape[:2]
    x, y, w, h = box

    return frame[
        round(y * height):round((y + h) * height),
        round(x * width):round((x + w) * width),
    ]


def read_timer_experimental(
    crop: np.ndarray,
) -> tuple[float | None, str]:
    """Experimental only. Timer OCR is disabled by default."""
    import pytesseract

    if crop.size == 0:
        return None, ""

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(
        gray, None, fx=3, fy=3,
        interpolation=cv2.INTER_CUBIC,
    )
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    _, binary = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    choices = []

    for picture in (gray, binary, cv2.bitwise_not(binary)):
        raw = pytesseract.image_to_string(
            picture,
            config=(
                "--psm 8 "
                "-c tessedit_char_whitelist=0123456789:."
            ),
        ).strip()

        parsed = parse_timer(raw)

        if parsed is not None:
            choices.append((parsed, raw))

    if not choices:
        return None, ""

    return max(
        choices,
        key=lambda p: sum(v == p[0] for v, _ in choices),
    )


# ============================================================
# GO! AND FINISH! DETECTION
# ============================================================

def gold_mask(frame: np.ndarray) -> np.ndarray:
    frame = cv2.resize(
        frame,
        SCREEN_SIZE,
        interpolation=cv2.INTER_AREA,
    )

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    return cv2.inRange(
        hsv,
        (7, 110, 130),
        (36, 255, 255),
    )


def load_banner_template(path: Path, label: str) -> np.ndarray:
    frame = cv2.imread(str(path))

    if frame is None:
        raise FileNotFoundError(
            f"Missing {label.upper()} reference screenshot: {path}"
        )

    h, w = frame.shape[:2]
    x0, y0, x1, y1 = BANNER_BOXES[label]

    crop = frame[
        round(y0 * h):round(y1 * h),
        round(x0 * w):round(x1 * w),
    ]

    mask = cv2.inRange(
        cv2.cvtColor(crop, cv2.COLOR_BGR2HSV),
        (7, 110, 130),
        (36, 255, 255),
    )

    count, labels, stats, _ = (
        cv2.connectedComponentsWithStats(mask, 8)
    )

    filtered = np.zeros_like(mask)
    min_area = max(50, round(0.00065 * w * h))

    for idx in range(1, count):
        if stats[idx, cv2.CC_STAT_AREA] >= min_area:
            filtered[labels == idx] = 255

    tw = max(
        2,
        round(crop.shape[1] * SCREEN_SIZE[0] / w),
    )
    th = max(
        2,
        round(crop.shape[0] * SCREEN_SIZE[1] / h),
    )

    template = cv2.resize(
        filtered,
        (tw, th),
        interpolation=cv2.INTER_NEAREST,
    )

    if np.count_nonzero(template) < 80:
        raise ValueError(
            f"Reference doesn't contain a readable {label} banner"
        )

    return template


def banner_match(
    frame: np.ndarray,
    template: np.ndarray,
) -> float:
    mask = gold_mask(frame)
    width, height = SCREEN_SIZE

    x_offset = round(.08 * width)
    y_offset = round(.20 * height)

    search = mask[
        y_offset:round(.65 * height),
        x_offset:round(.92 * width),
    ]

    best = 0.0

    for scale in (.90, .95, 1.0, 1.05, 1.10):
        tw = round(template.shape[1] * scale)
        th = round(template.shape[0] * scale)

        if tw >= search.shape[1] or th >= search.shape[0]:
            continue

        resized = cv2.resize(
            template,
            (tw, th),
            interpolation=cv2.INTER_NEAREST,
        )

        scores = cv2.matchTemplate(
            search,
            resized,
            cv2.TM_CCOEFF_NORMED,
        )

        _, score, _, pos = cv2.minMaxLoc(scores)

        cx = x_offset + pos[0] + tw / 2
        cy = y_offset + pos[1] + th / 2

        if (
            .28 * width <= cx <= .72 * width
            and .26 * height <= cy <= .63 * height
        ):
            best = max(best, float(score))

    return best


def detect_race_boundaries(
    video: Path,
    scan_every: float,
    go_reference: Path,
    finish_reference: Path,
) -> dict:
    if scan_every <= 0:
        raise ValueError("--scan-every must be positive")

    templates = {
        "go": load_banner_template(go_reference, "go"),
        "finish": load_banner_template(
            finish_reference, "finish"
        ),
    }

    cap = cv2.VideoCapture(str(video))

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video}")

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        cap.release()
        raise RuntimeError("Invalid video FPS")

    stride = max(1, round(fps * scan_every))

    phase = "waiting"
    consecutive = 0
    first_hit = None

    start = None
    end = None

    go_score = 0.0
    finish_score = 0.0
    index = 0

    try:
        while cap.grab():
            if index % stride == 0:
                ok, frame = cap.retrieve()

                if not ok:
                    break

                timestamp = index / fps

                if phase == "waiting":
                    score = banner_match(
                        frame, templates["go"]
                    )

                    if score >= BANNER_THRESHOLD:
                        if consecutive == 0:
                            first_hit = timestamp

                        consecutive += 1

                        if consecutive >= 2:
                            start = first_hit
                            go_score = score
                            phase = "racing"
                            consecutive = 0

                            print(
                                f"GO! detected at {start:.3f}s "
                                f"(match {go_score:.3f})"
                            )
                    else:
                        consecutive = 0

                elif timestamp > start + 1:
                    score = banner_match(
                        frame, templates["finish"]
                    )

                    if score >= BANNER_THRESHOLD:
                        if consecutive == 0:
                            first_hit = timestamp

                        consecutive += 1

                        if consecutive >= 2:
                            end = first_hit
                            finish_score = score

                            print(
                                f"FINISH! detected at {end:.3f}s "
                                f"(match {finish_score:.3f})"
                            )
                            break
                    else:
                        consecutive = 0

            index += 1

    finally:
        cap.release()

    if start is None or end is None:
        missing = "GO!" if start is None else "FINISH!"
        raise RuntimeError(
            f"Couldn't detect {missing}; "
            "use --start and --end as a fallback"
        )

    return {
        "start_video_seconds": round(start, 3),
        "end_video_seconds": round(end, 3),
        "method": "gold_template_matching",
        "go_match_score": round(go_score, 3),
        "finish_match_score": round(finish_score, 3),
    }


# ============================================================
# VIDEO SAMPLING
# ============================================================

def sample_video(
    video: Path,
    rois: dict,
    every: float,
    start: float,
    end: float | None,
    debug_dir: Path | None = None,
    ocr_timer: bool = False,
) -> tuple[list[Sample], dict]:

    if every <= 0:
        raise ValueError("--every must be positive")

    cap = cv2.VideoCapture(str(video))

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps <= 0:
        cap.release()
        raise RuntimeError("Invalid video FPS")

    first = max(0, round(fps * start))

    stop = (
        total_frames
        if end is None
        else min(total_frames, round(fps * end))
    )

    if first >= stop:
        cap.release()
        raise ValueError("The selected race window is empty")

    step = max(1, round(fps * every))
    samples = []

    if debug_dir:
        debug_dir.mkdir(parents=True, exist_ok=True)

    cap.set(cv2.CAP_PROP_POS_FRAMES, first)
    index = first

    try:
        while index < stop and cap.grab():
            if (index - first) % step == 0:
                ok, frame = cap.retrieve()

                if not ok:
                    break

                coins, coins_note = recognize_hud(
                    crop_roi(frame, rois["coins"]),
                    "coins",
                )

                lap, lap_note = recognize_hud(
                    crop_roi(frame, rois["lap"]),
                    "lap",
                )

                timer, timer_note = (
                    read_timer_experimental(
                        crop_roi(frame, rois["timer"])
                    )
                    if ocr_timer
                    else (None, "")
                )

                samples.append(
                    Sample(
                        video_seconds=round(index / fps, 3),
                        coins=coins,
                        lap=lap,
                        race_timer_seconds=timer,
                        coins_ocr=coins_note,
                        lap_ocr=lap_note,
                        timer_ocr=timer_note,
                        race_elapsed_seconds=round(
                            (index - first) / fps, 3
                        ),
                    )
                )

                if debug_dir and len(samples) % 15 == 1:
                    overlay = frame.copy()

                    for name in ROI_NAMES:
                        x, y, w, h = rois[name]
                        hh, ww = overlay.shape[:2]

                        p1 = (
                            round(x * ww),
                            round(y * hh),
                        )
                        p2 = (
                            round((x + w) * ww),
                            round((y + h) * hh),
                        )

                        cv2.rectangle(
                            overlay, p1, p2,
                            (0, 255, 255), 2,
                        )
                        cv2.putText(
                            overlay,
                            name,
                            p1,
                            cv2.FONT_HERSHEY_SIMPLEX,
                            .65,
                            (255, 255, 255),
                            2,
                        )

                    cv2.imwrite(
                        str(
                            debug_dir
                            / f"frame_{index:07}.jpg"
                        ),
                        overlay,
                    )

            index += 1

    finally:
        cap.release()

    return samples, {
        "fps": fps,
        "total_frames": total_frames,
        "duration_seconds": round(total_frames / fps, 3),
        "samples": len(samples),
        "race_start_video_seconds": round(first / fps, 3),
        "race_end_video_seconds": round(stop / fps, 3),
    }


# ============================================================
# LAP TIMING
# ============================================================

def lap_transitions(samples: list[Sample]) -> list[dict]:
    laps = [s.lap for s in samples]
    times = [s.video_seconds for s in samples]

    result = []
    previous_index = 0

    for old_lap, new_lap in ((1, 2), (2, 3)):
        found = None

        for i in range(previous_index + 1, len(samples)):
            if laps[i] != new_lap:
                continue

            before = laps[max(previous_index, i - 8):i]
            after = laps[i:i + 12]

            if (
                before.count(old_lap) < 5
                or after.count(new_lap) < 7
            ):
                continue

            previous = next(
                (
                    j for j in range(
                        i - 1,
                        previous_index - 1,
                        -1,
                    )
                    if laps[j] == old_lap
                ),
                None,
            )

            if previous is None:
                continue

            midpoint = (times[previous] + times[i]) / 2

            found = {
                "new_lap": new_lap,
                "last_previous_lap_frame": round(
                    times[previous], 3
                ),
                "first_new_lap_frame": round(
                    times[i], 3
                ),
                "boundary_video_seconds_estimate": round(
                    midpoint, 3
                ),
                "sampling_uncertainty_seconds": round(
                    (times[i] - times[previous]) / 2, 3
                ),
            }

            previous_index = i
            break

        if found is None:
            break

        result.append(found)

    return result


def summarize(
    samples: list[Sample],
    bounds: dict,
    final_time: float | None,
) -> dict:
    transitions = lap_transitions(samples)
    start = bounds["start_video_seconds"]

    lap_times = [None, None, None]

    if transitions:
        first = transitions[0][
            "boundary_video_seconds_estimate"
        ]
        lap_times[0] = round(first - start, 3)

    if len(transitions) == 2:
        second = transitions[1][
            "boundary_video_seconds_estimate"
        ]

        lap_times[1] = round(second - first, 3)

        if final_time is not None:
            lap_times[2] = round(
                final_time - (second - start), 3
            )

    if any(
        t is not None and t <= 0
        for t in lap_times
    ):
        raise ValueError(
            "Implausible lap estimate; verify transitions"
        )

    raw_coins = [
        s.coins
        for s in samples
        if s.coins is not None
    ]

    return {
        "schema_version": "0.4",
        "mode": "TimeTrial",
        "track": "SNES Rainbow Road",
        "lap_transitions": transitions,
        "lap_times_seconds_approx": lap_times,
        "lap_metrics_present": all(
            t is not None for t in lap_times
        ),
        "final_time_seconds": final_time,
        "final_time_source": (
            "user_verified_manual"
            if final_time is not None
            else "unavailable"
        ),
        "average_coins": (
            round(sum(raw_coins) / len(raw_coins), 3)
            if raw_coins else None
        ),
        "valid_coin_samples": len(raw_coins),
        "total_samples": len(samples),
        "coin_read_coverage": (
            round(len(raw_coins) / len(samples), 3)
            if samples else 0
        ),
        "overall_score_ready": False,
        "limitations": [
            "Lap timing is estimated from lap-counter transitions.",
            "Final lap timing requires the official total.",
            "Raw and inferred coins require validation before scoring.",
            "Coin V4 leaves uncertain periods unresolved.",
            "Coin-loss events are not independently verified.",
            "Continuous timer OCR is unreliable.",
        ],
    }


# ============================================================
# COIN V3 TEMPORAL DECODING
# ============================================================

def enrich_coins_v3(
    samples: list[Sample],
) -> tuple[list[dict], dict]:

    rows = [asdict(s) for s in samples]

    evidence_rows = [
        {
            "video_seconds": str(s.video_seconds),
            "coins": (
                "" if s.coins is None else str(s.coins)
            ),
            "coins_ocr": s.coins_ocr,
        }
        for s in samples
    ]

    records, _ = (
        decode_coins_v3(evidence_rows)
        if samples else ([], [])
    )

    if len(records) != len(rows):
        raise RuntimeError(
            "V3 decoder returned an unexpected number of records"
        )

    states = []
    valid = []
    sources = Counter()

    for row, record in zip(rows, records):
        (
            value,
            source,
            support,
            state,
            guess,
            similarity,
            margin,
        ) = record

        row.update({
            "coins_v3": (
                "" if value is None else value
            ),
            "coins_v3_source": source,
            "coins_v3_support": support,
            "coins_v3_state_unverified": state,
            "coins_v3_raw_best": (
                "" if guess is None else guess
            ),
            "coins_v3_raw_similarity": similarity,
            "coins_v3_raw_margin": margin,
        })

        states.append((row["video_seconds"], state))
        sources[source] += 1

        if value is not None:
            valid.append(value)

    candidate_changes = [
        {
            "video_seconds": timestamp,
            "from_state": old_state,
            "to_state": state,
            "needs_video_validation": True,
        }
        for (timestamp, state), (_, old_state)
        in zip(states[1:], states[:-1])
        if state != old_state
    ]

    summary = {
        "coverage": (
            round(len(valid) / len(rows), 3)
            if rows else 0
        ),
        "resolved_samples": len(valid),
        "unresolved_samples": len(rows) - len(valid),
        "source_counts": dict(sources),
        "provisional_average_coins": (
            round(sum(valid) / len(valid), 3)
            if valid else None
        ),
        "provisional_fraction_at_10": (
            round(
                sum(v == 10 for v in valid) / len(valid),
                3,
            )
            if valid else None
        ),
        "candidate_state_changes_for_review": (
            candidate_changes
        ),
        "verified": False,
        "notes": (
            "V3 support is local evidence, not a calibrated "
            "probability. State changes remain unverified."
        ),
    }

    return rows, summary


# ============================================================
# COIN V4 GAP FILLING AND TIME-WEIGHTED ANALYTICS
# ============================================================

def _coin_value(value) -> int | None:
    """Convert missing data without turning it into zero."""
    if value is None or value == "":
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(number) or not number.is_integer():
        return None

    integer = int(number)

    return integer if 0 <= integer <= 10 else None


def _local_stable(
    values: list[int | None],
    index: int,
    target: int,
    side: str,
) -> bool:
    """Require at least two agreeing readings near the gap."""

    if side == "left":
        neighbors = values[
            max(0, index - 4):index + 1
        ]
    else:
        neighbors = values[
            index:min(len(values), index + 5)
        ]

    known = [
        value for value in neighbors
        if value is not None
    ]

    return (
        len(known) >= 2
        and known.count(target) >= 2
        and known.count(target) / len(known) >= .67
    )


def coin_analytics_v4(
    rows: list[dict],
    bounds: dict,
    max_gap_seconds: float = 1.0,
) -> tuple[list[dict], dict]:
    """
    Estimate short missing intervals and calculate
    time-weighted coin statistics.

    Original raw/V3 readings are never overwritten.
    """

    if not 0 < max_gap_seconds <= 3:
        raise ValueError(
            "--max-coin-gap must be between 0 and 3 seconds"
        )

    if not rows:
        return rows, {
            "average_coins_time_weighted": None,
            "time_coverage_fraction": 0.0,
            "time_at_10_coins_seconds_estimated": 0.0,
            "unresolved_samples": 0,
        }

    times = [
        float(row["video_seconds"])
        for row in rows
    ]

    if any(
        b <= a
        for a, b in zip(times, times[1:])
    ):
        raise ValueError(
            "Video timestamps must be strictly increasing"
        )

    start = float(bounds["start_video_seconds"])
    finish_value = bounds.get("end_video_seconds")

    finish = (
        float(finish_value)
        if finish_value is not None
        else times[-1] + (
            times[-1] - times[-2]
            if len(times) > 1
            else .2
        ) / 2
    )

    if (
        finish <= start
        or times[0] < start - .01
        or times[-1] > finish + .01
    ):
        raise ValueError(
            "Coin timestamps don't match race boundaries"
        )

    v3 = [
        _coin_value(row.get("coins_v3"))
        for row in rows
    ]

    values = v3.copy()

    sources = [
        (
            f"v3_{row.get('coins_v3_source', 'accepted')}"
            if value is not None
            else "unresolved"
        )
        for row, value in zip(rows, v3)
    ]

    gaps_filled = []
    gaps_unresolved = []

    index = 0

    while index < len(rows):

        if v3[index] is not None:
            index += 1
            continue

        first_missing = index

        while index < len(rows) and v3[index] is None:
            index += 1

        after = index
        before = first_missing - 1

        event = {
            "first_missing_video_seconds": round(
                times[first_missing], 3
            ),
            "last_missing_video_seconds": round(
                times[after - 1], 3
            ),
            "missing_samples": after - first_missing,
        }

        if before < 0 or after >= len(rows):
            event["reason"] = "missing_both_endpoints"
            gaps_unresolved.append(event)
            continue

        left = v3[before]
        right = v3[after]
        duration = times[after] - times[before]

        event.update({
            "left_coin_count": left,
            "right_coin_count": right,
            "endpoint_span_seconds": round(
                duration, 3
            ),
        })

        # Rule 1: Never bridge a long gap.
        if duration > max_gap_seconds + 1e-9:
            event["reason"] = "long_gap"
            gaps_unresolved.append(event)
            continue

        # Rule 2: Both sides must be locally stable.
        if not (
            _local_stable(v3, before, left, "left")
            and _local_stable(v3, after, right, "right")
        ):
            event["reason"] = (
                "insufficient_plateau_evidence"
            )
            gaps_unresolved.append(event)
            continue

        # Rule 3: Be cautious about possible coin losses.
        if right < left:
            event["reason"] = "possible_coin_loss"
            gaps_unresolved.append(event)
            continue

        # Rule 4: Don't override strong contradictory
        # image evidence in the missing interval.
        conflict = False

        for k in range(first_missing, after):
            raw = _coin_value(
                rows[k].get("coins")
            )

            if raw is None or raw in (left, right):
                continue

            try:
                similarity = float(
                    rows[k].get(
                        "coins_v3_raw_similarity"
                    ) or 0
                )
            except (TypeError, ValueError):
                similarity = 0.0

            if similarity >= .78:
                conflict = True
                break

        if conflict:
            event["reason"] = "conflicting_raw_evidence"
            gaps_unresolved.append(event)
            continue

        # Rule 5: Fill stable gaps or approximate
        # an increasing transition at its midpoint.
        midpoint = (
            times[before] + times[after]
        ) / 2

        for k in range(first_missing, after):
            if left == right:
                values[k] = left
                sources[k] = (
                    "v4_stable_gap_estimate"
                )

            else:
                values[k] = (
                    left
                    if times[k] < midpoint
                    else right
                )

                sources[k] = (
                    "v4_transition_midpoint_estimate"
                )

        event["method"] = (
            "stable_endpoints"
            if left == right
            else "transition_midpoint"
        )

        gaps_filled.append(event)

    # --------------------------------------------------------
    # TIME-WEIGHTED COIN STATISTICS
    # --------------------------------------------------------

    # Each sampled frame represents the period halfway
    # to the previous and next sampled frames.
    edges = [start]

    edges.extend(
        (a + b) / 2
        for a, b in zip(times, times[1:])
    )

    edges.append(finish)

    weights = [
        max(0.0, b - a)
        for a, b in zip(edges, edges[1:])
    ]

    race_seconds = finish - start

    counted_seconds = sum(
        dt
        for value, dt in zip(values, weights)
        if value is not None
    )

    unknown_seconds = max(
        0.0,
        race_seconds - counted_seconds,
    )

    weighted_coins = sum(
        value * dt
        for value, dt in zip(values, weights)
        if value is not None
    )

    seconds_at_10 = sum(
        dt
        for value, dt in zip(values, weights)
        if value == 10
    )

    imputed_seconds = sum(
        dt
        for source, dt in zip(sources, weights)
        if source.startswith("v4_")
    )

    # Preserve all evidence and add new V4 columns.
    for row, value, source, dt in zip(
        rows, values, sources, weights
    ):
        row["coins_v4"] = (
            "" if value is None else value
        )
        row["coins_v4_source"] = source
        row["coins_v4_interval_seconds"] = round(
            dt, 6
        )

    average = (
        weighted_coins / counted_seconds
        if counted_seconds > 0
        else None
    )

    summary = {
        "method": (
            "time_weighted_v3_plus_guarded_short_gap_estimates"
        ),
        "max_endpoint_gap_seconds": max_gap_seconds,
        "total_samples": len(rows),
        "resolved_samples": sum(
            value is not None
            for value in values
        ),
        "newly_imputed_samples": sum(
            source.startswith("v4_")
            for source in sources
        ),
        "unresolved_samples": sum(
            value is None
            for value in values
        ),
        "source_counts": dict(Counter(sources)),
        "race_window_seconds": round(
            race_seconds, 3
        ),
        "resolved_time_seconds": round(
            counted_seconds, 3
        ),
        "estimated_added_time_seconds": round(
            imputed_seconds, 3
        ),
        "unresolved_time_seconds": round(
            unknown_seconds, 3
        ),
        "time_coverage_fraction": round(
            counted_seconds / race_seconds, 4
        ),
        "average_coins_time_weighted": (
            round(average, 3)
            if average is not None
            else None
        ),
        "time_at_10_coins_seconds_estimated": round(
            seconds_at_10, 3
        ),
        "fraction_of_resolved_time_at_10_coins": (
            round(
                seconds_at_10 / counted_seconds,
                4,
            )
            if counted_seconds
            else None
        ),
        "fraction_of_race_time_assigned_10_coins": round(
            seconds_at_10 / race_seconds,
            4,
        ),
        "average_coins_possible_range_from_unknown_time": [
            round(
                weighted_coins / race_seconds,
                3,
            ),
            round(
                (
                    weighted_coins
                    + 10 * unknown_seconds
                ) / race_seconds,
                3,
            ),
        ],
        "gap_fill_events": gaps_filled,
        "unresolved_gap_events": gaps_unresolved,
        "confirmed_coin_loss_events": None,
        "verified": False,
        "notes": [
            (
                "Unresolved time is excluded from both "
                "the weighted numerator and denominator."
            ),
            (
                "Estimated values are not direct observations "
                "or calibrated probabilities."
            ),
            (
                "A short gap with matching endpoints may "
                "conceal a fast coin loss and recovery."
            ),
            (
                "Coin losses require verification before scoring."
            ),
            (
                "The race window uses GO!/FINISH! video "
                "timestamps, not exact game timer ticks."
            ),
        ],
    }

    return rows, summary


# ============================================================
# HUD CALIBRATION
# ============================================================

def calibrate(
    video: Path,
    at: float,
    dest: Path,
) -> None:
    cap = cv2.VideoCapture(str(video))

    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video}")

    cap.set(cv2.CAP_PROP_POS_MSEC, at * 1000)

    ok, frame = cap.read()
    cap.release()

    if not ok:
        raise RuntimeError(
            f"Cannot read video at {at}s"
        )

    h, w = frame.shape[:2]
    scale = min(1.0, 1280 / w, 720 / h)

    resized = cv2.resize(
        frame,
        (round(w * scale), round(h * scale)),
    )

    rw, rh = resized.shape[1], resized.shape[0]
    rois = {}

    for name, instruction in (
        (
            "coins",
            "Select ONLY the coin digits (00 through 10)",
        ),
        (
            "lap",
            "Select ONLY the lap numerator (1, 2, or 3)",
        ),
        (
            "timer",
            "Select the entire top-right timer",
        ),
    ):
        print(
            f"\n{name}: {instruction}; "
            "press ENTER to confirm"
        )

        x, y, cw, ch = cv2.selectROI(
            f"Select {name}",
            resized,
            showCrosshair=True,
            fromCenter=False,
        )

        cv2.destroyAllWindows()

        if cw <= 0 or ch <= 0:
            raise ValueError(
                f"No ROI selected for {name}"
            )

        rois[name] = [
            round(x / rw, 6),
            round(y / rh, 6),
            round(cw / rw, 6),
            round(ch / rh, 6),
        ]

    dest.parent.mkdir(
        parents=True, exist_ok=True
    )

    dest.write_text(
        json.dumps(rois, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Saved {dest}")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Mario Kart Time Trial analyzer "
            "with Coin V4 statistics"
        )
    )

    sub = parser.add_subparsers(
        dest="cmd",
        required=True,
    )

    cal = sub.add_parser("calibrate")
    cal.add_argument("video", type=Path)
    cal.add_argument(
        "--at", type=float, default=15.0
    )
    cal.add_argument(
        "--rois",
        type=Path,
        default=Path("rois.json"),
    )

    analyze = sub.add_parser("analyze")
    analyze.add_argument("video", type=Path)
    analyze.add_argument(
        "--rois",
        type=Path,
        default=Path("rois.json"),
    )
    analyze.add_argument(
        "--out",
        type=Path,
        default=Path("results"),
    )
    analyze.add_argument(
        "--every",
        type=float,
        default=0.2,
    )
    analyze.add_argument(
        "--auto-boundaries",
        action="store_true",
    )
    analyze.add_argument(
        "--scan-every",
        type=float,
        default=0.1,
    )
    analyze.add_argument(
        "--go-reference",
        type=Path,
        default=Path("go_reference.png"),
    )
    analyze.add_argument(
        "--finish-reference",
        type=Path,
        default=Path("finish_reference.png"),
    )
    analyze.add_argument(
        "--start", type=float
    )
    analyze.add_argument(
        "--end", type=float
    )
    analyze.add_argument(
        "--final-time", type=str
    )
    analyze.add_argument(
        "--debug",
        action="store_true",
    )
    analyze.add_argument(
        "--max-coin-gap",
        type=float,
        default=1.0,
        help=(
            "Maximum known-endpoint gap for coin "
            "estimates, in seconds"
        ),
    )
    analyze.add_argument(
        "--ocr-timer",
        action="store_true",
        help="Experimental timer OCR; not used for lap timing",
    )

    args = parser.parse_args()

    if args.cmd == "calibrate":
        calibrate(args.video, args.at, args.rois)
        return

    if args.auto_boundaries and (
        args.start is not None
        or args.end is not None
    ):
        parser.error(
            "Choose --auto-boundaries OR --start/--end"
        )

    if args.start is not None or args.end is not None:
        if (
            args.start is None
            or args.end is None
            or args.start < 0
            or args.end <= args.start
        ):
            parser.error(
                "Manual mode requires valid --start and --end"
            )

    final = (
        parse_timer(args.final_time)
        if args.final_time is not None
        else None
    )

    if args.final_time is not None and final is None:
        parser.error(
            "Use --final-time M:SS.mmm"
        )

    rois = load_rois(args.rois)

    if args.auto_boundaries:
        bounds = detect_race_boundaries(
            args.video,
            args.scan_every,
            args.go_reference,
            args.finish_reference,
        )

    elif args.start is not None:
        bounds = {
            "start_video_seconds": args.start,
            "end_video_seconds": args.end,
            "method": "manual_video_timestamps",
        }

    else:
        print(
            "WARNING: Analyzing the full video. "
            "Use --auto-boundaries for race-only samples."
        )

        bounds = {
            "start_video_seconds": 0.0,
            "end_video_seconds": None,
            "method": "full_video",
        }

    args.out.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Collecting HUD samples...")

    samples, info = sample_video(
        args.video,
        rois,
        args.every,
        bounds["start_video_seconds"],
        bounds["end_video_seconds"],
        debug_dir=(
            args.out / "debug"
            if args.debug else None
        ),
        ocr_timer=args.ocr_timer,
    )

    print(
        f"Collected {len(samples)} samples. "
        "Running Coin V3 temporal decoder..."
    )

    enriched, coin_v3_summary = enrich_coins_v3(
        samples
    )

    print(
        "Calculating Coin V4 gap estimates "
        "and time-weighted statistics..."
    )

    enriched, coin_v4_summary = coin_analytics_v4(
        enriched,
        bounds,
        args.max_coin_gap,
    )

    summary = summarize(
        samples,
        bounds,
        final,
    )

    summary.update({
        "video_name": args.video.name,
        "video_info": info,
        "race_bounds": bounds,
        "coin_v3": coin_v3_summary,
        "coin_v4": coin_v4_summary,
    })

    # Keep both original and improved coin averages.
    summary["raw_average_coins"] = summary["average_coins"]

    summary["average_coins"] = coin_v4_summary[
        "average_coins_time_weighted"
    ]

    summary["coin_average_method"] = coin_v4_summary[
        "method"
    ]

    # Original HUD observations.
    with (args.out / "samples.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(
                Sample.__dataclass_fields__
            ),
        )
        writer.writeheader()
        writer.writerows(
            asdict(s) for s in samples
        )

    if enriched:
        # Save original V3 output separately.
        v3_fields = [
            key for key in enriched[0]
            if not key.startswith("coins_v4")
        ]

        with (args.out / "coins_v3.csv").open(
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=v3_fields,
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(enriched)

        # Full V4 results with estimated intervals.
        with (args.out / "coins_v4.csv").open(
            "w",
            newline="",
            encoding="utf-8",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=list(enriched[0]),
            )
            writer.writeheader()
            writer.writerows(enriched)

    (args.out / "race_bounds.json").write_text(
        json.dumps(bounds, indent=2) + "\n",
        encoding="utf-8",
    )

    (args.out / "score_input.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = enhance_analysis(args.out)

    print(json.dumps({
        "samples": len(samples),
        "lap_times_seconds_approx": summary[
            "lap_times_seconds_approx"
        ],
        "coin_v3_coverage": coin_v3_summary[
            "coverage"
        ],
        "coin_v3_provisional_average": (
            coin_v3_summary["provisional_average_coins"]
        ),
        "coin_v4_estimated_average": (
            coin_v4_summary["average_coins_time_weighted"]
        ),
        "coin_v4_time_coverage": (
            coin_v4_summary["time_coverage_fraction"]
        ),
        "coin_v4_time_at_10_seconds": (
            coin_v4_summary[
                "time_at_10_coins_seconds_estimated"
            ]
        ),
        "output_folder": str(args.out),
    }, indent=2))

if __name__ == "__main__":
    main()
