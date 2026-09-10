"""Small end-to-end checks for export safety and unattended operation."""

from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from PIL import Image

import export_season_photos as export


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "raw"
        self.camera = self.source / "CAM"
        self.camera.mkdir(parents=True)
        self.destination = self.root / "export"
        self.gpkg = self.root / "cameras.gpkg"
        with closing(sqlite3.connect(self.gpkg)) as db, db:
            db.execute("CREATE TABLE cameras (ID TEXT, deployment_ID TEXT)")
            db.execute("INSERT INTO cameras VALUES ('CAM','SITE_1')")
        self.photo("unique.JPG", "2024:11:07 12:30:01")
        self.photo("duplicate_a.JPG", "2024:11:07 12:40:01")
        self.photo("duplicate_b.JPG", "2024:11:07 12:40:01")
        (self.camera / "bad.JPG").write_bytes(bytes(1024))
        (self.camera / "video.MP4").write_bytes(b"video fixture")
        self.original_hashes = self.hashes()

    def photo(self, name, timestamp):
        exif = Image.Exif()
        exif[34665] = {36867: timestamp}
        Image.new("RGB", (8, 8), (30, 60, 90)).save(self.camera / name, exif=exif)

    def hashes(self):
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.camera.iterdir()}

    def test_run_preserves_every_file_and_resumes_without_overwrite(self):
        export.run_export(self.source, self.gpkg, self.destination)
        with closing(export.connect(self.destination)) as db, db:
            rows = db.execute("SELECT * FROM files").fetchall()
            self.assertEqual(len(rows), 5)
            self.assertEqual(sum(r["note"] == "duplicate_capture_time" for r in rows), 2)
            for row in rows:
                self.assertEqual(row["status"], "copied")
                self.assertEqual((self.source / row["source_relative"]).read_bytes(),
                                 (self.destination / row["destination_relative"]).read_bytes())
        target = self.destination / "SITE_1/SITE_1_20241107123001.JPG"
        inode = target.stat().st_ino
        export.run_export(self.source, self.gpkg, self.destination)
        self.assertEqual(target.stat().st_ino, inode)
        target.write_bytes(b"manual edit")
        with closing(export.connect(self.destination)) as db, db:
            db.execute("UPDATE files SET status='pending' WHERE source_relative='CAM/unique.JPG'")
        with self.assertRaises(RuntimeError):
            export.run_export(self.source, self.gpkg, self.destination)
        self.assertEqual(target.read_bytes(), b"manual edit")
        self.assertEqual(self.hashes(), self.original_hashes)

    def test_interrupted_inventory_resumes(self):
        with patch.object(export, "export_manifest", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                export.run_export(self.source, self.gpkg, self.destination)
        export.run_export(self.source, self.gpkg, self.destination)
        with closing(export.connect(self.destination)) as db, db:
            self.assertEqual(db.execute("SELECT count(*) FROM files WHERE status='copied'").fetchone()[0], 5)
        self.assertEqual(self.hashes(), self.original_hashes)

    def test_interrupted_copy_resumes(self):
        export.plan(self.source, self.gpkg, self.destination)
        export.copy_files(self.destination, limit=2)
        export.run_export(self.source, self.gpkg, self.destination)
        with closing(export.connect(self.destination)) as db, db:
            self.assertEqual(db.execute("SELECT count(*) FROM files WHERE status='copied'").fetchone()[0], 5)

    def test_background_command_finishes_without_supervision(self):
        result = subprocess.run([sys.executable, str(Path(export.__file__)), "run",
                                 str(self.source), str(self.gpkg), str(self.destination), "--background"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        status_path = self.destination.with_name("export.status.json")
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if status_path.exists():
                status = json.loads(status_path.read_text())
                if status["phase"] in {"completed", "failed"}:
                    self.assertEqual(status["phase"], "completed", status)
                    self.assertEqual(status["counts"], {"copied": 5})
                    return
            time.sleep(0.1)
        self.fail("Background job did not complete")

    def test_copy_fallback_and_space_check(self):
        with patch.object(export, "choose_copy_method", return_value="copy"):
            export.run_export(self.source, self.gpkg, self.destination)
        self.assertEqual(self.hashes(), self.original_hashes)
        second = self.root / "no_space"
        with patch.object(export, "choose_copy_method", return_value="copy"), \
                patch.object(export.shutil, "disk_usage", return_value=export.shutil._ntuple_diskusage(1, 1, 0)):
            with self.assertRaisesRegex(ValueError, "Not enough free space"):
                export.run_export(self.source, self.gpkg, second)
        self.assertFalse(list((second / "SITE_1").rglob("*.JPG")))


if __name__ == "__main__":
    unittest.main()
