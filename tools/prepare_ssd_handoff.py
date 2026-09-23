"""Back up MonarchSSD and recover a standalone release without changing either source.

Run using uv and the bundled Python runtime, which supplies Pillow. The destination
must be a new folder or this tool's existing resumable backup. Never formats disks.
"""

import argparse
from collections import Counter, defaultdict
import csv
import ctypes
from datetime import datetime
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import subprocess
import time
import xml.etree.ElementTree as ET

from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SSD = Path('/Volumes/MonarchSSD')
VAULT = Path('/Volumes/MediaVault')
PUBLIC = Path('data_release/publication_package')
NOTE = ('TGR1 capture times were reconstructed from deployment start and end times. '
        'The visible timestamp overlay retains the incorrect camera date and time.')


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def jpeg_payload(data):
    """Hash JPEG coding segments and entropy bytes, ignoring metadata segments."""
    if data[:2] != b'\xff\xd8':
        raise ValueError('Not a JPEG')
    result = hashlib.sha256(data[:2])
    offset = 2
    while offset < len(data):
        if data[offset] != 255:
            raise ValueError('Invalid JPEG segment')
        start = offset
        while data[offset] == 255:
            offset += 1
        marker = data[offset]
        offset += 1
        if marker in (0xDA, 0xD9):
            result.update(data[start:])
            return result.hexdigest()
        length = int.from_bytes(data[offset:offset + 2], 'big')
        if length < 2 or offset + length > len(data):
            raise ValueError('Invalid JPEG segment length')
        end = offset + length
        if not 0xE0 <= marker <= 0xEF and marker != 0xFE:
            result.update(data[start:end])
        offset = end
    raise ValueError('JPEG has no image data')


class Handoff:
    def __init__(self, destination, work):
        self.destination = destination
        self.work = work
        self.work.mkdir(parents=True, exist_ok=True)
        self.status_path = work / 'status.json'
        self.last_status = 0
        self.started = time.time()
        config = {'ssd': str(SSD), 'vault': str(VAULT), 'destination': str(destination)}
        marker = destination / '_verification/config.json'
        if destination.exists():
            if not marker.is_file() or json.loads(marker.read_text()) != config:
                raise ValueError('Destination is not this handoff backup')
        else:
            marker.parent.mkdir(parents=True)
            marker.write_text(json.dumps(config, indent=2) + '\n')
        self.db = sqlite3.connect(work / 'manifest.sqlite')
        self.db.row_factory = sqlite3.Row
        self.db.execute('''CREATE TABLE IF NOT EXISTS files (
            relative TEXT PRIMARY KEY, source TEXT NOT NULL, kind TEXT NOT NULL,
            collection TEXT NOT NULL, size INTEGER NOT NULL, mtime INTEGER NOT NULL,
            link_target TEXT, sha256 TEXT, state TEXT NOT NULL DEFAULT 'pending')''')
        self.db.execute('CREATE TABLE IF NOT EXISTS directories (relative TEXT PRIMARY KEY, source TEXT)')
        self.copy_metadata = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True).copyfile
        self.copy_metadata.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_uint32]
        self.copy_metadata.restype = ctypes.c_int
        self.get_xattr = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True).getxattr
        self.get_xattr.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p,
                                  ctypes.c_size_t, ctypes.c_uint32, ctypes.c_int]
        self.get_xattr.restype = ctypes.c_ssize_t

    def resource_fork(self, path):
        """Read a macOS resource fork even when Python lacks os.getxattr."""
        name = b'com.apple.ResourceFork'
        size = self.get_xattr(os.fsencode(path), name, None, 0, 0, 0)
        if size < 0:
            error = ctypes.get_errno()
            if error == errno.ENOATTR:
                return None
            raise OSError(error, os.strerror(error), str(path))
        buffer = ctypes.create_string_buffer(size)
        actual = self.get_xattr(os.fsencode(path), name, buffer, size, 0, 0)
        if actual < 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), str(path))
        if actual != size:
            raise ValueError(f'Resource fork changed while reading {path}')
        return buffer.raw[:actual]

    def status(self, phase, force=False, **details):
        if not force and time.time() - self.last_status < 30:
            return
        self.db.commit()
        value = {'phase': phase, 'updated': datetime.now().astimezone().isoformat(),
                 'elapsed_seconds': round(time.time() - self.started), **details}
        temporary = self.status_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value, indent=2) + '\n')
        temporary.replace(self.status_path)
        print(json.dumps(value), flush=True)
        self.last_status = time.time()

    def add(self, source, relative, collection):
        s = source.lstat()
        kind = 'symlink' if stat.S_ISLNK(s.st_mode) else 'file'
        if kind == 'file' and not stat.S_ISREG(s.st_mode):
            raise ValueError(f'Unsupported source type {source}')
        target = os.readlink(source) if kind == 'symlink' else None
        self.db.execute('INSERT INTO files(relative,source,kind,collection,size,mtime,link_target) VALUES (?,?,?,?,?,?,?)',
                        (str(relative), str(source), kind, collection, s.st_size, s.st_mtime_ns, target))

    def backup_tree(self, source):
        for base, dirs, files in os.walk(source, followlinks=False):
            base = Path(base)
            relative = base.relative_to(SSD)
            if relative == PUBLIC:
                dirs[:] = []
                continue
            self.db.execute('INSERT INTO directories VALUES (?,?)', (str(relative), str(base)))
            for name in list(dirs):
                path = base / name
                if path.is_symlink():
                    self.add(path, path.relative_to(SSD), 'backup')
                    dirs.remove(name)
            for name in files:
                self.add(base / name, relative / name, 'backup')

    def prepare_tgr1(self):
        mapping = read_csv(REPO / 'data/release_working/tgr1_photo_times.csv')
        folder = self.work / 'corrected_TGR1'
        complete = self.work / 'tgr1_verified.json'
        if complete.exists():
            for row in json.loads(complete.read_text())['files']:
                assert sha(folder / row['name']) == row['sha256']
            return folder
        folder.mkdir(exist_ok=True)
        tags = []
        self.status('reconstructing_tgr1', force=True, total=len(mapping))
        for number, row in enumerate(mapping, 1):
            source = VAULT / 'Masters' / Path(row['source_relative_path']).relative_to('raw')
            target = folder / row['image_filename']
            shutil.copy2(source, target)
            timestamp = datetime.fromisoformat(row['timestamp_recorded'])
            value = timestamp.strftime('%Y:%m:%d %H:%M:%S')
            fraction = f'{timestamp.microsecond // 1000:03d}'
            tags.append({'SourceFile': str(target), 'EXIF:DateTimeOriginal': value,
                         'EXIF:CreateDate': value, 'EXIF:ModifyDate': value,
                         'EXIF:SubSecTimeOriginal': fraction, 'EXIF:SubSecTimeDigitized': fraction,
                         'EXIF:SubSecTime': fraction, 'EXIF:ImageDescription': NOTE})
            self.status('reconstructing_tgr1', completed=number, total=len(mapping))
        metadata = self.work / 'tgr1_metadata.csv'
        with metadata.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(tags[0]))
            writer.writeheader()
            writer.writerows(tags)
        paths = self.work / 'tgr1_paths.txt'
        paths.write_text('\n'.join(row['SourceFile'] for row in tags) + '\n')
        subprocess.run(['exiftool', '-overwrite_original', '-P', '-csv=' + str(metadata), '-@', str(paths)], check=True)
        corrected = json.loads(subprocess.check_output([
            'exiftool', '-json', '-DateTimeOriginal', '-CreateDate', '-ModifyDate',
            '-SubSecTimeOriginal', '-SubSecTimeDigitized', '-SubSecTime', '-ImageDescription',
            '-@', str(paths)], text=True))
        observed = {row['SourceFile']: row for row in corrected}
        checks = []
        for number, (row, tag) in enumerate(zip(mapping, tags), 1):
            source = VAULT / 'Masters' / Path(row['source_relative_path']).relative_to('raw')
            target = folder / row['image_filename']
            before, after = source.read_bytes(), target.read_bytes()
            assert jpeg_payload(before) == jpeg_payload(after), target
            with Image.open(io.BytesIO(after)) as image:
                image.load()
            for key, value in tag.items():
                if key != 'SourceFile':
                    assert str(observed[str(target)][key.split(':', 1)[1]]) == value, (target, key)
            checks.append({'name': target.name, 'sha256': hashlib.sha256(after).hexdigest(),
                           'original_sha256': hashlib.sha256(before).hexdigest()})
            self.status('checking_tgr1_corrections', completed=number, total=len(mapping))
        complete.write_text(json.dumps({'files': checks, 'pixels_and_coding_unchanged': True,
                                       'decoded_images': len(checks), 'EXIF_matches_saved_mapping': True}, indent=2))
        return folder

    def plan(self):
        marker = self.work / 'plan_complete.json'
        if marker.exists():
            return json.loads(marker.read_text())
        if self.db.execute('SELECT count(*) FROM files').fetchone()[0]:
            raise ValueError('Incomplete plan. Inspect the local manifest before rebuilding it.')
        tgr = self.prepare_tgr1()
        for name in ['Pictures', 'monarch-knowledge-base', 'data_release']:
            self.backup_tree(SSD / name)
        for p in SSD.iterdir():
            if p.is_symlink() or (p.is_file() and p.name == '.DS_Store'):
                self.add(p, p.relative_to(SSD), 'backup')
        root = SSD / PUBLIC
        index = read_csv(root / 'photo_index.csv')
        if len(index) != 226830 or len({r['relative_path'] for r in index}) != 226830:
            raise ValueError('Unexpected release index')
        original = defaultdict(list)
        for row in read_csv(VAULT / 'Masters/VSFB_2025_Deployment_Review/metadata/manifest.csv'):
            original[Path(row['destination_relative']).name].append(row)
        self.db.execute('INSERT INTO directories VALUES (?,NULL)', (str(PUBLIC),))
        self.db.execute('INSERT INTO directories VALUES (?,NULL)', (str(PUBLIC / 'photos'),))
        for dep in {r['deployment_id'] for r in index}:
            self.db.execute('INSERT INTO directories VALUES (?,NULL)', (str(PUBLIC / 'photos' / dep),))
        for row in index:
            relative = Path(row['relative_path'])
            if relative.is_absolute() or '..' in relative.parts or relative.parts != ('photos', row['deployment_id'], row['image_filename']):
                raise ValueError('Unsafe index path')
            source = root / relative
            if not source.is_file():
                dep, name = row['deployment_id'], row['image_filename']
                choices = [tgr / name] if dep == 'TGR1' else [
                    VAULT / 'Masters/Camelot_Photos' / dep / name,
                    VAULT / 'Masters/VSFB_2025_Deployment_Review' / dep / name]
                matches = [p for p in choices if p.is_file()]
                if not matches:
                    matches = [VAULT / 'Masters/VSFB 2025' / r['source_relative']
                               for r in original[name] if (VAULT / 'Masters/VSFB 2025' / r['source_relative']).is_file()]
                if len(matches) != 1:
                    raise ValueError(f'Ambiguous or absent source {relative}')
                source = matches[0]
            if source.is_symlink() or not source.stat().st_size:
                raise ValueError(f'Invalid photo source {source}')
            self.add(source, PUBLIC / relative, 'release_photo')
        for name in ['deployments.csv', 'classifications.csv', 'photo_index.csv', 'temperature_measurements.csv',
                     'wind_measurements.csv', 'data_dictionary.csv', 'metadata.xml']:
            self.add(root / name, PUBLIC / name, 'release_table')
        self.db.commit()
        summary = dict(self.db.execute("SELECT count(*) files, sum(size) bytes FROM files WHERE kind='file'").fetchone())
        if shutil.disk_usage(self.destination).free < summary['bytes'] * 1.1:
            raise ValueError('Insufficient free space')
        marker.write_text(json.dumps(summary, indent=2))
        self.status('plan_complete', force=True, **summary)
        return summary

    def copy(self, summary):
        for row in self.db.execute('SELECT * FROM directories ORDER BY length(relative)'):
            (self.destination / row['relative']).mkdir(parents=True, exist_ok=True)
        progress = dict(self.db.execute("SELECT count(*) files, coalesce(sum(size),0) bytes FROM files WHERE kind='file' AND state IN ('copied','verified')").fetchone())
        for row in self.db.execute("SELECT * FROM files ORDER BY CASE WHEN source LIKE '/Volumes/MonarchSSD/%' THEN 0 ELSE 1 END, source").fetchall():
            source = Path(row['source'])
            target = self.destination / row['relative']
            if row['state'] in ('copied', 'verified'):
                continue
            if row['kind'] == 'symlink':
                if target.is_symlink():
                    assert os.readlink(target) == row['link_target']
                elif target.exists():
                    raise ValueError(f'Unexpected target {target}')
                else:
                    target.symlink_to(row['link_target'])
                self.db.execute("UPDATE files SET state='copied' WHERE relative=?", (row['relative'],))
                continue
            before = source.stat()
            if (before.st_size, before.st_mtime_ns) != (row['size'], row['mtime']):
                raise ValueError(f'Source changed {source}')
            if target.is_symlink():
                raise ValueError(f'Unexpected target link {target}')
            if target.exists():
                digest = sha(source)
                if sha(target) != digest:
                    raise ValueError(f'Existing file differs {target}')
            else:
                temporary = target.with_name('.' + target.name + '.handoff-partial')
                digest_object = hashlib.sha256()
                with source.open('rb') as incoming, temporary.open('wb') as output:
                    while block := incoming.read(8 * 1024 * 1024):
                        digest_object.update(block)
                        output.write(block)
                if self.copy_metadata(os.fsencode(source), os.fsencode(temporary), None, 7) != 0:
                    error = ctypes.get_errno()
                    raise OSError(error, os.strerror(error), str(source))
                temporary.replace(target)
                digest = digest_object.hexdigest()
            after = source.stat()
            assert (after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns), source
            self.db.execute("UPDATE files SET state='copied',sha256=? WHERE relative=?", (digest, row['relative']))
            progress['files'] += 1
            progress['bytes'] += row['size']
            self.status('copying', completed=progress['files'], total=summary['files'],
                        copied_bytes=progress['bytes'], total_bytes=summary['bytes'], current=row['relative'])
        self.db.commit()
        subprocess.run(['sync'], check=True)
        self.status('copy_complete', force=True, **progress)

    def verify(self, summary):
        progress = dict(self.db.execute("SELECT count(*) files, coalesce(sum(size),0) bytes FROM files WHERE kind='file' AND state='verified'").fetchone())
        for row in self.db.execute('SELECT * FROM files ORDER BY relative').fetchall():
            source, target = Path(row['source']), self.destination / row['relative']
            if row['kind'] == 'symlink':
                assert target.is_symlink() and os.readlink(target) == row['link_target'], target
                self.db.execute("UPDATE files SET state='verified' WHERE relative=?", (row['relative'],))
                continue
            if row['state'] == 'verified':
                continue
            assert target.is_file() and not target.is_symlink(), target
            assert target.stat().st_size == row['size'], target
            source_stat = source.stat()
            assert (source_stat.st_size, source_stat.st_mtime_ns) == (row['size'], row['mtime']), source
            if row['collection'] == 'release_photo':
                data = target.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                with Image.open(io.BytesIO(data)) as image:
                    assert image.format == 'JPEG' and image.width > 0 and image.height > 0
                    image.verify()
            else:
                digest = sha(target)
            assert digest == row['sha256'], f'Checksum mismatch {target}'
            assert self.resource_fork(source) == self.resource_fork(target), (target, 'com.apple.ResourceFork')
            self.db.execute("UPDATE files SET state='verified' WHERE relative=?", (row['relative'],))
            progress['files'] += 1
            progress['bytes'] += row['size']
            self.status('verifying', completed=progress['files'], total=summary['files'],
                        verified_bytes=progress['bytes'], total_bytes=summary['bytes'], current=row['relative'])
        self.db.commit()
        # Preserve directory metadata after all writes into the directories finish.
        for row in self.db.execute('SELECT * FROM directories WHERE source IS NOT NULL ORDER BY length(relative) DESC'):
            if self.copy_metadata(os.fsencode(row['source']), os.fsencode(self.destination / row['relative']), None, 7) != 0:
                error = ctypes.get_errno()
                raise OSError(error, os.strerror(error), row['source'])
        self.status('checksum_verification_complete', force=True, **progress)

    def final_checks(self):
        root = self.destination / PUBLIC
        index = read_csv(root / 'photo_index.csv')
        photos = {r['relative_path'] for r in index}
        allowed = photos | {'deployments.csv', 'classifications.csv', 'photo_index.csv',
                            'temperature_measurements.csv', 'wind_measurements.csv', 'data_dictionary.csv', 'metadata.xml'}
        found = set()
        for base, dirs, files in os.walk(root, followlinks=False):
            for name in dirs + files:
                assert not (Path(base) / name).is_symlink(), Path(base) / name
            found.update(str((Path(base) / name).relative_to(root)) for name in files)
        assert found == allowed, (found - allowed, allowed - found)
        assert len(photos) == len(index) == 226830
        assert len({(r['deployment_id'], r['timestamp']) for r in index}) == len(index)
        assert not any(Path(p).stem.endswith('_02') for p in photos)
        keys = {(r['deployment_id'], r['image_filename']) for r in index}
        deploys = {r['deployment_id'] for r in read_csv(root / 'deployments.csv')}
        assert len(deploys) == 28 and {r['deployment_id'] for r in index} == deploys
        expected_rows = {'deployments.csv': 28, 'classifications.csv': 3713,
                         'temperature_measurements.csv': 56066, 'wind_measurements.csv': 757260,
                         'photo_index.csv': 226830, 'data_dictionary.csv': 69}
        for name, count in expected_rows.items():
            records = read_csv(root / name)
            assert len(records) == count
            assert all(k is not None and v is not None and v != '' for r in records for k, v in r.items())
            if name in ('classifications.csv', 'temperature_measurements.csv'):
                assert all((r['deployment_id'], r['image_filename']) in keys for r in records)
            if name != 'data_dictionary.csv':
                assert all(r['deployment_id'] in deploys for r in records)
        xml = ET.parse(root / 'metadata.xml')
        pending = [e.text for e in xml.iter() if e.text and ('REVIEW_REQUIRED' in e.text or e.text == 'Unpublished material')]
        # Ensure all backed-up source paths still have the original inventories.
        planned = {row['relative'] for row in self.db.execute("SELECT relative FROM files WHERE collection='backup'")}
        observed = set()
        for name in ['Pictures', 'monarch-knowledge-base', 'data_release']:
            for base, dirs, files in os.walk(SSD / name, followlinks=False):
                base = Path(base)
                if base.relative_to(SSD) == PUBLIC:
                    dirs[:] = []
                    continue
                observed.update(str((base / n).relative_to(SSD)) for n in dirs + files if (base / n).is_symlink() or (base / n).is_file())
        observed.update(p.name for p in SSD.iterdir() if p.is_symlink() or (p.is_file() and p.name == '.DS_Store'))
        assert observed == planned, 'Source inventory changed during backup'
        assert self.db.execute("SELECT count(*) FROM files WHERE state!='verified'").fetchone()[0] == 0
        counts = [dict(row) for row in self.db.execute('SELECT collection,kind,count(*) files,sum(size) bytes FROM files GROUP BY collection,kind')]
        report = {'completed': datetime.now().astimezone().isoformat(), 'backup': str(self.destination),
                  'release': str(root), 'counts': counts, 'release_photos': len(photos), 'deployments': len(deploys),
                  'release_symlinks': 0, 'all_file_content_checksums_passed': True,
                  'release_index_exact_match': True, 'JPEG_structural_checks': len(photos),
                  'TGR1_full_decode_and_saved_EXIF_checks': 2973, 'pending_publication_fields': pending,
                  'formatting_performed': False, 'ready_for_formatting_decision': True,
                  'limitations': 'JPEG structural verification is not full pixel decoding for non-TGR1 photographs. Backup symlinks preserve the original targets and do not copy data stored elsewhere. Publication date and DOI remain pending.'}
        verification = self.destination / '_verification'
        destination_db = sqlite3.connect(verification / 'manifest.sqlite')
        self.db.backup(destination_db)
        destination_db.close()
        shutil.copyfile(self.work / 'tgr1_verified.json', verification / 'tgr1_verified.json')
        (verification / 'complete.json').write_text(json.dumps(report, indent=2) + '\n')
        (self.work / 'complete.json').write_text(json.dumps(report, indent=2) + '\n')
        subprocess.run(['sync'], check=True)
        self.status('complete', force=True, report=str(verification / 'complete.json'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    if args.destination.parent != VAULT or not SSD.is_mount() or not VAULT.is_mount():
        raise ValueError('Both source drives must be mounted and the destination must be directly on MediaVault')
    job = Handoff(args.destination, args.work)
    try:
        summary = job.plan()
        job.copy(summary)
        job.verify(summary)
        job.final_checks()
    except BaseException as error:
        job.status('error', force=True, error=repr(error))
        raise


if __name__ == '__main__':
    main()
