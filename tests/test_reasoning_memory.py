from __future__ import annotations

import json
import unittest

from arc_agent.reasoning_memory import ReasoningMemory


class ReasoningMemoryTests(unittest.TestCase):
    def test_persists_belief_and_valid_keyboard_plan(self):
        memory=ReasoningMemory()
        memory.observe(level=0,state="NOT_FINISHED",latest_transition=None)
        reply=json.dumps({
            "action":1,"data":{},"reason":"try movement",
            "goal":"get to the exit",
            "hypothesis":"action two moves object to the right",
            "next_actions":[{"action":2,"data":{}},
                            {"action":6,"data":{"x":1,"y":1}},
                            {"action":999,"data":{}},
                            {"action":3,"data":{}}]
        })
        memory.absorb(reply,legal_actions=[1,2,3,6],complex_action_ids={6},width=4,height=4)
        state=memory.prompt_context()
        self.assertEqual(state["unverified_goal_hypothesis"],"get to the exit")
        self.assertEqual(state["unverified_dynamics_hypothesis"],"action two moves object to the right")
        self.assertEqual(state["remaining_planned_keyboard_actions"],[{"action":2,"data":{}}])
        self.assertEqual(memory.take_plan(legal_actions=[1,2]),(2,{}))
        self.assertIsNone(memory.take_plan(legal_actions=[1,2]))

    def test_plan_consumption_and_progress_flush(self):
        mem=ReasoningMemory()
        mem.observe(level=0,state="NOT_FINISHED",latest_transition=None)
        response=json.dumps({"goal":"move","hypothesis":"keyboard control", "next_actions":[{"action":1,"data":{}},{"action":2,"data":{}}]})
        mem.absorb(response,legal_actions=[1,2],complex_action_ids=set(),width=4,height=4)
        mem.observe(level=0,state="NOT_FINISHED",latest_transition={
            "changed_cells":4,"levels_delta":0,"state_changed":False,"proven_noop":False
        })
        self.assertEqual(mem.take_plan(legal_actions=[1,2]),(1,{}))
        mem.observe(level=1,state="NOT_FINISHED",latest_transition={"levels_delta":1})
        self.assertIsNone(mem.take_plan(legal_actions=[1,2]))
        self.assertEqual(mem.goal,"")
        self.assertEqual(mem.steps_without_progress,0)

    def test_stagnation_retains_belief_but_discards_future_plan(self):
        m=ReasoningMemory(max_stagnation=2)
        m.observe(level=0,state="NOT_FINISHED",latest_transition=None)
        m.absorb('{"goal":"find the goal","next_actions":[{"action":1,"data":{}}]}',
                 legal_actions=[1],complex_action_ids=set(),width=1,height=1)
        delta={"changed_cells":1,"levels_delta":0,"state_changed":False,"proven_noop":False}
        m.observe(level=0,state="NOT_FINISHED",latest_transition=delta)
        self.assertFalse(m.prompt_context()["stagnation_warning"])
        m.observe(level=0,state="NOT_FINISHED",latest_transition=delta)
        self.assertTrue(m.prompt_context()["stagnation_warning"])
        self.assertEqual(m.stagnation_events,1)
        self.assertEqual(m.goal,"find the goal")
        self.assertIsNone(m.take_plan(legal_actions=[1]))

    def test_verified_noop_interrupts_plan(self):
        m=ReasoningMemory()
        m.observe(level=0,state="NOT_FINISHED",latest_transition=None)
        m.absorb('{"next_actions":[{"action":1,"data":{}}]}',
                 legal_actions=[1],complex_action_ids=set(),width=1,height=1)
        m.observe(level=0,state="NOT_FINISHED",latest_transition={
            "changed_cells":0,"levels_delta":0,"state_changed":False,"proven_noop":True
        })
        self.assertEqual(m.plan_interruptions,1)
        self.assertIsNone(m.take_plan(legal_actions=[1]))

    def test_restricts_untrusted_model_text_and_invalid_json(self):
        m=ReasoningMemory()
        m.absorb('{"goal":"'+("x"*500)+'","hypothesis":123}',
                 legal_actions=[1],complex_action_ids=set(),width=1,height=1)
        self.assertEqual(len(m.goal),200)
        self.assertEqual(m.hypothesis,"")
        m.absorb("malformed",legal_actions=[1],complex_action_ids=set(),width=1,height=1)
        self.assertEqual(len(m.goal),200)
        m.on_reset()
        self.assertEqual(m.steps_without_progress,0)

    def test_invalid_bounds(self):
        with self.assertRaises(ValueError):
            ReasoningMemory(max_planned_actions=5)
        with self.assertRaises(ValueError):
            ReasoningMemory(max_stagnation=0)


if __name__=="__main__":
    unittest.main()
