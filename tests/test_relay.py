import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import relay


class RelayCliTests(unittest.TestCase):
    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project"
            with mock.patch.object(relay, "home_agents", return_value=Path(directory) / "home"):
                self.assertEqual(relay.init_project(target, "lite", False, True, True), 0)
            self.assertFalse(target.exists())

    def test_init_preserves_existing_asset_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            agents = target / "AGENTS.md"
            agents.write_text("local\n", encoding="utf-8")
            with mock.patch.object(relay, "home_agents", return_value=Path(directory) / "home"):
                self.assertEqual(relay.init_project(target, "lite", False, False, False), 2)
            self.assertEqual(agents.read_text(encoding="utf-8"), "local\n")
            self.assertFalse((target / ".relay.json").exists())

    def test_non_file_asset_is_reported_as_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "AGENTS.md").mkdir()
            self.assertEqual(relay.init_project(target, "lite", False, False, False), 2)

    def test_repeated_init_preserves_metadata_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "project"
            self.assertEqual(relay.init_project(target, "standard", False, False, False), 0)
            metadata = target / ".agents" / "relay.json"
            original = metadata.read_text(encoding="utf-8")
            self.assertEqual(relay.init_project(target, "standard", False, False, False), 0)
            self.assertEqual(metadata.read_text(encoding="utf-8"), original)

    def test_invalid_registry_is_preserved_and_blocks_init(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            agents_home = root / "home"
            registry = agents_home / "custodian" / "projects.json"
            registry.parent.mkdir(parents=True)
            registry.write_text("not-json\n", encoding="utf-8")
            target = root / "project"
            with mock.patch.object(relay, "home_agents", return_value=agents_home):
                self.assertEqual(relay.init_project(target, "lite", False, False, True), 2)
            self.assertFalse(target.exists())
            self.assertEqual(registry.read_text(encoding="utf-8"), "not-json\n")

    def test_audit_detects_missing_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            metadata = target / ".relay.json"
            metadata.write_text(json.dumps({"version": relay.VERSION, "profile": "lite"}), encoding="utf-8")
            self.assertEqual(relay.audit(target), 1)

    def test_init_then_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            with mock.patch.object(relay, "home_agents", return_value=Path(directory) / "home"):
                self.assertEqual(relay.init_project(target, "lite", False, False, False), 0)
            self.assertEqual(relay.audit(target), 0)

    def test_standard_and_heavy_profiles_are_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(relay, "home_agents", return_value=root / "home"):
                self.assertEqual(relay.init_project(root / "standard", "standard", False, False, False), 0)
                self.assertEqual(relay.init_project(root / "heavy", "heavy", False, False, False), 0)
            self.assertEqual(relay.audit(root / "standard"), 0)
            self.assertEqual(relay.audit(root / "heavy"), 0)

    def test_sweep_updates_registry_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            agents_home = root / "home"
            with mock.patch.object(relay, "home_agents", return_value=agents_home):
                self.assertEqual(relay.init_project(project, "lite", False, False, True), 0)
                report = root / "report.md"
                self.assertEqual(relay.sweep(False, report), 0)
            self.assertIn("healthy", report.read_text(encoding="utf-8"))
            registry = json.loads((agents_home / "custodian" / "projects.json").read_text(encoding="utf-8"))
            self.assertEqual(registry[0]["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
