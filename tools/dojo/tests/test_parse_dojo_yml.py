import json
import pathlib
import subprocess
import tempfile
import unittest


PARSER = pathlib.Path(__file__).resolve().parents[1] / "parse-dojo-yml"


class ChallengeTransferTests(unittest.TestCase):
    def parse_challenge(self, transfer, *, location="resources"):
        with tempfile.TemporaryDirectory() as directory:
            dojo = pathlib.Path(directory)
            module = dojo / "new-module"
            challenge = module / "new-challenge"
            challenge.mkdir(parents=True)
            (dojo / "dojo.yml").write_text(json.dumps({"id": "test-dojo", "modules": [{"id": "new-module"}]}))
            resource = {"id": "new-challenge", "transfer": transfer}
            if location != "challenges":
                resource["type"] = "challenge"
            if location == "challenge.yml":
                (challenge / "challenge.yml").write_text(json.dumps({"transfer": resource.pop("transfer")}))
            (module / "module.yml").write_text(
                json.dumps({"challenges" if location == "challenges" else "resources": [resource]})
            )
            return subprocess.run([str(PARSER), str(dojo / "dojo.yml"), "--json"], text=True, capture_output=True)

    def test_preserves_transfer_in_update_payload(self):
        sources = [
            {"challenge": "old-challenge"},
            {"module": "old-module", "challenge": "old-challenge"},
            {"dojo": "old-dojo~01234567", "module": "old-module", "challenge": "old-challenge"},
        ]
        for source in sources:
            for location in ("resources", "challenges", "challenge.yml"):
                with self.subTest(source=source, location=location):
                    result = self.parse_challenge(source, location=location)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    module = json.loads(result.stdout)["modules"][0]
                    resource = module["resources"][0]
                    self.assertEqual(module["id"], "new-module")
                    self.assertEqual(resource["id"], "new-challenge")
                    self.assertEqual(resource["transfer"], source)

    def test_rejects_malformed_transfer(self):
        sources = [
            {},
            "old-module/old-challenge",
            {"challenge": "old-challenge", "modul": "old-module"},
            {"challenge": "old/challenge"},
            {"challenge": "x" * 33},
            {"module": "Old Module", "challenge": "old-challenge"},
            {"dojo": "invalid/dojo", "challenge": "old-challenge"},
            {"dojo": "x" * 129, "challenge": "old-challenge"},
        ]
        for source in sources:
            with self.subTest(source=source):
                result = self.parse_challenge(source)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, "")
                self.assertIn(".transfer", result.stderr)

    def test_omits_absent_transfer(self):
        result = self.parse_challenge(None)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("transfer", json.loads(result.stdout)["modules"][0]["resources"][0])


if __name__ == "__main__":
    unittest.main()
