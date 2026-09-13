import tempfile
import unittest
from pathlib import Path

from finalize_reviewed_photos import apply_moves, digest


class PhotoMoveTests(unittest.TestCase):
    def test_move_preserves_bytes_and_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, new = root / "old.JPG", root / "new.JPG"
            old.write_bytes(b"distinct photograph bytes")
            plan = [{"old_path": old.name, "new_path": new.name, "sha256": digest(old)}]
            apply_moves(root, plan)
            apply_moves(root, plan)
            self.assertFalse(old.exists())
            self.assertEqual(new.read_bytes(), b"distinct photograph bytes")

    def test_collision_does_not_overwrite_or_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, new = root / "old.JPG", root / "new.JPG"
            old.write_bytes(b"one")
            new.write_bytes(b"two")
            with self.assertRaises(ValueError):
                apply_moves(root, [{"old_path": old.name, "new_path": new.name, "sha256": digest(old)}])
            self.assertEqual(old.read_bytes(), b"one")
            self.assertEqual(new.read_bytes(), b"two")

    def test_interrupted_link_resumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old, new = root / "old.JPG", root / "new.JPG"
            old.write_bytes(b"one")
            new.hardlink_to(old)
            apply_moves(root, [{"old_path": old.name, "new_path": new.name, "sha256": digest(old)}])
            self.assertFalse(old.exists())
            self.assertEqual(new.read_bytes(), b"one")


if __name__ == "__main__":
    unittest.main()
