"""Public-only EXP-020 notebook RNG and authoritative progress regression tests."""
from __future__ import annotations

import importlib.util
import json
import random
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from public_policy_rng import policy_rng_seed
from compare_real_public_probes import compare


def load_probe():
    fake_arc_agi = types.ModuleType("arc_agi")
    fake_arc_agi.Arcade = object
    fake_arc_agi.OperationMode = object
    fake_arcengine = types.ModuleType("arcengine")
    fake_arcengine.FrameData = object
    fake_arcengine.GameAction = types.SimpleNamespace(RESET=object())
    spec = importlib.util.spec_from_file_location(
        "_public_probe_rng_test", SCRIPTS / "kaggle_exp005_public_probe.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"arc_agi": fake_arc_agi, "arcengine": fake_arcengine}):
        spec.loader.exec_module(module)
    return module


def probe_document(game="public-fixture", *, seed=None, levels=0,
                   level_action=None, calls=10, wallclock=11.5):
    trace = [
        {"levels_completed": int(levels if level_action == action else 0)}
        for action in range(1, 4)
    ]
    if level_action is not None:
        for idx, record in enumerate(trace, 1):
            record["levels_completed"] = levels if idx >= level_action else 0
    return {
        "model": "fixture-not-a-real-Qwen-run",
        "probe_complete": True,
        "completed_games": 1,
        "probe_protocol": {
            "controller_seed": seed, "environment_seed": 0,
            "official_submission": False, "verified_progress": "levels_completed",
        },
        "results": [{
            "game": game, "actions": 3, "levels_completed": levels,
            "max_levels_completed": levels, "model_calls": calls,
            "elapsed_seconds": wallclock,
            "action_trace": trace,
            "controller_seed": seed, "environment_seed": 0,
            "level_completion_actions": (
                [{"level": levels, "after_action": level_action}]
                if levels and level_action else []
            ),
        }],
    }


class PublicRngTests(unittest.TestCase):
    def test_probe_seed_matches_existing_independent_evaluation(self):
        probe = load_probe()
        for game in ("fixture-a", "fixture-b"):
            for seed in (0, 1, 101, 2026):
                self.assertEqual(
                    probe._public_controller_seed(game, seed),
                    policy_rng_seed(game, seed),
                )
        self.assertNotEqual(
            probe._public_controller_seed("fixture-a", 1),
            probe._public_controller_seed("fixture-a", 2),
        )
        for invalid in (False, True, -1, "2", 1.2):
            with self.assertRaises(ValueError):
                probe._public_controller_seed("fixture", invalid)

    def test_rng_override_changes_probe_only(self):
        probe = load_probe()
        a = types.SimpleNamespace(_explorer=types.SimpleNamespace(_rng=random.Random(4)))
        b = types.SimpleNamespace(_explorer=types.SimpleNamespace(_rng=random.Random(4)))
        c = types.SimpleNamespace(_explorer=types.SimpleNamespace(_rng=random.Random(4)))
        probe._seed_public_explorer(a, "fixture", 101)
        probe._seed_public_explorer(b, "fixture", 101)
        probe._seed_public_explorer(c, "fixture", 202)
        self.assertEqual([a._explorer._rng.random() for _ in range(5)],
                         [b._explorer._rng.random() for _ in range(5)])
        self.assertNotEqual(a._explorer._rng.random(), c._explorer._rng.random())
        unmodified = random.Random(4)
        probe._seed_public_explorer(c, "fixture", None)
        d = types.SimpleNamespace(_explorer=types.SimpleNamespace(_rng=random.Random(4)))
        probe._seed_public_explorer(d, "fixture", None)
        self.assertEqual(d._explorer._rng.random(), unmodified.random())
        with self.assertRaisesRegex(RuntimeError, "seedable RNG"):
            probe._seed_public_explorer(types.SimpleNamespace(), "fixture", 1)

    def test_only_authoritative_completed_levels_generate_milestones(self):
        probe = load_probe()
        self.assertEqual(probe._completion_events(0, 0, 15), [])
        self.assertEqual(probe._completion_events(2, 0, 16), [])
        self.assertEqual(
            probe._completion_events(0, 2, 21),
            [{"level": 1, "after_action": 21},
             {"level": 2, "after_action": 21}],
        )
        for args in ((0, 1, 0), (False, 1, 1), (1, -1, 1)):
            with self.assertRaises(ValueError):
                probe._completion_events(*args)

    def test_kaggle_builder_pins_offline_model_and_probe_seed(self):
        import build_kaggle_exp005_notebook as module
        label = "EXP-020"
        slug = "arc-agi-3-exp-020-persistent-reasoning-policy"
        notebook, metadata = module.build_artifacts(
            agent_source="VALUE = 1\n", username="fixture-user",
            kernel_slug=slug, experiment_label=label, probe_controller_seed=101,
        )
        src = notebook["cells"][1]["source"]
        self.assertIn("controller_seed=101", src)
        self.assertIn("run_public_probe(", src)
        self.assertFalse(metadata["enable_internet"])
        self.assertEqual(metadata["machine_shape"], "NvidiaRtxPro6000")
        self.assertIn("sha256:", metadata["docker_image"])
        self.assertEqual(metadata["model_sources"], [module.base.MODEL_SOURCE])
        with self.assertRaisesRegex(ValueError, "controller seed"):
            module.build_artifacts(
                agent_source="VALUE = 1\n", username="fixture-user",
                kernel_slug=slug, experiment_label=label, probe_controller_seed=-1,
            )


class RealProbeCompareTests(unittest.TestCase):
    def compare_documents(self, before, after):
        with tempfile.TemporaryDirectory() as folder:
            old = Path(folder) / "old.json"
            new = Path(folder) / "new.json"
            old.write_text(json.dumps(before), encoding="utf-8")
            new.write_text(json.dumps(after), encoding="utf-8")
            return compare(old, new)

    def test_confirmed_level_actions_not_pixel_changes(self):
        before = probe_document(levels=1, level_action=3, calls=5, wallclock=20)
        after = probe_document(levels=1, level_action=2, calls=4, wallclock=15)
        after["results"][0]["action_trace"][0]["changed_cells"] = 4096
        compared = self.compare_documents(before, after)
        self.assertEqual(compared["baseline_levels"], 1)
        self.assertEqual(compared["candidate_levels"], 1)
        self.assertEqual(
            compared["public_games"][0]["paired_first_completion_action_delta"], -1
        )
        self.assertEqual(compared["model_call_reduction_percent"], 20)
        self.assertNotIn("action_trace", json.dumps(compared))
        self.assertNotIn("changed_cells", json.dumps(compared))

    def test_different_controller_seed_cannot_be_paired(self):
        old = probe_document(seed=101)
        new = probe_document(seed=102)
        with self.assertRaisesRegex(ValueError, "unpaired"):
            self.compare_documents(old, new)

    def test_seeded_game_metadata_must_match_protocol(self):
        before = probe_document(seed=101)
        after = probe_document(seed=101)
        after["results"][0]["controller_seed"] = 102
        with self.assertRaisesRegex(ValueError, "game controller seed"):
            self.compare_documents(before, after)
        after["results"][0]["controller_seed"] = 101
        after["results"][0]["environment_seed"] = 1
        with self.assertRaisesRegex(ValueError, "game environment seed"):
            self.compare_documents(before, after)
        del after["results"][0]["environment_seed"]
        with self.assertRaisesRegex(ValueError, "missing game environment seed"):
            self.compare_documents(before, after)

    def test_incomplete_and_inconsistent_probes_rejected(self):
        old = probe_document(levels=1, level_action=2)
        new = probe_document(levels=1, level_action=2)
        old["probe_complete"] = False
        with self.assertRaisesRegex(ValueError, "fully completed"):
            self.compare_documents(old, new)
        old["probe_complete"] = True
        new["results"][0]["max_levels_completed"] = 0
        with self.assertRaisesRegex(ValueError, "disagree"):
            self.compare_documents(old, new)


if __name__ == "__main__":
    unittest.main()
