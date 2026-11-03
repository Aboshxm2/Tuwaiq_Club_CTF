"""CTFd 3.8.7 integration checks; SQLite only, no Docker daemon or production."""
import importlib
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from CTFd import create_app
from CTFd.config import TestingConfig
from CTFd.cache import cache
from CTFd.models import Challenges, ChallengeFiles, Flags, Hints, Solves, Tags, Teams, Users, db
from CTFd.utils import set_config

# Import the real Whale model without its Linux-only scheduler/socket startup.
import CTFd.plugins
whale_package = types.ModuleType("CTFd.plugins.ctfd-whale")
whale_package.__path__ = [str(Path(CTFd.plugins.__file__).parent / "ctfd-whale")]
sys.modules["CTFd.plugins.ctfd-whale"] = whale_package
importlib.import_module("CTFd.plugins.ctfd-whale.models")

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("curated_import", ROOT / "ctfd-platform/scripts/import_curated.py")
importer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(importer)


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

        class Config(TestingConfig):
            SAFE_MODE = False
            SQLALCHEMY_DATABASE_URI = "sqlite://"
            SERVER_NAME = "localhost.localdomain"
            UPLOAD_FOLDER = self.temp.name

        plugins = ["challenges", "ctfd-rounds", "dynamic_challenges", "flags"]
        with patch("CTFd.plugins.get_plugin_names", return_value=plugins):
            self.app = create_app(Config)
        self.context = self.app.app_context()
        self.context.push()
        db.session().expire_on_commit = False
        self.addCleanup(self.context.pop)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(cache.clear)
        set_config("setup", True)
        set_config("user_mode", "teams")
        self.models = importlib.import_module("CTFd.plugins.ctfd-rounds.models")
        self.catalog = importlib.import_module("CTFd.plugins.ctfd-rounds.curated_catalog")
        self.number = "441234567890"  # Test-only number; no real OSINT answer in source.

    def stage(self, apply=True):
        importer.stage("Test pack", self.number, apply=apply)

    def test_dry_run_and_pause_preflight_write_nothing(self):
        self.stage(apply=False)
        self.assertEqual(Challenges.query.count(), 0)
        with self.assertRaisesRegex(RuntimeError, "Pause CTF"):
            self.stage()
        self.assertEqual(Challenges.query.count(), 0)

    def test_missing_number_preflight_write_nothing(self):
        set_config("paused", True)
        with self.assertRaisesRegex(RuntimeError, "CURATED_OSINT_PHONE"):
            importer.stage("Test pack", "", apply=True)
        self.assertEqual(Challenges.query.count(), 0)

    def test_stage_repeat_and_preserve_legacy(self):
        set_config("paused", True)
        legacy = Challenges(name="Legacy challenge", value=20, state="visible", type="standard")
        db.session.add(legacy)
        db.session.commit()
        self.stage()
        self.assertEqual(Challenges.query.count(), 22)
        pack = Challenges.query.filter(Challenges.name != "Legacy challenge").all()
        self.assertTrue(all(c.state == "hidden" for c in pack))
        self.assertEqual(legacy.state, "visible")
        rnd = self.models.Rounds.query.filter_by(name="Test pack").one()
        self.assertEqual((rnd.state, rnd.duration, len(rnd.challenge_ids)), ("pending",10800,5))
        self.assertEqual(self.models.ChallengeMeta.query.count(), 13)
        self.assertEqual(ChallengeFiles.query.count(), 1)
        self.assertEqual(Flags.query.count(), 1)
        self.assertEqual(Flags.query.one().content, "TAIBAH{" + self.number + "}")
        hint_count = Hints.query.count()
        self.stage()
        self.assertEqual(Challenges.query.count(), 22)
        self.assertEqual(Hints.query.count(), hint_count)
        self.assertEqual(ChallengeFiles.query.count(), 1)
        self.assertEqual(len(rnd.challenge_ids), 5)

    def test_started_pack_rejected(self):
        set_config("paused", True)
        self.stage()
        rnd = self.models.Rounds.query.filter_by(name="Test pack").one()
        rnd.state = "running"
        db.session.commit()
        with self.assertRaisesRegex(RuntimeError, "has started"):
            self.stage()

    def test_generated_instance_rejected(self):
        set_config("paused", True)
        self.stage()
        meta = self.models.ChallengeMeta.query.first()
        db.session.add(self.models.PersonalFlags(account_id=1, challenge_id=meta.challenge_id, flag="TAIBAH{test}",token="test"))
        db.session.commit()
        with self.assertRaisesRegex(RuntimeError, "participant activity"):
            self.stage()


if __name__ == "__main__":
    unittest.main()
