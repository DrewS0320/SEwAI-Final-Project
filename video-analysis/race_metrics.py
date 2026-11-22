
"""Derived Mario Kart coin/lap metrics from existing V4 HUD data.

This module deliberately does NOT change the performance score. Values derived
from V4 coins and video/lap transitions are estimates, not frame-exact truth.
Unresolved OCR samples remain unknown; they are never silently treated as zero.

Requires only the Python standard library. Works with existing score_input.json
and coins_v4.csv files; no video processing or Tesseract rerun is needed.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _rounded(value: float | None, digits: int = 3) -> float | None:
    return round(value, digits) if value is not None else None


def _read_coin_samples(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"video_seconds", "coins_v4", "coins_v4_source"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                f"{csv_path}: missing required columns: "
                f"{sorted(required - set(reader.fieldnames or []))}"
            )
        samples = []
        for line_num, row in enumerate(reader, 2):
            t = float(row["video_seconds"])
            raw = (row.get("coins_v4") or "").strip()
            coin = None if not raw else int(float(raw))
            if coin is not None and not 0 <= coin <= 10:
                raise ValueError(
                    f"{csv_path}:{line_num}: coin count out of range: {coin}"
                )
            samples.append({
                "video_seconds": t,
                "coins": coin,
                "source": row.get("coins_v4_source") or "unknown",
            })

    if not samples:
        raise ValueError(f"{csv_path}: no coin samples")
    if any(
        b["video_seconds"] <= a["video_seconds"]
        for a, b in zip(samples, samples[1:])
    ):
        raise ValueError(
            f"{csv_path}: video_seconds must be strictly increasing"
        )
    return samples


def _get_bounds(summary: dict[str, Any]) -> tuple[float, float]:
    bounds = summary.get("race_bounds", {})
    start = bounds.get("start_video_seconds")
    end = bounds.get("end_video_seconds")
    if start is None or end is None or float(end) <= float(start):
        raise ValueError(
            "score_input.json must contain valid race_bounds "
            "start/end video seconds"
        )
    return float(start), float(end)


def _intervals(
    samples: list[dict[str, Any]],
    start: float,
    end: float
) -> list[dict[str, Any]]:
    """Assign sample states to nearest-time cells clipped to the race."""
    intervals = []
    for i, sample in enumerate(samples):
        center = sample["video_seconds"]
        left = (
            start if i == 0
            else (samples[i - 1]["video_seconds"] + center) / 2
        )
        right = (
            end if i == len(samples) - 1
            else (center + samples[i + 1]["video_seconds"]) / 2
        )
        left, right = max(start, left), min(end, right)
        if right > left:
            intervals.append({**sample, "start": left, "end": right})
    return intervals


def _duration_by_coins(
    intervals: list[dict[str, Any]],
    start: float,
    end: float
) -> dict[str, Any]:
    distribution = {i: 0.0 for i in range(11)}
    unknown = 0.0
    longest_ten = 0.0
    longest_bounds = None
    current_ten_start = None
    current_ten_end = None

    def end_streak() -> None:
        nonlocal longest_ten, longest_bounds
        nonlocal current_ten_start, current_ten_end

        if current_ten_start is not None and current_ten_end is not None:
            length = current_ten_end - current_ten_start
            if length > longest_ten:
                longest_ten = length
                longest_bounds = [current_ten_start, current_ten_end]
        current_ten_start = current_ten_end = None

    for sample in intervals:
        left = max(start, sample["start"])
        right = min(end, sample["end"])
        if right <= left:
            continue

        coins = sample["coins"]
        if coins is None:
            unknown += right - left
        else:
            distribution[coins] += right - left

        if coins == 10:
            if (
                current_ten_start is None
                or current_ten_end is None
                or left > current_ten_end + 1e-6
            ):
                end_streak()
                current_ten_start = left
            current_ten_end = right
        else:
            end_streak()

    end_streak()

    duration = end - start
    resolved = sum(distribution.values())
    weighted_coins = sum(
        count * seconds for count, seconds in distribution.items()
    )
    first_ten = next(
        (
            s["video_seconds"]
            for s in intervals
            if s["coins"] == 10
            and start <= s["video_seconds"] <= end
        ),
        None
    )
    observed_ten = distribution[10]
    below_five = sum(distribution[i] for i in range(5))

    return {
        "window_seconds": _rounded(duration),
        "resolved_time_seconds": _rounded(resolved),
        "unresolved_time_seconds": _rounded(unknown),
        "time_coverage_fraction": (
            _rounded(resolved / duration, 4) if duration else None
        ),
        "time_weighted_average_coins": (
            _rounded(weighted_coins / resolved) if resolved else None
        ),
        "time_to_first_observed_10_coins_seconds_estimate": (
            _rounded(first_ten - start)
            if first_ten is not None else None
        ),
        "time_at_10_coins_seconds_estimate": _rounded(observed_ten),
        "fraction_of_race_at_10_coins": (
            _rounded(observed_ten / duration, 4) if duration else None
        ),
        "fraction_of_resolved_time_at_10_coins": (
            _rounded(observed_ten / resolved, 4) if resolved else None
        ),
        "time_below_5_coins_seconds_estimate": _rounded(below_five),
        "fraction_of_race_below_5_coins": (
            _rounded(below_five / duration, 4) if duration else None
        ),
        "longest_observed_10_coin_streak_seconds_estimate": (
            _rounded(longest_ten)
        ),
        "longest_observed_10_coin_streak_race_elapsed_bounds": (
            [
                _rounded(longest_bounds[0] - start),
                _rounded(longest_bounds[1] - start)
            ]
            if longest_bounds is not None else None
        ),
        "distribution_seconds": {
            str(i): _rounded(distribution[i]) for i in range(11)
        } | {"unknown": _rounded(unknown)},
        "distribution_fraction_of_race": {
            str(i): _rounded(distribution[i] / duration, 4)
            for i in range(11)
        } | {"unknown": _rounded(unknown / duration, 4)},
    }


def _split_by_lap(
    intervals: list[dict[str, Any]],
    summary: dict[str, Any],
    start: float,
    end: float
) -> list[dict[str, Any]]:
    transitions = summary.get("lap_transitions") or []
    expected_laps = len(summary.get("lap_times_seconds_approx") or [])

    if expected_laps < 1 or len(transitions) != expected_laps - 1:
        return []
    if [t.get("new_lap") for t in transitions] != list(
        range(2, expected_laps + 1)
    ):
        return []

    boundaries = [start]
    for entry in transitions:
        t = entry.get("boundary_video_seconds_estimate")
        if t is not None and start < float(t) < end:
            boundaries.append(float(t))
    boundaries.append(end)

    if (
        boundaries != sorted(set(boundaries))
        or len(boundaries) < 2
    ):
        return []

    result = []
    for i, (left, right) in enumerate(
        zip(boundaries, boundaries[1:]), 1
    ):
        histogram = _duration_by_coins(intervals, left, right)
        result.append({
            "lap": i,
            "start_video_seconds_estimate": _rounded(left),
            "end_video_seconds_estimate": _rounded(right),
            **histogram,
        })
    return result


def _coin_recovery(
    events: list[dict[str, Any]],
    intervals: list[dict[str, Any]],
    race_start: float,
    race_end: float
) -> dict[str, Any]:
    """Estimate recovery to pre-decrease count after loss candidates."""
    eligible = [
        e for e in events
        if e.get("classification") in {
            "strong_three_coin_loss_candidate",
            "possible_capped_coin_loss"
        }
    ]
    eligible.sort(
        key=lambda e: float(e["video_seconds_estimate"])
    )

    results = []
    recovered_durations = []

    for i, event in enumerate(eligible):
        time = float(event["video_seconds_estimate"])
        target = int(event["coins_before"])
        next_event = (
            float(eligible[i + 1]["video_seconds_estimate"])
            if i + 1 < len(eligible) else race_end
        )

        recovery_at = None
        unknown_seconds = 0.0

        for sample in intervals:
            if sample["end"] <= time:
                continue
            if sample["start"] >= next_event:
                break

            if sample["coins"] is None:
                unknown_seconds += max(
                    0.0,
                    min(sample["end"], next_event)
                    - max(sample["start"], time)
                )

            if (
                sample["video_seconds"] > time
                and sample["video_seconds"] < next_event
                and sample["coins"] is not None
                and sample["coins"] >= target
            ):
                recovery_at = sample["video_seconds"]
                break

        seconds = (
            recovery_at - time
            if recovery_at is not None else None
        )
        if seconds is not None:
            recovered_durations.append(seconds)

        results.append({
            "candidate_classification": event["classification"],
            "race_elapsed_seconds_estimate": _rounded(
                time - race_start
            ),
            "previous_coin_count": target,
            "recovered_previous_coin_count": (
                recovery_at is not None
            ),
            "recovery_time_seconds_estimate": _rounded(seconds),
            "unresolved_time_during_recovery_seconds": _rounded(
                unknown_seconds
            ),
            "censored_by_next_candidate": (
                recovery_at is None and next_event < race_end
            ),
            "verified_in_video": False,
        })

    return {
        "eligible_loss_candidates": len(eligible),
        "recovered_before_next_candidate": len(
            recovered_durations
        ),
        "mean_observed_recovery_time_seconds_estimate": (
            _rounded(
                sum(recovered_durations) / len(recovered_durations)
            )
            if recovered_durations else None
        ),
        "candidates_per_race_minute": _rounded(
            len(eligible) * 60 / (race_end - race_start), 3
        ),
        "events": results,
        "note": (
            "Coin decreases are unverified candidates, not confirmed "
            "hits; recovery is to the previous coin count and may "
            "have occurred earlier in unreadable intervals."
        ),
    }


def _lookup_wr(
    world_records_path: Path | None,
    track: str,
    engine_class: str
):
    if (
        world_records_path is None
        or not world_records_path.is_file()
    ):
        return None

    data = json.loads(
        world_records_path.read_text(encoding="utf-8")
    )

    for entry in data.get("tracks", []):
        if entry.get("name", "").casefold() == str(track).casefold():
            return entry.get("records", {}).get(str(engine_class))
    return None


def _lap_timing(
    summary: dict[str, Any],
    world_records_path: Path | None,
    engine_class: str
) -> dict[str, Any]:
    laps = summary.get("lap_times_seconds_approx") or []
    times = [
        float(t)
        if isinstance(t, (int, float)) and t > 0
        else None
        for t in laps
    ]

    valid = [
        (index + 1, t)
        for index, t in enumerate(times)
        if t is not None
    ]

    fastest = min(valid, key=lambda x: x[1]) if valid else None
    slowest = max(valid, key=lambda x: x[1]) if valid else None

    changes = []
    for i in range(1, len(times)):
        prev, cur = times[i - 1], times[i]
        changes.append({
            "from_lap": i,
            "to_lap": i + 1,
            "change_seconds": (
                _rounded(cur - prev)
                if prev is not None and cur is not None
                else None
            ),
            "change_percent": (
                _rounded((cur / prev - 1) * 100, 2)
                if prev is not None and cur is not None
                else None
            ),
            "improved": (
                cur < prev
                if prev is not None and cur is not None
                else None
            ),
        })

    wr = _lookup_wr(
        world_records_path,
        summary.get("track", ""),
        engine_class
    )

    wr_total = (
        float(wr["total_seconds"])
        if wr and wr.get("total_seconds") is not None
        else None
    )

    wr_splits = wr.get("lap_splits_seconds") if wr else None
    complete_splits = (
        isinstance(wr_splits, list)
        and len(wr_splits) == len(times)
        and all(
            isinstance(s, (int, float)) and s > 0
            for s in wr_splits
        )
    )
    wr_splits = (
        [float(s) for s in wr_splits]
        if complete_splits else None
    )

    cumulative_player = cumulative_wr = 0.0
    per_lap = []

    for i, lap in enumerate(times):
        wr_split = (
            wr_splits[i]
            if wr_splits is not None else None
        )
        cumulative_player = (
            cumulative_player + lap
            if cumulative_player is not None and lap is not None
            else None
        )
        cumulative_wr = (
            cumulative_wr + wr_split
            if cumulative_wr is not None and wr_split is not None
            else None
        )

        per_lap.append({
            "lap": i + 1,
            "time_seconds_estimate": _rounded(lap),
            "gap_to_fastest_lap_seconds": (
                _rounded(lap - fastest[1])
                if lap is not None and fastest else None
            ),
            "world_record_split_seconds": _rounded(wr_split),
            "gap_to_world_record_split_seconds_estimate": (
                _rounded(lap - wr_split)
                if lap is not None and wr_split is not None
                else None
            ),
            "cumulative_time_seconds_estimate": _rounded(
                cumulative_player
            ),
            "cumulative_world_record_seconds": _rounded(
                cumulative_wr
            ),
            "cumulative_gap_to_world_record_seconds_estimate": (
                _rounded(cumulative_player - cumulative_wr)
                if (
                    cumulative_player is not None
                    and cumulative_wr is not None
                )
                else None
            ),
        })

    final_time = summary.get("final_time_seconds")
    final_time = (
        float(final_time)
        if isinstance(final_time, (int, float))
        else None
    )

    return {
        "timing_source": summary.get(
            "final_time_source", "unavailable"
        ),
        "lap_splits_are_estimated": True,
        "fastest_lap": (
            {"lap": fastest[0], "seconds": _rounded(fastest[1])}
            if fastest else None
        ),
        "slowest_lap": (
            {"lap": slowest[0], "seconds": _rounded(slowest[1])}
            if slowest else None
        ),
        "lap_to_lap_changes": changes,
        "lap_2_vs_3_absolute_difference_seconds": (
            _rounded(abs(times[1] - times[2]))
            if (
                len(times) >= 3
                and times[1] is not None
                and times[2] is not None
            )
            else None
        ),
        "world_record": {
            "available": wr_total is not None,
            "engine_class": str(engine_class),
            "total_seconds": _rounded(wr_total),
            "lap_splits_available": wr_splits is not None,
            "final_time_gap_seconds_estimate": (
                _rounded(final_time - wr_total)
                if final_time is not None and wr_total is not None
                else None
            ),
            "final_time_slower_than_wr_percent": (
                _rounded((final_time / wr_total - 1) * 100, 2)
                if final_time is not None and wr_total is not None
                else None
            ),
            "source_url": (
                wr.get("source_url") if wr else None
            ),
        },
        "per_lap": per_lap,
    }


def calculate_race_metrics(
    score_input: dict[str, Any],
    csv_path: Path,
    loss_events: list[dict[str, Any]] | None = None,
    world_records_path: Path | None = None,
    engine_class: str = "150"
) -> dict[str, Any]:
    """Compute descriptive statistics without modifying scoring."""
    start, end = _get_bounds(score_input)
    samples = _read_coin_samples(Path(csv_path))
    intervals = _intervals(samples, start, end)

    coins = _duration_by_coins(intervals, start, end)
    coins["per_lap"] = _split_by_lap(
        intervals, score_input, start, end
    )
    coins["loss_candidate_recovery"] = _coin_recovery(
        loss_events or [], intervals, start, end
    )

    timeline = [
        {
            "race_elapsed_seconds": _rounded(
                s["video_seconds"] - start
            ),
            "coins": s["coins"],
            "source": s["source"],
        }
        for s in samples
        if start <= s["video_seconds"] <= end
    ]

    return {
        "schema_version": "1.0",
        "track": score_input.get("track"),
        "engine_class": str(engine_class),
        "race_window_seconds": _rounded(end - start),
        "coin_metrics": coins,
        "lap_metrics": _lap_timing(
            score_input, world_records_path, str(engine_class)
        ),
        "coin_timeline": timeline,
        "notes": [
            "Coin metrics use time-weighted V4 states. Unknown OCR "
            "intervals remain unknown rather than being set to zero.",
            "Times to 10 coins, streaks, coin recoveries and per-lap "
            "coin allocations are estimates from ~0.2 second sampling.",
            "An unknown coin reading interrupts a continuous observed "
            "10-coin streak; it may make the streak appear shorter.",
            "Lap boundaries and lap splits are estimates. Do not "
            "treat them as official game timer readings.",
            "World-record comparisons are shown only when matching "
            "record data are available.",
            "Coin-loss events are candidate detections and have "
            "not been validated against the video.",
        ],
    }
