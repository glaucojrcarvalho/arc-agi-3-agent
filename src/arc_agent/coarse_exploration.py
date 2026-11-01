"""Geometry-aware exploration key; never a score or level-progress signal."""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
from typing import Sequence

Frame = Sequence[Sequence[Sequence[int]]]


def coarse_state_key(frame: Frame, *, bins: int = 4, quantum: int = 8) -> str:
    """Coarsen settled-frame foreground occupancy plus a global color histogram."""
    if isinstance(bins, bool) or not isinstance(bins, int) or not 1 <= bins <= 8:
        raise ValueError("bins must be integer 1..8")
    if isinstance(quantum, bool) or not isinstance(quantum, int) or not 2 <= quantum <= 32:
        raise ValueError("quantum must be integer 2..32")
    if not frame or not frame[-1] or not frame[-1][0]:
        return sha256(f"empty:{bins}:{quantum}".encode("ascii")).hexdigest()
    board = frame[-1]
    height, width = len(board), len(board[0])
    if any(len(row) != width for row in board):
        raise ValueError("non-rectangular frame")
    palette = Counter(int(value) for row in board for value in row)
    background = min(palette, key=lambda color: (-palette[color], color))
    total = width * height
    colors = tuple(sorted((color, (count * quantum * 2 + total) // (2 * total))
                          for color, count in palette.items()
                          if count * quantum >= total // 2))
    occupancy = []
    for by in range(bins):
        y0, y1 = height * by // bins, height * (by + 1) // bins
        for bx in range(bins):
            x0, x1 = width * bx // bins, width * (bx + 1) // bins
            size = (y1 - y0) * (x1 - x0)
            if not size:
                occupancy.append(-1)
                continue
            foreground = sum(int(board[y][x]) != background
                             for y in range(y0, y1) for x in range(x0, x1))
            occupancy.append((2 * foreground * quantum + size) // (2 * size))
    signature = (height, width, bins, quantum, background, colors, tuple(occupancy))
    return sha256(repr(signature).encode("ascii")).hexdigest()
