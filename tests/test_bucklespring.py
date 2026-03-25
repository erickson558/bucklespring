import json
import tempfile
import time
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import bucklespring as app


class FakeKeyboardEvent:
    def __init__(self, name: str | None, scan_code: int | None, event_type: str) -> None:
        self.name = name
        self.scan_code = scan_code
        self.event_type = event_type


class SoundEngineTests(unittest.TestCase):
    def make_engine(
        self,
        *,
        mixer_ready: bool = False,
        sound_files: dict[str, dict[str, Path]] | None = None,
        use_real_load_settings: bool = False,
    ) -> app.SoundEngine:
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(app.SoundEngine, "_setup_mixer", lambda self: setattr(self, "mixer_ready", mixer_ready)))
        stack.enter_context(
            patch.object(
                app.SoundEngine,
                "_discover_sound_files",
                lambda self, sound_files=sound_files: dict(sound_files or {}),
            )
        )
        if not use_real_load_settings:
            stack.enter_context(patch.object(app.SoundEngine, "load_settings", lambda self: None))
        stack.enter_context(patch("bucklespring.keyboard.unhook_all", lambda: None))
        stack.enter_context(patch("bucklespring.keyboard.clear_all_hotkeys", lambda: None))
        stack.enter_context(patch("bucklespring.pygame.mixer.quit", lambda: None))
        return app.SoundEngine()

    def test_stray_release_does_not_enqueue_audio(self) -> None:
        engine = self.make_engine()
        observed: list[app.KeyEventSnapshot] = []
        engine.add_event_observer(observed.append)

        engine.handle_key_event(FakeKeyboardEvent("a", 30, "up"))

        self.assertEqual(len(observed), 1)
        self.assertTrue(engine.audio_queue.empty())
        engine.shutdown()

    def test_audio_worker_survives_sound_load_error(self) -> None:
        with patch("bucklespring.pygame.mixer.Sound", side_effect=RuntimeError("broken wav")):
            engine = self.make_engine(mixer_ready=True, sound_files={"ff": {"press": Path("broken.wav")}})
            engine.audio_queue.put(app.KeyEventSnapshot(name="a", scan_code=30, event_type="down"))
            time.sleep(0.2)

            self.assertTrue(engine.audio_worker.is_alive())
            self.assertIn("broken.wav", engine.last_audio_error or "")
            engine.shutdown()

    def test_save_settings_uses_fallback_path_when_primary_fails(self) -> None:
        engine = self.make_engine()

        with tempfile.TemporaryDirectory() as tmpdir:
            primary = Path(tmpdir) / "read-only" / "config.json"
            fallback = Path(tmpdir) / "local" / "config.json"
            original_write_text = Path.write_text

            def fake_write_text(path: Path, content: str, encoding: str = "utf-8") -> int:
                if path == primary:
                    raise OSError("read only target")
                path.parent.mkdir(parents=True, exist_ok=True)
                return original_write_text(path, content, encoding=encoding)

            engine.config_path = primary
            with patch("bucklespring.iter_config_paths", return_value=(primary, fallback)):
                with patch.object(Path, "write_text", autospec=True, side_effect=fake_write_text):
                    saved_path = engine.save_settings()

            self.assertEqual(saved_path, fallback)
            self.assertEqual(engine.config_path, fallback)
            self.assertEqual(json.loads(fallback.read_text(encoding="utf-8"))["version"], app.APP_VERSION)
            engine.shutdown()

    def test_load_settings_skips_corrupted_primary_and_uses_valid_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            primary = Path(tmpdir) / "broken" / "config.json"
            fallback = Path(tmpdir) / "local" / "config.json"
            primary.parent.mkdir(parents=True, exist_ok=True)
            fallback.parent.mkdir(parents=True, exist_ok=True)
            primary.write_text("{invalid json", encoding="utf-8")
            fallback.write_text(json.dumps({"volume": 0.35, "enabled": False, "language": "es"}), encoding="utf-8")

            with patch("bucklespring.iter_config_paths", return_value=(primary, fallback)):
                engine = self.make_engine(use_real_load_settings=True)

            self.assertEqual(engine.config_path, fallback)
            self.assertEqual(engine.volume, 0.35)
            self.assertFalse(engine.enabled)
            self.assertEqual(engine.language, "es")
            engine.shutdown()


if __name__ == "__main__":
    unittest.main()
