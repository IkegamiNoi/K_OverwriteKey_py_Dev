import unittest

from keyseq.application.app_state import AppState
from keyseq.application.call_chain import chain_from, chain_top
from keyseq.domain.sequence_control import MAX_CALL_DEPTH


def call(key):
    return {"type": "system", "op": "call", "target": key}


class CallChainTest(unittest.TestCase):
    def setUp(self):
        self.state = AppState()
        self.triggers = {}

    def register(self, key, action):
        self.triggers[key] = {"actions": [action]}
        self.state.indices_for("set-a")[key] = 0

    def find_trigger(self, key):
        return self.triggers.get(key)

    def test_without_mark_returns_only_starting_key(self):
        self.register("a", call("b"))

        self.assertEqual(chain_from(self.state, "set-a", "a", self.find_trigger), ("a",))

    def test_follows_two_and_three_trigger_chains(self):
        self.register("a", call("b"))
        self.register("b", call("c"))
        self.register("c", {"type": "text", "text": "done"})
        self.state.call_refs_for("set-a").add("a")

        self.assertEqual(chain_from(self.state, "set-a", "a", self.find_trigger), ("a", "b"))
        self.state.call_refs_for("set-a").add("b")
        self.assertEqual(chain_from(self.state, "set-a", "a", self.find_trigger), ("a", "b", "c"))
        self.assertEqual(chain_top(self.state, "set-a", "a", self.find_trigger), "c")

    def test_stops_when_current_row_is_not_a_call_or_target_is_missing(self):
        self.register("a", {"type": "text", "text": "ordinary"})
        self.register("b", call("missing"))
        self.state.call_refs_for("set-a").update({"a", "b"})

        self.assertEqual(chain_from(self.state, "set-a", "a", self.find_trigger), ("a",))
        self.assertEqual(chain_from(self.state, "set-a", "b", self.find_trigger), ("b",))

    def test_stops_before_repeating_a_key(self):
        self.register("a", call("b"))
        self.register("b", call("a"))
        self.state.call_refs_for("set-a").update({"a", "b"})

        self.assertEqual(chain_from(self.state, "set-a", "a", self.find_trigger), ("a", "b"))

    def test_stops_at_maximum_call_depth(self):
        keys = [f"k{index}" for index in range(MAX_CALL_DEPTH + 2)]
        for index, key in enumerate(keys):
            self.register(key, call(keys[index + 1]) if index + 1 < len(keys) else {"type": "text"})
        self.state.call_refs_for("set-a").update(keys[:-1])

        chain = chain_from(self.state, "set-a", keys[0], self.find_trigger)

        self.assertEqual(len(chain), MAX_CALL_DEPTH + 1)
        self.assertEqual(chain[-1], keys[MAX_CALL_DEPTH])


if __name__ == "__main__":
    unittest.main()
