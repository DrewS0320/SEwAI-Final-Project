"""Conservative, calibrated backup reading for SNES Rainbow Road's lap numeral.

The normal HUD classifier remains primary. This fallback uses the known
1920x1080 capture layout (scaled proportionally for 16:9 footage) and
binary templates of the visible lap numerator from a verified recording.
A poor or ambiguous match returns None rather than guessing.
"""

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

# Full lap numerator, including wider digits 2 and 3 (not the '/3' suffix).
_REFERENCE_WIDTH = 1920
_REFERENCE_HEIGHT = 1080
_BOX = (331, 956, 376, 1014)  # x0, y0, x1, y1
_TEMPLATE_SIZE = (_BOX[2] - _BOX[0], _BOX[3] - _BOX[1])
_TEMPLATE_DIR = Path(__file__).resolve().parent / 'templates'


@lru_cache(maxsize=1)
def _references() -> dict[int, np.ndarray]:
    loaded: dict[int, np.ndarray] = {}
    for lap in (1, 2, 3):
        template = cv2.imread(
            str(_TEMPLATE_DIR / f'lap_fallback_{lap}.png'),
            cv2.IMREAD_GRAYSCALE,
        )
        if template is None or template.shape != (_TEMPLATE_SIZE[1], _TEMPLATE_SIZE[0]):
            return {}
        loaded[lap] = (template >= 128).astype(np.uint8)
    return loaded


def classify_lap_digit(frame: np.ndarray) -> int | None:
    """Return a verified 1/2/3 only for a close, unambiguous template match."""
    if frame is None or frame.ndim != 3:
        return None
    height, width = frame.shape[:2]
    if width < 640 or height < 360 or abs(width / height - 16 / 9) > 0.025:
        return None
    refs = _references()
    if not refs:
        return None
    x0, y0, x1, y1 = _BOX
    sx, sy = width / _REFERENCE_WIDTH, height / _REFERENCE_HEIGHT
    frame_crop = frame[
        round(y0 * sy):round(y1 * sy),
        round(x0 * sx):round(x1 * sx),
    ]
    if frame_crop.size == 0:
        return None
    frame_crop = cv2.resize(frame_crop, _TEMPLATE_SIZE, interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(frame_crop, cv2.COLOR_BGR2HSV)
    white_pixels = cv2.inRange(hsv, (0, 0, 155), (179, 110, 255))
    observed = (white_pixels >= 128).astype(np.uint8)
    scores = sorted(
        (float(np.mean((observed.astype(np.float32) - reference.astype(np.float32)) ** 2)), lap)
        for lap, reference in refs.items()
    )
    (best_error, best_lap), (runner_up_error, _) = scores[:2]
    # Reject missing digits, overlays, different layouts, and weak/near-tie matches.
    if best_error > 0.065 or runner_up_error - best_error < 0.035:
        return None
    return best_lap
