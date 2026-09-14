"""Regression checks for season-specific release names and source preservation."""

import os
from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from prepare_data_release import release_deployment_id, release_photo_path, stage_photos


class ReleaseDeploymentIds(unittest.TestCase):
    def test_seasons_and_collision_suffix(self):
        self.assertEqual(release_deployment_id("2023-2024", "SC12"), "SC12")
        self.assertEqual(release_deployment_id("2024-2025", "SC12"), "SC13")
        self.assertEqual(release_deployment_id("2024-2025", "SC13"), "SC13")
        self.assertEqual(str(release_photo_path("2024-2025", "SC12/SC12_20241103010000_02.JPG")),
                         "SC13/SC13_20241103010000_02.JPG")
        self.assertEqual(str(release_photo_path("2023-2024", "SC12/SC12_20240103010000.JPG")),
                         "SC12/SC12_20240103010000.JPG")

    def test_staging_preserves_source_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "VSFB_2025_Deployment_Review/SC12/SC12_20250101000000.JPG"
            original.parent.mkdir(parents=True)
            original.write_bytes(b"unchanged image content")
            before = original.stat()
            package = root / "publication_package"
            old = package / "photos/2024-2025/SC12"
            old.parent.mkdir(parents=True)
            old.symlink_to(original.parent, target_is_directory=True)
            dep = pd.DataFrame([{"season": "2024-2025", "deployment_id": "SC13"}])
            photos = pd.DataFrame([{"season": "2024-2025", "deployment_id": "SC13",
                                    "image_filename": "SC13_20250101000000.JPG",
                                    "relative_path": "photos/2024-2025/SC13/SC13_20250101000000.JPG"}])
            stage_photos(root, package, dep, photos)
            stage_photos(root, package, dep, photos)
            new = package / photos.iloc[0].relative_path
            self.assertTrue(os.path.samefile(original, new))
            self.assertEqual((original.stat().st_size, original.stat().st_mtime_ns),
                             (before.st_size, before.st_mtime_ns))
            self.assertFalse(old.is_symlink())
            self.assertEqual(original.read_bytes(), b"unchanged image content")
            # A colliding destination must not be silently accepted or overwritten.
            new.unlink()
            new.write_bytes(b"unrelated data")
            with self.assertRaisesRegex(ValueError, "differs from original"):
                stage_photos(root, package, dep, photos)
            self.assertEqual(new.read_bytes(), b"unrelated data")


if __name__ == "__main__":
    unittest.main()
