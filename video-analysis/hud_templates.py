
"""Mario Kart 8 Deluxe coin and lap template reader."""

from pathlib import Path
from functools import lru_cache

import cv2
import numpy as np


TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

COIN_NAMES = {
    **{
        i: f"{i}_coins_zoomed.png"
        for i in (0, 2, 3, 4, 5, 6, 7, 8, 9)
    },
    1: "1_coin_zoomed.png",
    10: "10_coins_zoomed.png",
}

LAP_NAMES = {
    i: f"lap_{i}_zoomed.png"
    for i in (1, 2, 3)
}


def foreground(image, kind):
    """Extract bright white or orange HUD digits."""

    if image is None or image.size == 0:
        return None, False

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    white = (v > 160) & (s < 115)
    gold = (
        (v > 130)
        & (s > 90)
        & (h >= 4)
        & (h <= 38)
    )

    use_gold = (
        kind == "coins"
        and np.count_nonzero(white) < 0.026 * white.size
    )

    mask = (
        gold if use_gold else white
    ).astype(np.uint8) * 255

    height, width = mask.shape

    # Remove likely edge/background artifacts.
    mask[:round(0.065 * height)] = 0
    mask[round(0.90 * height):] = 0
    mask[:, :round(0.025 * width)] = 0
    mask[:, round(0.98 * width):] = 0

    count, labels, stats, centers = (
        cv2.connectedComponentsWithStats(mask, 8)
    )

    clean = np.zeros_like(mask)

    for k in range(1, count):
        area = stats[k, cv2.CC_STAT_AREA]

        if (
            area >= max(5, round(mask.size * 0.003))
            and 0.06 * height < centers[k, 1] < 0.90 * height
        ):
            clean[labels == k] = 255

    ys, xs = np.where(clean != 0)

    if len(xs) < 20:
        return None, use_gold

    shape = clean[
        ys.min():ys.max() + 1,
        xs.min():xs.max() + 1
    ]

    canvas_w, canvas_h = (
        (128, 64) if kind == "coins" else (64, 64)
    )

    scale = min(
        (canvas_w - 8) / shape.shape[1],
        (canvas_h - 8) / shape.shape[0],
    )

    sw = max(1, round(shape.shape[1] * scale))
    sh = max(1, round(shape.shape[0] * scale))

    smaller = cv2.resize(
        shape,
        (sw, sh),
        interpolation=cv2.INTER_NEAREST,
    )

    canvas = np.zeros(
        (canvas_h, canvas_w),
        dtype=np.uint8,
    )

    ox = (canvas_w - sw) // 2
    oy = (canvas_h - sh) // 2

    canvas[oy:oy + sh, ox:ox + sw] = smaller

    normalized = cv2.GaussianBlur(
        canvas, (3, 3), 0
    ).astype(np.float32) / 255.0

    return normalized, use_gold


@lru_cache(maxsize=2)
def templates(kind):
    """Load reference templates once, then reuse them."""

    names = (
        COIN_NAMES if kind == "coins"
        else LAP_NAMES
    )

    result = {}

    for value, filename in names.items():
        path = TEMPLATE_DIR / filename
        image = cv2.imread(str(path))

        if image is None:
            raise FileNotFoundError(
                f"Missing template image: {path}"
            )

        mask, is_gold = foreground(image, kind)

        if mask is None:
            raise ValueError(
                f"Could not extract digits from {path}"
            )

        result[value] = (mask, is_gold)

    return result


def classify(crop, kind):
    """
    Recognize a coin count or lap number.

    Returns:
        (value, diagnostic_string)

    Unknown or ambiguous readings return None.
    """

    if kind not in ("coins", "lap"):
        raise ValueError(
            "Template classification supports coins and lap"
        )

    mask, gold = foreground(crop, kind)

    if mask is None:
        return None, "template:no_foreground"

    # --------------------------------------------------------
    # LAP RECOGNITION
    # --------------------------------------------------------

    if kind == "lap":
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        _, saturation, brightness = cv2.split(hsv)

        bright = (
            (brightness > 160)
            & (saturation < 115)
        )

        height, width = bright.shape

        upper = bright[
            round(0.20 * height):round(0.53 * height),
            :
        ].copy()

        upper[:, :round(0.08 * width)] = False

        ys, xs = np.where(upper)

        if len(xs) >= 15:
            span = (
                np.percentile(xs, 90)
                - np.percentile(xs, 10)
            ) / width

            # Digit 1 is much narrower than 2 and 3.
            if span < 0.24:
                return 1, (
                    f"shape:lap1 width={span:.3f}"
                )

            # Digits 2 and 3 differ in their lower segments.
            if span > 0.29:
                lower = bright[
                    round(0.55 * height):round(0.78 * height)
                ]

                left = lower[
                    :,
                    round(0.18 * width):round(0.48 * width)
                ].mean()

                right = lower[
                    :,
                    round(0.60 * width):round(0.90 * width)
                ].mean()

                if left - right > 0.13:
                    return 2, (
                        f"shape:lap2 left={left:.2f} "
                        f"right={right:.2f}"
                    )

                if right - left > 0.13:
                    return 3, (
                        f"shape:lap3 left={left:.2f} "
                        f"right={right:.2f}"
                    )

    # --------------------------------------------------------
    # TEMPLATE MATCHING
    # --------------------------------------------------------

    references = templates(kind)

    if kind == "coins":

        # 10 coins is displayed with orange/gold digits.
        if gold:
            allowed = {10}

        else:
            allowed = set(range(10))

            # Segment-based checks help distinguish
            # 00 from 08 and similar-looking values.
            middle = float(
                mask[27:37, 82:108].mean()
            )

            left = float(
                mask[12:25, 74:84].mean()
            )

            top = float(
                mask[4:14, 82:108].mean()
            )

            if middle < 0.29:
                allowed &= {0, 1, 7}

                if left >= 0.16:
                    allowed &= {0}
                elif top >= 0.39:
                    allowed &= {7}
                else:
                    allowed &= {1}

            elif middle > 0.44:
                allowed -= {0, 1, 7}

    else:
        allowed = {1, 2, 3}

    norm = np.linalg.norm(mask) + 1e-8
    scored = []

    for label in allowed:
        reference, _ = references[label]

        similarity = float(
            np.sum(mask * reference)
            / (
                norm
                * (np.linalg.norm(reference) + 1e-8)
            )
        )

        scored.append((label, similarity))

    if not scored:
        return None, "template:no_candidate"

    scored.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    winner, confidence = scored[0]

    second = (
        scored[1][1]
        if len(scored) > 1
        else 0.0
    )

    minimum = (
        0.55 if kind == "coins"
        else 0.50
    )

    margin = confidence - second

    # Reject weak or ambiguous matches.
    if (
        confidence < minimum
        or (
            len(scored) > 1
            and margin < 0.025
        )
    ):
        return None, (
            f"template:uncertain best={winner} "
            f"sim={confidence:.3f} "
            f"gap={margin:.3f}"
        )

    return winner, (
        f"template:{winner} "
        f"sim={confidence:.3f} "
        f"gap={margin:.3f}"
    )


if __name__ == "__main__":
    # Test the reader against all 14 reference images.
    for kind, names in (
        ("coins", COIN_NAMES),
        ("lap", LAP_NAMES),
    ):
        for expected, filename in sorted(names.items()):
            image = cv2.imread(
                str(TEMPLATE_DIR / filename)
            )

            observed, details = classify(image, kind)

            print(
                f"{kind:5} "
                f"expected={expected:2} "
                f"observed={str(observed):>4} "
                f"{details}"
            )
