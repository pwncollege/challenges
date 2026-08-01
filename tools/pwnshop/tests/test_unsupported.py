import contextlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from click.testing import CliRunner


PWNSHOP_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PWNSHOP_ROOT / "src"))

from pwnshop.commands import test as test_command  # noqa: E402


class TestCommandMetadataTests(unittest.TestCase):
    @staticmethod
    def challenge_context(flag):
        @contextlib.contextmanager
        def manager():
            yield "container-id", "http://workspace/", flag

        return manager()

    def invoke_test_command(
        self,
        returncode,
        *,
        allow_unsupported_tests=False,
        attempts=1,
        required=None,
    ):
        with tempfile.TemporaryDirectory() as directory:
            module = pathlib.Path(directory)
            challenge = module / "challenge"
            challenge.mkdir()
            if allow_unsupported_tests:
                (challenge / "challenge.yml").write_text("auxiliary:\n  pwnshop:\n    allow_unsupported_tests: true\n")
            if required is not None:
                (module / "module.yml").write_text(
                    f"resources:\n  - type: challenge\n    id: challenge\n    required: {str(required).lower()}\n"
                )

            rendered = module / "rendered"
            test = rendered / "tests_private" / "test_solve.py"
            test.parent.mkdir(parents=True)
            test.write_text("#!/usr/bin/python3\n")

            arguments = [
                "--jobs",
                "1",
                "--attempts",
                str(attempts),
                "--require-solved",
                str(challenge),
            ]
            outcome = subprocess.CompletedProcess(
                [str(test)],
                returncode,
                stdout="test output without the generated flag\n",
                stderr="",
            )

            with (
                mock.patch.object(test_command.lib, "resolve_targets", return_value=[challenge]),
                mock.patch.object(test_command.lib, "render_challenge", return_value=rendered),
                mock.patch.object(test_command.lib, "build_challenge", return_value="image-id"),
                mock.patch.object(
                    test_command.lib,
                    "run_challenge",
                    side_effect=lambda *_args, **_kwargs: self.challenge_context("generated-flag"),
                ) as run_challenge,
                mock.patch.object(test_command, "run_workspace_command", return_value=outcome) as run_test,
            ):
                result = CliRunner().invoke(test_command.test_command, arguments)

        return result, run_challenge.call_count, run_test.call_count

    def test_optional_challenge_does_not_need_to_emit_the_flag(self):
        result, container_calls, test_calls = self.invoke_test_command(0, required=False)

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual((container_calls, test_calls), (1, 1))
        self.assertNotIn("Unsolved challenges", result.output)

    def test_optional_challenge_test_failure_still_fails(self):
        result, container_calls, test_calls = self.invoke_test_command(1, required=False)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual((container_calls, test_calls), (1, 1))
        self.assertIn("Some tests failed", result.output)
        self.assertNotIn("Unsolved challenges", result.output)

    def test_unsupported_test_is_exempt_and_not_retried(self):
        result, container_calls, test_calls = self.invoke_test_command(
            test_command.UNSUPPORTED_TEST_EXIT_CODE,
            allow_unsupported_tests=True,
            attempts=4,
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual((container_calls, test_calls), (1, 1))
        self.assertNotIn("Unsolved challenges", result.output)

    def test_unsupported_exit_requires_opt_in(self):
        result, container_calls, test_calls = self.invoke_test_command(test_command.UNSUPPORTED_TEST_EXIT_CODE)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual((container_calls, test_calls), (1, 1))
        self.assertIn("Some tests failed", result.output)

    def test_unsupported_opt_in_requires_auxiliary_pwnshop_boolean(self):
        invalid_metadata = [
            "allow_unsupported_tests: true\n",
            "auxiliary:\n",
            "auxiliary: invalid\n",
            "auxiliary:\n  pwnshop:\n",
            "auxiliary:\n  pwnshop: invalid\n",
            'auxiliary:\n  pwnshop:\n    allow_unsupported_tests: "true"\n',
        ]
        with tempfile.TemporaryDirectory() as directory:
            challenge = pathlib.Path(directory)
            challenge_yml = challenge / "challenge.yml"
            for metadata in invalid_metadata:
                with self.subTest(metadata=metadata):
                    challenge_yml.write_text(metadata)
                    self.assertFalse(test_command._allows_unsupported_tests(challenge))

    def test_dojo_parser_preserves_auxiliary_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            dojo = pathlib.Path(directory)
            module = dojo / "module"
            challenge = module / "challenge"
            challenge.mkdir(parents=True)
            (dojo / "dojo.yml").write_text("id: test-dojo\nname: Test Dojo\nmodules:\n- id: module\n")
            (module / "module.yml").write_text(
                "name: Test Module\nresources:\n- type: challenge\n  id: challenge\n  name: Test Challenge\n"
            )
            (challenge / "challenge.yml").write_text(
                "auxiliary:\n  pwnshop:\n    allow_unsupported_tests: true\n  unrelated:\n    preserved: true\n"
            )

            parse_dojo_yml = PWNSHOP_ROOT.parents[1] / "tools" / "dojo" / "parse-dojo-yml"
            result = subprocess.run(
                [str(parse_dojo_yml), str(dojo / "dojo.yml"), "--json"],
                text=True,
                capture_output=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        auxiliary = json.loads(result.stdout)["modules"][0]["resources"][0]["auxiliary"]
        self.assertEqual(
            auxiliary,
            {
                "pwnshop": {"allow_unsupported_tests": True},
                "unrelated": {"preserved": True},
            },
        )

    def test_other_nonzero_exit_is_not_unsupported(self):
        result, container_calls, test_calls = self.invoke_test_command(1, allow_unsupported_tests=True)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual((container_calls, test_calls), (1, 1))
        self.assertIn("Some tests failed", result.output)

    def test_required_challenge_without_flag_is_still_unsolved(self):
        result, container_calls, test_calls = self.invoke_test_command(0)

        self.assertEqual(result.exit_code, 1)
        self.assertEqual((container_calls, test_calls), (1, 1))
        self.assertIn("Unsolved challenges", result.output)


if __name__ == "__main__":
    unittest.main()
