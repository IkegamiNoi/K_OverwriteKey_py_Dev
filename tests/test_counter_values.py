import unittest

from keyseq.application.app_state import AppState
from keyseq.application.counter_values import CounterValues, counter_start, counter_value


class CounterValuesTest(unittest.TestCase):
    def test_value_uses_stored_value_then_start_then_zero(self):
        counters = CounterValues()
        counters.set_starts({"used": 10, "unused": -3})
        counters["used"] = 0
        self.assertEqual(counters.value("used"), 0)
        self.assertEqual(counters.value("unused"), -3)
        self.assertEqual(counters.value("missing"), 0)
        self.assertNotIn("unused", counters)
        self.assertNotIn("missing", counters)

    def test_set_starts_copies_mapping_without_changing_values(self):
        counters = CounterValues()
        counters["used"] = 8
        starts = {"used": 3, "unused": 4}
        counters.set_starts(starts)
        starts["unused"] = 99
        self.assertEqual(counters, {"used": 8})
        self.assertEqual(counters.value("unused"), 4)
        counters.set_starts({"unused": 6})
        self.assertEqual(counters.value("used"), 8)
        self.assertEqual(counter_start(counters, "used"), 0)

    def test_helpers_accept_plain_dict_and_counter_values(self):
        counters = CounterValues()
        counters.set_starts({"n": 7})
        for values, expected in (({}, 0), ({"n": -2}, -2), (counters, 7)):
            with self.subTest(values=values):
                self.assertEqual(counter_value(values, "n"), expected)
                self.assertEqual(counter_start(values, "n"), 7 if values is counters else 0)

    def test_app_state_keeps_values_and_starts_on_reset(self):
        state = AppState()
        state.set_counter_starts({"n": 5})
        state.counters["used"] = 9
        counters = state.counters
        state.reset_indices()
        self.assertIs(state.counters, counters)
        self.assertEqual(counter_value(state.counters, "n"), 5)
        self.assertEqual(state.counters, {"used": 9})
