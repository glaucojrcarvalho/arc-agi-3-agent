from __future__ import annotations

import unittest

from arc_agent.state import diff_frames, frame_fingerprint


class StateTests(unittest.TestCase):
    def test_identical_frames_have_no_changes(self) -> None:
        frame = [[[0, 1], [2, 3]]]
        delta = diff_frames(frame, frame)

        self.assertEqual(delta.changed_cells, 0)
        self.assertTrue(delta.is_noop)
        self.assertEqual(delta.change_ratio, 0.0)

    def test_detects_changed_cell(self) -> None:
        before = [[[0, 1], [2, 3]]]
        after = [[[0, 1], [9, 3]]]

        delta = diff_frames(before, after)

        self.assertEqual(delta.changed_cells, 1)
        self.assertEqual(delta.changes[0].coordinate, (0, 1, 0))
        self.assertEqual(delta.changes[0].before, 2)
        self.assertEqual(delta.changes[0].after, 9)
        self.assertEqual(delta.change_ratio, 0.25)

    def test_shape_changes_are_counted(self) -> None:
        before = [[[1]]]
        after = [[[1, 2]]]

        delta = diff_frames(before, after)

        self.assertEqual(delta.changed_cells, 1)
        self.assertEqual(delta.changes[0].before, None)
        self.assertEqual(delta.changes[0].after, 2)

    def test_fingerprint_is_deterministic_and_content_sensitive(self) -> None:
        first = [[[0, 1], [2, 3]]]
        same = [[[0, 1], [2, 3]]]
        different = [[[0, 1], [2, 4]]]

        self.assertEqual(frame_fingerprint(first), frame_fingerprint(same))
        self.assertNotEqual(frame_fingerprint(first), frame_fingerprint(different))


if __name__ == "__main__":
    unittest.main()
