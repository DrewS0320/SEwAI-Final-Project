
"""Add finish-time estimates, coin-loss candidates, and race metrics."""

import argparse
import csv
import json
from pathlib import Path

from race_metrics import calculate_race_metrics


DIRECT_SOURCES = {
    "v3_observed_supported",
    "v3_strong_transition_observed",
    "v3_strong_weak_guess_confirmed",
    "v3_corrected_raw",
}


def coin_loss_report(csv_path, start_time=None):
    with open(csv_path, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {
            "video_seconds",
            "coins_v4",
            "coins_v4_source"
        }

        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                "coins_v4.csv is missing required columns"
            )

        rows = [
            (
                float(r["video_seconds"]),
                int(float(r["coins_v4"]))
            )
            for r in reader
            if (
                r["coins_v4"]
                and r["coins_v4_source"] in DIRECT_SOURCES
            )
        ]

    def stable_samples(i, step):
        t, coins = rows[i]
        count = 0

        while 0 <= i < len(rows):
            other_t, other_coins = rows[i]
            if (
                abs(other_t - t) > 0.8
                or other_coins != coins
            ):
                break

            count += 1
            i += step

        return count

    events = []

    for i in range(1, len(rows)):
        t0, before = rows[i - 1]
        t1, after = rows[i]

        if after >= before:
            continue

        gap = t1 - t0

        stable = (
            stable_samples(i - 1, -1) >= 2
            and stable_samples(i, 1) >= 2
        )

        if before - after == 3 and gap <= 0.8 and stable:
            classification = "strong_three_coin_loss_candidate"

        elif (
            before < 3
            and after == 0
            and gap <= 1.0
            and stable
        ):
            classification = "possible_capped_coin_loss"

        else:
            classification = "ambiguous_decrease_review"

        timestamp = round((t0 + t1) / 2, 3)

        event = {
            "classification": classification,
            "video_seconds_estimate": timestamp,
            "video_seconds_window": [
                round(t0, 3),
                round(t1, 3)
            ],
            "coins_before": before,
            "coins_after": after,
            "verified_in_video": False,
        }

        if start_time is not None:
            event["race_elapsed_seconds_estimate"] = round(
                timestamp - start_time, 3
            )

        events.append(event)

    return {
        "strong_three_coin_loss_candidates": sum(
            e["classification"]
            == "strong_three_coin_loss_candidate"
            for e in events
        ),
        "possible_capped_coin_losses": sum(
            e["classification"]
            == "possible_capped_coin_loss"
            for e in events
        ),
        "ambiguous_decreases": sum(
            e["classification"]
            == "ambiguous_decrease_review"
            for e in events
        ),
        "verified_coin_loss_events": None,
        "events": events,
        "notes": (
            "Candidates need video review; unreadable intervals "
            "may hide other changes."
        ),
    }


def enhance_analysis(
    output_folder,
    world_records_path=None,
    engine_class="150"
):
    folder = Path(output_folder)

    score_path = folder / "score_input.json"
    summary = json.loads(
        score_path.read_text(encoding="utf-8")
    )

    bounds = json.loads(
        (folder / "race_bounds.json").read_text(
            encoding="utf-8"
        )
    )

    start = bounds.get("start_video_seconds")
    end = bounds.get("end_video_seconds")

    # Never replace the user's supplied official final time.
    if (
        summary.get("final_time_seconds") is None
        and start is not None
        and end is not None
    ):
        duration = round(float(end) - float(start), 3)

        if duration > 0:
            summary["final_time_seconds"] = duration

            summary["final_time_source"] = (
                "go_finish_video_duration_estimate"
                if bounds.get("method") == "gold_template_matching"
                else "video_bounds_duration_estimate"
            )

            laps = summary.get("lap_times_seconds_approx")

            if (
                isinstance(laps, list)
                and len(laps) == 3
                and all(
                    isinstance(n, (int, float)) and n > 0
                    for n in laps[:2]
                )
            ):
                third = round(
                    duration - laps[0] - laps[1], 3
                )

                if third > 0:
                    laps[2] = third
                    summary["lap_metrics_present"] = True

            notes = summary.setdefault("limitations", [])

            notes[:] = [
                n for n in notes
                if "Final lap timing requires the official total"
                not in n
            ]

            note = (
                "GO!/FINISH! timing is estimated from video, "
                "not the official game timer."
            )

            if note not in notes:
                notes.append(note)

    coin_path = folder / "coins_v4.csv"

    if coin_path.exists():
        report = coin_loss_report(
            coin_path,
            float(start) if start is not None else None
        )

        (folder / "coin_loss_events.json").write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8"
        )

        summary["coin_loss_detection"] = {
            "strong_candidates": report[
                "strong_three_coin_loss_candidates"
            ],
            "possible_capped_losses": report[
                "possible_capped_coin_losses"
            ],
            "ambiguous_decreases": report[
                "ambiguous_decreases"
            ],
            "verified_in_video": False,
            "events_file": "coin_loss_events.json",
        }

    # Generate descriptive statistics for the frontend.
    # This does not change the C# scoring formula.
    if coin_path.exists():

        if world_records_path is None:
            candidate = (
                Path(__file__).resolve().parent.parent
                / "backend"
                / "Data"
                / "world_records.json"
            )

            world_records_path = (
                candidate if candidate.is_file() else None
            )

        report_events = (
            report["events"]
            if "report" in locals()
            else []
        )

        derived = calculate_race_metrics(
            summary,
            coin_path,
            report_events,
            (
                Path(world_records_path)
                if world_records_path else None
            ),
            str(engine_class),
        )

        (folder / "race_metrics.json").write_text(
            json.dumps(derived, indent=2) + "\n",
            encoding="utf-8"
        )

        # Include lightweight metrics in score_input.json,
        # but avoid duplicating the entire coin timeline.
        summary["race_metrics"] = {
            k: v
            for k, v in derived.items()
            if k != "coin_timeline"
        }

        summary["race_metrics_file"] = "race_metrics.json"

    score_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8"
    )

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "results_folder",
        type=Path
    )

    parser.add_argument(
        "--world-records",
        type=Path,
        help="Path to backend/Data/world_records.json"
    )

    parser.add_argument(
        "--engine-class",
        choices=("150", "200"),
        default="150"
    )

    args = parser.parse_args()

    result = enhance_analysis(
        args.results_folder,
        args.world_records,
        args.engine_class
    )

    print(
        "Final race time:",
        result.get("final_time_seconds")
    )

    print(
        "Time source:",
        result.get("final_time_source")
    )

    print(
        "Lap times:",
        result.get("lap_times_seconds_approx")
    )

    print(
        "Coin-loss candidates:",
        result.get("coin_loss_detection")
    )

    if "race_metrics" in result:
        print(
            "New metrics:",
            str(args.results_folder / "race_metrics.json")
        )

        print(
            "Coin coverage:",
            result["race_metrics"]["coin_metrics"][
                "time_coverage_fraction"
            ]
        )
