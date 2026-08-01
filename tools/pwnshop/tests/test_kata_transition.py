import pathlib
import sys
import threading
import unittest


PWNSHOP_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PWNSHOP_ROOT / "src"))

from pwnshop import lib  # noqa: E402


class KataTransitionTests(unittest.TestCase):
    def test_kata_workers_are_serialized(self):
        first_entered = threading.Event()
        release_first = threading.Event()
        second_entered = threading.Event()

        def first_call():
            first_entered.set()
            release_first.wait()

        first = threading.Thread(target=lib._run_with_transition_lock, args=("kata", first_call))
        second = threading.Thread(
            target=lib._run_with_transition_lock,
            args=("kata", second_entered.set),
        )
        first.start()
        self.assertTrue(first_entered.wait(1))
        second.start()
        self.assertFalse(second_entered.wait(0.1))
        release_first.set()
        first.join(1)
        second.join(1)

        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())
        self.assertTrue(second_entered.is_set())


if __name__ == "__main__":
    unittest.main()
