"""Lossless symbolic ARC frames plus generic connected-component click proposals.

These helpers operate only on current observations; no game-specific rules,
training data or private game knowledge. Coordinates are pixel-based (x, y).
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any

from .state import Frame

_HEX = "0123456789abcdef"


def symbol_grid(frame: Frame) -> dict[str, Any]:
    """Losslessly express ARC color indices as aligned text rows.

    Official ARC frames use color indices 0..15. For out-of-range values,
    use fixed-width signed decimal columns rather than silently truncating.
    """
    colors = [int(v) for layer in frame for row in layer for v in row]
    hex_mode = all(0 <= v < 16 for v in colors)
    token_width = 1 if hex_mode else max(2, *(len(str(v)) for v in colors))
    layers = []
    for index, layer in enumerate(frame):
        rows = []
        for y, row in enumerate(layer):
            encoded = (
                "".join(_HEX[int(v)] for v in row)
                if hex_mode
                else " ".join(f"{int(v):{token_width}d}" for v in row)
            )
            rows.append(f"{y:02d}|{encoded}")
        layers.append({
            "layer": index,
            "width": len(layer[0]) if layer else 0,
            "height": len(layer),
            "rows": rows,
        })
    return {
        "encoding": (
            "hexadecimal_color_indices_0_to_f; each row y|pixels at x=0..W-1"
            if hex_mode
            else "signed_decimal_color_indices; each row y|space_separated_pixels_at_x=0..W-1"
        ),
        "layers": layers,
        "palette_counts": {
            str(color): count for color, count in sorted(Counter(colors).items())
        },
    }


def salient_click_targets(
    frame: Frame,
    *,
    max_targets: int = 24,
    max_per_color: int = 4,
) -> list[dict[str, int]]:
    """Propose pixel locations inside distinct colored connected regions.

    Favor rare visible colors, but keep multiple colors represented.
    Only four-neighbor connected components are used. Targets are *hints*,
    not claims that a pixel is interactive or that clicking it makes progress.
    """
    if max_targets < 1 or max_per_color < 1:
        raise ValueError("target limits must be positive")
    by_color: dict[int, list[dict[str, int]]] = {}
    counts: Counter[int] = Counter(
        int(v) for layer in frame for row in layer for v in row
    )
    for layer_index, layer in enumerate(frame):
        if not layer:
            continue
        height = min(len(layer), 64)
        width = min(min(len(row) for row in layer[:height]), 64)
        if width <= 0:
            continue
        visited = [[False] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                if visited[y][x]:
                    continue
                color = int(layer[y][x])
                visited[y][x] = True
                pending = deque([(x, y)])
                cells: list[tuple[int, int]] = []
                while pending:
                    cx, cy = pending.popleft()
                    cells.append((cx, cy))
                    for nx, ny in ((cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)):
                        if (
                            0 <= nx < width
                            and 0 <= ny < height
                            and not visited[ny][nx]
                            and int(layer[ny][nx]) == color
                        ):
                            visited[ny][nx] = True
                            pending.append((nx, ny))
                if len(cells) > width * height // 3:
                    # Very large background surfaces have little click specificity.
                    continue
                mx = sum(x1 for x1, _ in cells) / len(cells)
                my = sum(y1 for _, y1 in cells) / len(cells)
                rx, ry = min(
                    cells, key=lambda p: ((p[0]-mx)**2 + (p[1]-my)**2, p[1], p[0])
                )
                by_color.setdefault(color, []).append({
                    "x": rx,
                    "y": ry,
                    "layer": layer_index,
                    "color": color,
                    "pixels": len(cells),
                    "left": min(c[0] for c in cells),
                    "top": min(c[1] for c in cells),
                    "right": max(c[0] for c in cells),
                    "bottom": max(c[1] for c in cells),
                })
    for items in by_color.values():
        items.sort(key=lambda item: (-item["pixels"], item["y"], item["x"]))
    colors = sorted(by_color, key=lambda color: (counts[color], color))
    result: list[dict[str, int]] = []
    used: set[tuple[int, int]] = set()
    for rank in range(max_per_color):
        for color in colors:
            items = by_color[color]
            if rank >= len(items):
                continue
            item = items[rank]
            point = item["x"], item["y"]
            if point not in used:
                used.add(point)
                result.append(item)
                if len(result) >= max_targets:
                    return result
    return result



def bounded_animation_observation(
    frame: Frame, *, max_unique_frames: int = 4, max_runs: int = 48,
) -> dict[str, Any]:
    """Bound model context for an ARC response containing animation frames.

    The first dimension is an *animation sequence*, not image layers. Encode
    its full ordered sequence losslessly when it uses few distinct frames and
    transitions. Otherwise sample at most four keyframes, including the final
    settled observation, and explicitly report omitted frames. Never infer
    progress from animation alone.
    """
    if max_unique_frames < 2 or max_runs < 1:
        raise ValueError("invalid animation representation limits")
    if not frame:
        return {
            "encoding": "empty_animation", "animation_frame_count": 0,
            "settled_frame_index": None, "frames": [],
        }

    palette: list[Any] = []
    indices: dict[tuple[tuple[int, ...], ...], int] = {}
    runs: list[dict[str, int]] = []
    overflow = False
    for layer in frame:
        key = tuple(tuple(int(pixel) for pixel in row) for row in layer)
        frame_id = indices.get(key)
        if frame_id is None:
            if len(palette) >= max_unique_frames:
                overflow = True
                break
            frame_id = len(palette)
            indices[key] = frame_id
            palette.append(layer)
        if runs and runs[-1]["frame_id"] == frame_id:
            runs[-1]["count"] += 1
        else:
            runs.append({"frame_id": frame_id, "count": 1})
            if len(runs) > max_runs:
                overflow = True
                break

    if not overflow:
        encoded = symbol_grid(palette)
        return {
            "encoding": "lossless_animation_frame_dictionary",
            "grid_encoding": encoded["encoding"],
            "animation_frame_count": len(frame),
            "unique_frames": encoded["layers"],
            "frame_runs": runs,
            "settled_frame_id": runs[-1]["frame_id"],
            "palette_counts": encoded["palette_counts"],
        }

    end = len(frame) - 1
    selected = sorted(set((0, end // 3, (2 * end) // 3, end)))
    encoded = symbol_grid([frame[index] for index in selected])
    selected_frames = []
    for frame_index, item in zip(selected, encoded["layers"]):
        item["original_frame_index"] = frame_index
        selected_frames.append(item)
    return {
        "encoding": "sampled_animation_keyframes",
        "grid_encoding": encoded["encoding"],
        "animation_frame_count": len(frame),
        "sampled_frames": selected_frames,
        "omitted_frame_count": len(frame) - len(selected),
        "settled_frame_index": end,
        "palette_counts": encoded["palette_counts"],
    }
