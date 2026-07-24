import datetime
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

import click
from click.testing import CliRunner


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "discord-feedback"
LOADER = importlib.machinery.SourceFileLoader("discord_feedback", str(SCRIPT_PATH))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
discord_feedback = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = discord_feedback
LOADER.exec_module(discord_feedback)


class ResumeTests(unittest.TestCase):
    def test_analysis_checkpoint_skips_discord_scrape_without_token(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            run_id = "20260712-052851"
            artifact_dir = repo / ".discord-feedback" / run_id
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "analysis.md").write_text("analysis complete\n")
            (artifact_dir / "resume-state.json").write_text(json.dumps({"completed_phases": ["analysis"]}) + "\n")

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "resolve_scrape_since") as resolve_scrape_since,
                mock.patch.object(discord_feedback, "DiscordAPI") as discord_api,
                mock.patch.object(discord_feedback.GitHubAPI, "from_environment") as github_api,
                mock.patch.object(discord_feedback, "write_transcript") as write_transcript,
                mock.patch.object(discord_feedback, "run_agent") as run_agent,
                mock.patch.dict(os.environ, {"DISCORD_BOT_TOKEN": ""}),
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    ["--resume", run_id],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(
                "Resume: reusing feedback artifacts (skipping Discord scrape)",
                result.output,
            )
            resolve_scrape_since.assert_not_called()
            discord_api.assert_not_called()
            github_api.assert_not_called()
            write_transcript.assert_not_called()
            run_agent.assert_not_called()
            state = json.loads((artifact_dir / "resume-state.json").read_text())
            self.assertEqual(state["completed_phases"], ["analysis", "scrape"])

    def test_analysis_checkpoint_requires_completed_analysis_artifact(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            run_id = "20260712-052851"
            artifact_dir = repo / ".discord-feedback" / run_id
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "resume-state.json").write_text(json.dumps({"completed_phases": ["analysis"]}) + "\n")

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "resolve_scrape_since") as resolve_scrape_since,
                mock.patch.object(discord_feedback, "DiscordAPI") as discord_api,
                mock.patch.dict(os.environ, {"DISCORD_BOT_TOKEN": ""}),
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    ["--resume", run_id],
                )

            self.assertEqual(result.exit_code, 1, result.output)
            self.assertIn(
                "analysis is checkpointed but analysis.md is missing or empty",
                result.output,
            )
            resolve_scrape_since.assert_not_called()
            discord_api.assert_not_called()

    def test_uncheckpointed_resume_still_requires_discord_token(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            run_id = "20260712-052851"
            artifact_dir = repo / ".discord-feedback" / run_id
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "resume-state.json").write_text(json.dumps({"completed_phases": []}) + "\n")
            now = datetime.datetime(2026, 7, 12, 5, 28, 51, tzinfo=datetime.timezone.utc)

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "utc_now", return_value=now),
                mock.patch.object(
                    discord_feedback,
                    "resolve_scrape_since",
                    return_value=now - datetime.timedelta(hours=1),
                ),
                mock.patch.object(discord_feedback, "DiscordAPI") as discord_api,
                mock.patch.dict(os.environ, {"DISCORD_BOT_TOKEN": ""}),
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    ["--resume", run_id],
                )

            self.assertEqual(result.exit_code, 1, result.output)
            self.assertIn("DISCORD_BOT_TOKEN is not set", result.output)
            discord_api.assert_not_called()

    def test_scrape_checkpoint_skips_fetch_and_resumes_analysis(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            run_id = "20260712-052851"
            artifact_dir = repo / ".discord-feedback" / run_id
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "messages.jsonl").write_text("{}\n")
            (artifact_dir / "transcript.md").write_text("transcript\n")
            (artifact_dir / "run.json").write_text("{}\n")
            pr_feedback_path = artifact_dir / "recent-pr-feedback.md"
            pr_feedback_path.write_text("maintainer context\n")
            (artifact_dir / "resume-state.json").write_text(json.dumps({"completed_phases": ["scrape"]}) + "\n")
            analysis_path = artifact_dir / "analysis.md"

            def finish_analysis(*_args, **_kwargs):
                analysis_path.write_text("analysis complete\n")
                return analysis_path

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "DiscordAPI") as discord_api,
                mock.patch.object(
                    discord_feedback,
                    "run_agent",
                    side_effect=finish_analysis,
                ) as run_agent,
                mock.patch.dict(os.environ, {"DISCORD_BOT_TOKEN": ""}),
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    ["--resume", run_id],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            discord_api.assert_not_called()
            run_agent.assert_called_once()
            self.assertIn(str(pr_feedback_path), run_agent.call_args.args[1])
            state = json.loads((artifact_dir / "resume-state.json").read_text())
            self.assertEqual(state["completed_phases"], ["analysis", "scrape"])

    def test_legacy_run_metadata_infers_completed_scrape(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_dir = pathlib.Path(temporary_directory)
            (artifact_dir / "run.json").write_text("{}\n")

            self.assertEqual(
                discord_feedback.infer_completed_phases(artifact_dir),
                ["scrape"],
            )

            (artifact_dir / "analysis.md").write_text("analysis complete\n")
            self.assertEqual(
                discord_feedback.infer_completed_phases(artifact_dir),
                ["scrape", "analysis"],
            )

    def test_completed_scrape_is_checkpointed_before_fetch_only_returns(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            now = datetime.datetime(2026, 7, 12, 5, 28, 51, tzinfo=datetime.timezone.utc)
            run_id = now.strftime("%Y%m%d-%H%M%S")
            artifact_dir = repo / ".discord-feedback" / run_id

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "utc_now", return_value=now),
                mock.patch.object(
                    discord_feedback,
                    "resolve_scrape_since",
                    return_value=now - datetime.timedelta(hours=1),
                ),
                mock.patch.object(
                    discord_feedback,
                    "discover_channels",
                    return_value=([], {}),
                ),
                mock.patch.dict(os.environ, {"DISCORD_BOT_TOKEN": "token"}),
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    ["--fetch-only", "--no-pr-feedback"],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            state = json.loads((artifact_dir / "resume-state.json").read_text())
            self.assertEqual(state["completed_phases"], ["scrape"])
            self.assertTrue((artifact_dir / "messages.jsonl").is_file())
            self.assertTrue((artifact_dir / "transcript.md").is_file())
            self.assertTrue((artifact_dir / "run.json").is_file())


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


class OperatorFeedbackTests(unittest.TestCase):
    def test_agent_retries_policy_failure_with_recovery_prompt(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            artifact_dir = root / "artifacts"
            artifact_dir.mkdir()
            output_path = artifact_dir / "agent.md"
            prompts = []

            def stream_agent(_command, **kwargs):
                prompts.append(kwargs["input_text"])
                if len(prompts) == 1:
                    kwargs["line_handler"](
                        json.dumps(
                            {
                                "type": "turn.failed",
                                "error": {"message": "This content was flagged for possible cybersecurity risk."},
                            }
                        )
                    )
                    return 1
                output_path.write_text("recovered\n")
                return 0

            with (
                mock.patch.object(
                    discord_feedback,
                    "resolve_agent",
                    return_value=("codex", ["codex", "exec", "-"]),
                ),
                mock.patch.object(
                    discord_feedback,
                    "stream_command",
                    side_effect=stream_agent,
                ) as stream_command,
                mock.patch.object(discord_feedback.time, "sleep") as sleep,
            ):
                result = discord_feedback.run_agent(
                    "codex",
                    "Do the phase.",
                    repo=root,
                    artifact_dir=artifact_dir,
                    output_name=output_path.name,
                )

            self.assertEqual(result, output_path)
            self.assertEqual(output_path.read_text(), "recovered\n")
            self.assertEqual(stream_command.call_count, 2)
            self.assertNotIn("Recovery attempt", prompts[0])
            self.assertIn("Recovery attempt 2", prompts[1])
            self.assertIn("Do not open or quote tests_private", prompts[1])
            self.assertEqual(
                stream_command.call_args_list[0].kwargs["timeout"],
                discord_feedback.AGENT_ATTEMPT_TIMEOUT_SECONDS,
            )
            sleep.assert_called_once_with(discord_feedback.AGENT_RETRY_BASE_DELAY_SECONDS)

    def test_interrupted_agent_is_not_retried(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            artifact_dir = root / "artifacts"
            artifact_dir.mkdir()

            with (
                mock.patch.object(
                    discord_feedback,
                    "resolve_agent",
                    return_value=("codex", ["codex", "exec", "-"]),
                ),
                mock.patch.object(
                    discord_feedback,
                    "stream_command",
                    return_value=130,
                ) as stream_command,
                mock.patch.object(discord_feedback.time, "sleep") as sleep,
            ):
                with self.assertRaisesRegex(click.ClickException, "interrupted"):
                    discord_feedback.run_agent(
                        "codex",
                        "Do the phase.",
                        repo=root,
                        artifact_dir=artifact_dir,
                        output_name="agent.md",
                    )

            stream_command.assert_called_once()
            sleep.assert_not_called()

    def test_optional_cast_review_records_failure_and_continues(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            artifact_dir = root / "artifacts"
            artifact_dir.mkdir()

            with mock.patch.object(
                discord_feedback,
                "run_casts",
                side_effect=click.ClickException("provider stayed unavailable"),
            ):
                result = discord_feedback.run_optional_cast_review(
                    root,
                    artifact_dir,
                    artifact_dir / "analysis.md",
                    ["challenges/example/one"],
                    "codex",
                    [],
                )

            self.assertEqual(result, artifact_dir / "ux-review.md")
            self.assertIn("UX review unavailable", result.read_text())
            self.assertIn("provider stayed unavailable", result.read_text())

    def test_feedback_is_appended_as_durable_jsonl(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            feedback_path = pathlib.Path(temporary_directory) / "feedback.jsonl"

            first = discord_feedback.append_operator_feedback(feedback_path, "  Prefer the smaller fix.  ")
            second = discord_feedback.append_operator_feedback(feedback_path, "Keep Unicode: ☃")

            entries = discord_feedback.load_operator_feedback(feedback_path)
            self.assertEqual([entry["id"] for entry in entries], [first["id"], second["id"]])
            self.assertEqual(entries[0]["text"], "Prefer the smaller fix.")
            self.assertEqual(entries[1]["text"], "Keep Unicode: ☃")
            self.assertEqual(entries[0]["source"], "terminal")
            self.assertTrue(entries[0]["created_at"].endswith("+00:00"))

            with self.assertRaisesRegex(ValueError, "cannot be empty"):
                discord_feedback.append_operator_feedback(feedback_path, "   ")
            with self.assertRaisesRegex(ValueError, "cannot exceed"):
                discord_feedback.append_operator_feedback(
                    feedback_path,
                    "x" * (discord_feedback.OPERATOR_FEEDBACK_MAX_CHARS + 1),
                )

    def test_pending_feedback_ignores_malformed_and_handled_entries(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            feedback_path = pathlib.Path(temporary_directory) / "feedback.jsonl"
            handled = discord_feedback.append_operator_feedback(feedback_path, "done")
            pending = discord_feedback.append_operator_feedback(feedback_path, "new")
            with feedback_path.open("a") as output:
                output.write("not-json\n")
                output.write('{"id": "missing-text"}\n')

            entries = discord_feedback.pending_operator_feedback(
                feedback_path,
                {"handled_operator_feedback": [handled["id"]]},
            )

            self.assertEqual([entry["id"] for entry in entries], [pending["id"]])

    def test_every_agent_prompt_points_to_live_feedback_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            artifact_dir = root / "artifacts"
            artifact_dir.mkdir()
            streamed_prompt = None

            def stream_agent(_command, **kwargs):
                nonlocal streamed_prompt
                streamed_prompt = kwargs["input_text"]
                return 0

            with (
                mock.patch.object(
                    discord_feedback,
                    "resolve_agent",
                    return_value=("claude", ["claude"]),
                ),
                mock.patch.object(
                    discord_feedback,
                    "stream_command",
                    side_effect=stream_agent,
                ),
            ):
                discord_feedback.run_agent(
                    "claude",
                    "Do the phase.",
                    repo=root,
                    artifact_dir=artifact_dir,
                    output_name="agent.md",
                )

            self.assertIsNotNone(streamed_prompt)
            self.assertIn(
                str(artifact_dir / discord_feedback.OPERATOR_FEEDBACK_FILENAME),
                streamed_prompt,
            )
            self.assertIn("re-read the file immediately before finalizing", streamed_prompt)
            self.assertIn("Later entries supersede earlier entries", streamed_prompt)

    def test_reconciliation_leaves_feedback_arriving_mid_agent_pending(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            artifact_dir = root / "artifacts"
            artifact_dir.mkdir()
            state_path = artifact_dir / "pr-watch-state.json"
            state = discord_feedback.load_watch_state(state_path)
            feedback_path = discord_feedback.operator_feedback_path(artifact_dir)
            first = discord_feedback.append_operator_feedback(feedback_path, "first")
            arriving = None

            def run_feedback_agent(*_args, **_kwargs):
                nonlocal arriving
                response_path = artifact_dir / "operator-feedback-response-001.md"
                response_path.write_text("addressed\n")
                arriving = discord_feedback.append_operator_feedback(feedback_path, "arrived while the agent ran")
                return artifact_dir / "operator-feedback-agent-001.log"

            with mock.patch.object(
                discord_feedback,
                "run_agent",
                side_effect=run_feedback_agent,
            ):
                handled, pushed = discord_feedback.address_pending_operator_feedback(
                    root,
                    artifact_dir,
                    "codex",
                    [],
                    state,
                    state_path,
                )

            self.assertTrue(handled)
            self.assertFalse(pushed)
            self.assertEqual(state["handled_operator_feedback"], [first["id"]])
            self.assertIsNotNone(arriving)
            pending = discord_feedback.pending_operator_feedback(feedback_path, state)
            self.assertEqual([entry["id"] for entry in pending], [arriving["id"]])
            saved = json.loads(state_path.read_text())
            self.assertEqual(saved["handled_operator_feedback"], [first["id"]])

    def test_failed_operator_feedback_push_keeps_batch_pending(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            artifact_dir = root / "artifacts"
            artifact_dir.mkdir()
            state_path = artifact_dir / "pr-watch-state.json"
            state = discord_feedback.load_watch_state(state_path)
            feedback_path = discord_feedback.operator_feedback_path(artifact_dir)
            entry = discord_feedback.append_operator_feedback(feedback_path, "fix it")
            push_error = subprocess.CalledProcessError(1, ["git", "push"])

            with (
                mock.patch.object(discord_feedback, "run_agent"),
                mock.patch.object(
                    discord_feedback,
                    "commit_and_push",
                    side_effect=push_error,
                ),
            ):
                with self.assertRaisesRegex(OSError, "could not commit or push"):
                    discord_feedback.address_pending_operator_feedback(
                        root,
                        artifact_dir,
                        "codex",
                        [],
                        state,
                        state_path,
                        pr_url="https://github.com/pwncollege/challenges/pull/123",
                        commit_changes=True,
                    )

            self.assertNotIn(entry["id"], state["handled_operator_feedback"])
            pending = discord_feedback.pending_operator_feedback(feedback_path, state)
            self.assertEqual([item["id"] for item in pending], [entry["id"]])
            saved = json.loads(state_path.read_text())
            self.assertEqual(saved["handled_operator_feedback"], [])

    def test_watcher_backs_off_after_failed_operator_feedback_push(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            artifact_dir = repo / "artifacts"
            artifact_dir.mkdir()
            discord_feedback.append_operator_feedback(
                discord_feedback.operator_feedback_path(artifact_dir),
                "fix it",
            )
            push_error = subprocess.CalledProcessError(1, ["git", "push"])
            pull_states = [
                {"state": "open", "merged_at": None},
                {"state": "closed", "merged_at": "2026-07-13T00:00:00Z"},
            ]

            with (
                mock.patch.object(
                    discord_feedback,
                    "github_repo_slug",
                    return_value=("pwncollege", "challenges"),
                ),
                mock.patch.object(discord_feedback, "parse_pr_number", return_value=123),
                mock.patch.object(
                    discord_feedback.GitHubAPI,
                    "from_environment",
                    return_value=object(),
                ),
                mock.patch.object(
                    discord_feedback,
                    "get_pull_request",
                    side_effect=pull_states,
                ) as get_pull_request,
                mock.patch.object(discord_feedback, "run_agent") as run_agent,
                mock.patch.object(
                    discord_feedback,
                    "commit_and_push",
                    side_effect=push_error,
                ),
            ):
                started = time.monotonic()
                discord_feedback.watch_pull_request(
                    repo,
                    artifact_dir,
                    "https://github.com/pwncollege/challenges/pull/123",
                    "codex",
                    [],
                    0.05,
                    3,
                )
                elapsed = time.monotonic() - started

            self.assertGreaterEqual(elapsed, 0.04)
            run_agent.assert_called_once()
            self.assertEqual(get_pull_request.call_count, 2)

    def test_feedback_wakes_waiter_without_waiting_for_poll_interval(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            feedback_path = pathlib.Path(temporary_directory) / "feedback.jsonl"

            def submit_feedback():
                time.sleep(0.05)
                discord_feedback.append_operator_feedback(feedback_path, "wake up")

            thread = threading.Thread(target=submit_feedback)
            started = time.monotonic()
            thread.start()
            try:
                received = discord_feedback.wait_for_operator_feedback(
                    feedback_path,
                    {"handled_operator_feedback": []},
                    2,
                )
            finally:
                thread.join()

            self.assertTrue(received)
            self.assertLess(time.monotonic() - started, 1)

    def test_tui_auto_detection_requires_an_interactive_parent(self):
        with (
            mock.patch.object(sys.stdin, "isatty", return_value=True),
            mock.patch.object(sys.stdout, "isatty", return_value=True),
            mock.patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=False),
        ):
            self.assertTrue(discord_feedback.should_launch_terminal_ui(True))
            self.assertFalse(discord_feedback.should_launch_terminal_ui(False))
            with mock.patch.dict(
                os.environ,
                {discord_feedback.TUI_CHILD_ENV: "1"},
                clear=False,
            ):
                self.assertFalse(discord_feedback.should_launch_terminal_ui(True))

    def test_cli_routes_interactive_run_through_tui_parent(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            now = datetime.datetime(2026, 7, 13, 1, 2, 3, tzinfo=datetime.timezone.utc)

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "utc_now", return_value=now),
                mock.patch.object(
                    discord_feedback,
                    "should_launch_terminal_ui",
                    return_value=True,
                ),
                mock.patch.object(
                    discord_feedback,
                    "run_terminal_ui",
                    return_value=(0, repo / "run-ui.log"),
                ) as run_terminal_ui,
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    ["--fetch-only"],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            run_terminal_ui.assert_called_once()
            self.assertEqual(run_terminal_ui.call_args.kwargs["run_id"], "20260713-010203")
            self.assertTrue(
                (repo / ".discord-feedback" / "20260713-010203" / discord_feedback.OPERATOR_FEEDBACK_FILENAME).is_file()
            )
            self.assertIn("discord-feedback exited with code 0", result.output)

    def test_cli_tui_failure_keeps_resume_command_visible(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            now = datetime.datetime(2026, 7, 13, 1, 2, 3, tzinfo=datetime.timezone.utc)

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "utc_now", return_value=now),
                mock.patch.object(
                    discord_feedback,
                    "should_launch_terminal_ui",
                    return_value=True,
                ),
                mock.patch.object(
                    discord_feedback,
                    "run_terminal_ui",
                    return_value=(130, repo / "run-ui.log"),
                ),
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    ["--fetch-only"],
                )

            self.assertEqual(result.exit_code, 130, result.output)
            self.assertIn("--resume 20260713-010203", result.output)
            self.assertIn("Every completed phase is checkpointed", result.output)

    def test_feedback_arriving_during_validation_restarts_downstream_phases(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            run_id = "20260713-010203"
            artifact_dir = repo / ".discord-feedback" / run_id
            artifact_dir.mkdir(parents=True)
            (artifact_dir / "analysis.md").write_text("analysis complete\n")
            (artifact_dir / "implementation-notes.md").write_text("implemented\n")
            (artifact_dir / "resume-state.json").write_text(
                json.dumps({"completed_phases": ["analysis", "implementation"]}) + "\n"
            )

            invalidation_seen_by_agent = False

            def write_agent_output(*_args, **kwargs):
                nonlocal invalidation_seen_by_agent
                if kwargs["output_name"].startswith("operator-feedback-agent-"):
                    checkpoint = json.loads((artifact_dir / "resume-state.json").read_text())
                    invalidation_seen_by_agent = "validation" not in checkpoint["completed_phases"]
                output_path = artifact_dir / kwargs["output_name"]
                output_path.write_text("# Summary\n\nValidated changes.\n")
                return output_path

            validation_log = artifact_dir / "pwnshop-test-attempt-1.log"
            validation_calls = 0

            def validate_phase(*_args, **_kwargs):
                nonlocal validation_calls
                validation_calls += 1
                if validation_calls == 1:
                    discord_feedback.append_operator_feedback(
                        discord_feedback.operator_feedback_path(artifact_dir),
                        "Feedback submitted during validation.",
                    )
                return validation_log

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "prepare_branch"),
                mock.patch.object(
                    discord_feedback,
                    "validate_with_fixes",
                    side_effect=validate_phase,
                ),
                mock.patch.object(
                    discord_feedback,
                    "changed_challenges_since",
                    return_value=[],
                ),
                mock.patch.object(
                    discord_feedback,
                    "run_agent",
                    side_effect=write_agent_output,
                ),
                mock.patch.object(
                    discord_feedback,
                    "pr_body_is_usable",
                    return_value=True,
                ),
                mock.patch.object(discord_feedback, "git_output", return_value=""),
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    ["--resume", run_id, "--apply", "--skip-casts"],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(validation_calls, 2)
            self.assertTrue(invalidation_seen_by_agent)
            self.assertIn(
                "Direct operator feedback invalidated completed phase(s): validation",
                result.output,
            )
            state = json.loads((artifact_dir / "resume-state.json").read_text())
            self.assertIn("validation", state["completed_phases"])
            self.assertIn("pr-body", state["completed_phases"])

    def test_resumed_existing_pr_pushes_reconciled_operator_feedback(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            run_id = "20260713-010203"
            artifact_dir = repo / ".discord-feedback" / run_id
            artifact_dir.mkdir(parents=True)
            validation_log = artifact_dir / "pwnshop-test-attempt-1.log"
            validation_log.write_text("passed\n")
            (artifact_dir / "analysis.md").write_text("analysis complete\n")
            (artifact_dir / "implementation-notes.md").write_text("implemented\n")
            (artifact_dir / "pr-body.md").write_text("old body\n")
            (artifact_dir / "pr-url.txt").write_text("https://github.com/pwncollege/challenges/pull/123\n")
            (artifact_dir / "resume-state.json").write_text(
                json.dumps(
                    {
                        "completed_phases": [
                            "scrape",
                            "analysis",
                            "implementation",
                            "validation",
                            "casts",
                            "pr-body",
                            "create-pr",
                        ],
                        "test_log": str(validation_log),
                    }
                )
                + "\n"
            )
            feedback = discord_feedback.append_operator_feedback(
                discord_feedback.operator_feedback_path(artifact_dir),
                "Use the direct operator correction.",
            )

            def write_agent_output(*_args, **kwargs):
                output_path = artifact_dir / kwargs["output_name"]
                output_path.write_text("# Summary\n\nValidated changes.\n")
                return output_path

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "prepare_branch"),
                mock.patch.object(
                    discord_feedback,
                    "validate_with_fixes",
                    return_value=validation_log,
                ),
                mock.patch.object(
                    discord_feedback,
                    "changed_challenges_since",
                    return_value=[],
                ),
                mock.patch.object(
                    discord_feedback,
                    "run_agent",
                    side_effect=write_agent_output,
                ),
                mock.patch.object(
                    discord_feedback,
                    "pr_body_is_usable",
                    return_value=True,
                ),
                mock.patch.object(
                    discord_feedback,
                    "commit_and_push",
                    return_value=True,
                ) as commit_and_push,
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    [
                        "--resume",
                        run_id,
                        "--apply",
                        "--create-pr",
                        "--no-watch-pr",
                        "--skip-casts",
                    ],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            commit_and_push.assert_called_once_with(repo, "Address operator feedback")
            self.assertIn("Pushed resumed feedback changes", result.output)
            watch_state = json.loads((artifact_dir / "pr-watch-state.json").read_text())
            self.assertIn(feedback["id"], watch_state["handled_operator_feedback"])

    def test_empty_feedback_run_completes_without_opening_pr(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = pathlib.Path(temporary_directory)
            run_id = "20260724-061106"
            artifact_dir = repo / ".discord-feedback" / run_id
            artifact_dir.mkdir(parents=True)
            test_log = artifact_dir / "pwnshop-test-attempt-1.log"
            test_log.write_text("No challenges found since origin/main\n")
            (artifact_dir / "analysis.md").write_text("No changes needed.\n")
            (artifact_dir / "implementation-notes.md").write_text("No changes needed.\n")
            (artifact_dir / "pr-body.md").write_text("No changes needed.\n")
            (artifact_dir / "resume-state.json").write_text(
                json.dumps(
                    {
                        "completed_phases": [
                            "scrape",
                            "analysis",
                            "implementation",
                            "validation",
                            "casts",
                            "pr-body",
                        ],
                        "test_log": str(test_log),
                    }
                )
                + "\n"
            )

            with (
                mock.patch.object(discord_feedback, "git_root", return_value=repo),
                mock.patch.object(discord_feedback, "prepare_branch"),
                mock.patch.object(
                    discord_feedback,
                    "changed_challenges_since",
                    return_value=[],
                ),
                mock.patch.object(
                    discord_feedback,
                    "existing_pr_url",
                    return_value=None,
                ),
                mock.patch.object(
                    discord_feedback,
                    "repository_has_pr_changes",
                    return_value=False,
                ),
                mock.patch.object(
                    discord_feedback,
                    "create_pull_request",
                ) as create_pull_request,
                mock.patch.dict(os.environ, {"DISCORD_BOT_TOKEN": ""}),
            ):
                result = CliRunner().invoke(
                    discord_feedback.feedback_command,
                    [
                        "--resume",
                        run_id,
                        "--apply",
                        "--create-pr",
                        "--no-watch-pr",
                        "--skip-casts",
                    ],
                )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("no repository changes were needed", result.output)
            self.assertIn("no PR was opened", result.output)
            create_pull_request.assert_not_called()
            state = json.loads((artifact_dir / "resume-state.json").read_text())
            self.assertIn("no-changes", state["completed_phases"])

    def test_existing_pr_recovery_pushes_a_clean_branch_ahead_of_origin(self):
        repo = pathlib.Path("/repo")

        def git_output(arguments, _repo):
            if arguments == ["branch", "--show-current"]:
                return "feedback/run"
            if arguments == [
                "rev-list",
                "--count",
                "refs/remotes/origin/feedback/run..HEAD",
            ]:
                return "1"
            self.fail(f"unexpected git_output arguments: {arguments}")

        succeeded = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with (
            mock.patch.object(
                discord_feedback,
                "git_output",
                side_effect=git_output,
            ),
            mock.patch.object(
                discord_feedback.subprocess,
                "run",
                side_effect=[succeeded, succeeded],
            ) as run,
        ):
            result = discord_feedback.push_commits_ahead_of_origin(repo)

        self.assertTrue(result)
        self.assertEqual(
            run.call_args_list[-1].args[0],
            ["git", "push", "-u", "origin", "HEAD"],
        )

    def test_existing_pr_recovery_skips_an_up_to_date_branch(self):
        repo = pathlib.Path("/repo")

        def git_output(arguments, _repo):
            outputs = {
                ("branch", "--show-current"): "feedback/run",
                (
                    "rev-list",
                    "--count",
                    "refs/remotes/origin/feedback/run..HEAD",
                ): "0",
            }
            return outputs[tuple(arguments)]

        remote_exists = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with (
            mock.patch.object(
                discord_feedback,
                "git_output",
                side_effect=git_output,
            ),
            mock.patch.object(
                discord_feedback.subprocess,
                "run",
                return_value=remote_exists,
            ) as run,
        ):
            result = discord_feedback.push_commits_ahead_of_origin(repo)

        self.assertFalse(result)
        run.assert_called_once()

    def test_commit_and_push_still_rejects_a_clean_new_branch(self):
        repo = pathlib.Path("/repo")
        with (
            mock.patch.object(discord_feedback, "git_output", return_value=""),
            mock.patch.object(discord_feedback.subprocess, "run") as run,
        ):
            result = discord_feedback.commit_and_push(repo, "No changes")

        self.assertFalse(result)
        run.assert_not_called()


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

    def test_tui_teardown_kills_descendants_after_leader_exits(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            pid_path = root / "grandchild.pid"
            leader_code = "\n".join(
                (
                    "import pathlib, subprocess, sys",
                    "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)",
                    "pathlib.Path(sys.argv[1]).write_text(str(child.pid))",
                )
            )
            grandchild_pid = None
            try:
                process = subprocess.Popen(
                    [sys.executable, "-c", leader_code, str(pid_path)],
                    start_new_session=True,
                )
                process.wait(timeout=5)
                grandchild_pid = int(pid_path.read_text())
                self.assertTrue(self.process_is_live(grandchild_pid))

                discord_feedback.stop_terminal_ui_child(process)

                deadline = time.monotonic() + 2
                while self.process_is_live(grandchild_pid) and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertFalse(self.process_is_live(grandchild_pid))
            finally:
                if grandchild_pid is not None and self.process_is_live(grandchild_pid):
                    try:
                        os.kill(grandchild_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

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
