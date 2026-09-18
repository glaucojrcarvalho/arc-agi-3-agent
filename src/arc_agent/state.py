"""State comparison utilities independent from the ARC runtime package."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Sequence

Frame = Sequence[Sequence[Sequence[int]]]
Coordinate = tuple[int, int, int]


@dataclass(frozen=True)
class CellChange:
    """One changed coordinate between two observations."""

    coordinate: Coordinate
    before: int | None
    after: int | None


@dataclass(frozen=True)
class StateDelta:
    """Compact summary of a frame-to-frame transition."""

    changes: tuple[CellChange, ...]
    before_cell_count: int
    after_cell_count: int

    @property
    def changed_cells(self) -> int:
        return len(self.changes)

    @property
    def change_ratio(self) -> float:
        denominator = max(self.before_cell_count, self.after_cell_count, 1)
        return self.changed_cells / denominator

    @property
    def is_noop(self) -> bool:
        return not self.changes


def _cells(frame: Frame) -> dict[Coordinate, int]:
    cells: dict[Coordinate, int] = {}
    for layer_index, layer in enumerate(frame):
        for row_index, row in enumerate(layer):
            for column_index, value in enumerate(row):
                cells[(layer_index, row_index, column_index)] = int(value)
    return cells


def frame_fingerprint(frame: Frame) -> str:
    """Return a deterministic content fingerprint for an observation frame."""
    digest = sha256()
    for coordinate, value in sorted(_cells(frame).items()):
        layer, row, column = coordinate
        digest.update(f"{layer}:{row}:{column}:{value};".encode("utf-8"))
    return digest.hexdigest()


def diff_frames(before: Frame, after: Frame) -> StateDelta:
    """Compare two frames, including shape changes, without external dependencies."""
    before_cells = _cells(before)
    after_cells = _cells(after)

    changes: list[CellChange] = []
    for coordinate in sorted(before_cells.keys() | after_cells.keys()):
        old_value = before_cells.get(coordinate)
        new_value = after_cells.get(coordinate)
        if old_value != new_value:
            changes.append(
                CellChange(
                    coordinate=coordinate,
                    before=old_value,
                    after=new_value,
                )
            )

    return StateDelta(
        changes=tuple(changes),
        before_cell_count=len(before_cells),
        after_cell_count=len(after_cells),
    )
