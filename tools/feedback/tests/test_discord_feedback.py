import importlib.machinery
import importlib.util
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "discord-feedback"
LOADER = importlib.machinery.SourceFileLoader("discord_feedback", str(SCRIPT_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
discord_feedback = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = discord_feedback
LOADER.exec_module(discord_feedback)


class ValidationTests(unittest.TestCase):
    def test_primary_and_serial_validation_have_inner_and_outer_timeouts(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            repo = root / "repo"
            artifact_dir = root / "artifacts"
            challenge = pathlib.PurePosixPath("challenges/test-module/test-challenge")
            (repo / challenge / "challenge").mkdir(parents=True)
            failure_log = artifact_dir / "test-logs-attempt-7" / challenge / "tests_private/test_solve.log"
            failure_log.parent.mkdir(parents=True)
            failure_log.write_text("failed\n")

            def invocation(_repo, arguments):
                return ["pwnshop", *arguments]

            with (
                mock.patch.object(
                    discord_feedback,
                    "pwnshop_invocation",
                    side_effect=invocation,
                ),
                mock.patch.object(discord_feedback, "run_logged", side_effect=[1, 0]) as run_logged,
            ):
                result = discord_feedback.run_tests(repo, artifact_dir, "origin/main", 7)

            self.assertEqual(result, artifact_dir / "pwnshop-test-attempt-7.log")
            self.assertEqual(run_logged.call_count, 2)
            for call in run_logged.call_args_list:
                command = call.args[0]
                inner_timeout_index = command.index("--timeout")
                self.assertEqual(
                    command[inner_timeout_index + 1],
                    str(discord_feedback.PWNSHOP_TEST_TIMEOUT_SECONDS),
                )
                self.assertEqual(
                    call.kwargs["timeout"],
                    discord_feedback.PWNSHOP_VALIDATION_TIMEOUT_SECONDS,
                )

            self.assertEqual(discord_feedback.PWNSHOP_TEST_TIMEOUT_SECONDS, 600)
            self.assertEqual(discord_feedback.PWNSHOP_VALIDATION_TIMEOUT_SECONDS, 3600)
            serial_command = run_logged.call_args_list[1].args[0]
            self.assertEqual(serial_command[-1], challenge.as_posix())
            self.assertEqual(serial_command[serial_command.index("--jobs") + 1], "1")

    def test_timeout_runs_apply_mode_repair_and_retries(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            repo = root / "repo"
            artifact_dir = root / "artifacts"
            artifact_dir.mkdir()
            analysis_path = artifact_dir / "analysis.md"
            successful_log = artifact_dir / "pwnshop-test-attempt-2.log"
            timeout = subprocess.TimeoutExpired(["pwnshop", "test"], 3600)

            with (
                mock.patch.object(
                    discord_feedback,
                    "run_tests",
                    side_effect=[timeout, successful_log],
                ) as run_tests,
                mock.patch.object(discord_feedback, "run_agent") as run_agent,
                mock.patch.object(discord_feedback, "force_fresh_pwnshop") as force_fresh_pwnshop,
            ):
                result = discord_feedback.validate_with_fixes(
                    repo,
                    artifact_dir,
                    "origin/main",
                    agent="codex",
                    analysis_path=analysis_path,
                    directions=[],
                    pr_feedback_path=None,
                    fix_attempts=None,
                )

            self.assertEqual(result, successful_log)
            self.assertEqual([call.args[-1] for call in run_tests.call_args_list], [1, 2])
            run_agent.assert_called_once()
            repair_call = run_agent.call_args
            self.assertEqual(repair_call.args[0], "codex")
            self.assertTrue(repair_call.kwargs["apply"])
            self.assertEqual(repair_call.kwargs["output_name"], "fix-agent-attempt-1.log")
            self.assertIn("TimeoutExpired", repair_call.args[1])
            self.assertIn("timed out after 3600 seconds", repair_call.args[1])
            force_fresh_pwnshop.assert_called_once_with()

    def test_fix_prompt_names_all_attempt_artifacts_and_failure(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_dir = pathlib.Path(temporary_directory) / "artifacts"
            analysis_path = artifact_dir / "analysis.md"
            failure = subprocess.TimeoutExpired(["pwnshop", "test"], 3600)

            prompt = discord_feedback.build_fix_prompt(
                analysis_path,
                artifact_dir,
                4,
                failure,
                [],
            )

            expected_paths = [
                artifact_dir / "pwnshop-test-attempt-4.log",
                artifact_dir / "test-logs-attempt-4",
                artifact_dir / "pwnshop-test-attempt-4-serial.log",
                artifact_dir / "test-logs-attempt-4-serial",
            ]
            for path in expected_paths:
                self.assertIn(str(path), prompt)
            self.assertIn("Observed failure: TimeoutExpired", prompt)
            self.assertIn("timed out after 3600 seconds", prompt)

    def test_next_validation_attempt_avoids_primary_and_serial_collisions(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_dir = pathlib.Path(temporary_directory)
            self.assertEqual(discord_feedback.next_validation_attempt(artifact_dir), 1)
            for name in (
                "pwnshop-test-attempt-1.log",
                "pwnshop-test-attempt-3-serial.log",
                "pwnshop-test-attempt-7.log",
                "pwnshop-test-attempt-10-serial.log",
                "pwnshop-test-attempt-10.log",
                "pwnshop-test-attempt-invalid.log",
                "pwnshop-test-attempt-99.log.backup",
            ):
                (artifact_dir / name).write_text("")

            self.assertEqual(discord_feedback.next_validation_attempt(artifact_dir), 11)
            self.assertEqual(
                discord_feedback.resumed_test_log(artifact_dir, {}),
                artifact_dir / "pwnshop-test-attempt-10.log",
            )

    def test_resumed_validation_forces_a_fresh_pwnshop_generation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            artifact_dir = root / "artifacts"
            artifact_dir.mkdir()
            (artifact_dir / "pwnshop-test-attempt-4.log").write_text("failed\n")
            successful_log = artifact_dir / "pwnshop-test-attempt-5.log"

            with (
                mock.patch.object(discord_feedback, "run_tests", return_value=successful_log) as run_tests,
                mock.patch.object(discord_feedback, "force_fresh_pwnshop") as force_fresh_pwnshop,
            ):
                result = discord_feedback.validate_with_fixes(
                    root,
                    artifact_dir,
                    "origin/main",
                    agent="codex",
                    analysis_path=artifact_dir / "analysis.md",
                    directions=[],
                    pr_feedback_path=None,
                    fix_attempts=None,
                )

            self.assertEqual(result, successful_log)
            force_fresh_pwnshop.assert_called_once_with()
            self.assertEqual(run_tests.call_args.args[-1], 5)


class StreamCommandTests(unittest.TestCase):
    @staticmethod
    def process_is_live(pid):
        try:
            state = pathlib.Path(f"/proc/{pid}/stat").read_text().split()[2]
        except (FileNotFoundError, ProcessLookupError):
            return False
        return state != "Z"

    def test_timeout_marker_is_written_to_command_log(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            log_path = root / "command.log"
            command = [
                sys.executable,
                "-c",
                "import time; print('started', flush=True); time.sleep(60)",
            ]

            with self.assertRaises(subprocess.TimeoutExpired):
                discord_feedback.stream_command(
                    command,
                    cwd=root,
                    log_path=log_path,
                    timeout=0.05,
                    heartbeat_label="validation",
                )

            log = log_path.read_text()
            self.assertIn("started", log)
            self.assertIn("validation timed out after 0.05s", log)

    def test_exited_leader_does_not_leave_live_grandchild(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            log_path = root / "command.log"
            pid_path = root / "grandchild.pid"
            leader_code = "\n".join(
                (
                    "import pathlib, subprocess, sys",
                    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])",
                    "pathlib.Path(sys.argv[1]).write_text(str(child.pid))",
                    "print('leader exiting', flush=True)",
                )
            )
            grandchild_pid = None
            try:
                return_code = discord_feedback.stream_command(
                    [sys.executable, "-c", leader_code, str(pid_path)],
                    cwd=root,
                    log_path=log_path,
                    timeout=5,
                    heartbeat_label="leader",
                )
                grandchild_pid = int(pid_path.read_text())

                deadline = time.monotonic() + 2
                while self.process_is_live(grandchild_pid) and time.monotonic() < deadline:
                    time.sleep(0.02)

                self.assertEqual(return_code, 0)
                self.assertIn("leader exiting", log_path.read_text())
                self.assertFalse(self.process_is_live(grandchild_pid))
            finally:
                if grandchild_pid is not None and self.process_is_live(grandchild_pid):
                    try:
                        os.kill(grandchild_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass


if __name__ == "__main__":
    unittest.main()
