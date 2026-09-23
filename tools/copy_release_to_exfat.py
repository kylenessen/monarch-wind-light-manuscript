"""Copy the reviewed release to an already formatted SSD, without full checksums."""

import argparse
import csv
from datetime import datetime
import json
import os
from pathlib import Path
import plistlib
import subprocess

SOURCE = Path('/Volumes/MediaVault/MonarchSSD_backup_2026-09-22/data_release/publication_package')
SSD = Path('/Volumes/MonarchSSD')
WORK = Path('/Users/kylenessen/.codex/task-data/monarch-exfat-delivery-20260923')
SUPPORT = {'deployments.csv', 'classifications.csv', 'photo_index.csv',
           'temperature_measurements.csv', 'wind_measurements.csv',
           'data_dictionary.csv', 'metadata.xml'}


def inventory(root, remove_finder_files=False):
    files, directories = {}, set()
    for base, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            path = Path(base) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise ValueError(f'Symlink in release {path}')
            if path.is_dir():
                directories.add(relative)
            elif path.is_file():
                if name == '.DS_Store' or name.startswith('._'):
                    if remove_finder_files:
                        path.unlink()
                    continue
                files[relative] = path.stat().st_size
            else:
                raise ValueError(f'Unsupported entry {path}')
    return files, directories


def status(phase, **details):
    report = {'phase': phase, 'updated': datetime.now().astimezone().isoformat(), **details}
    temporary = WORK / 'status.tmp'
    temporary.write_text(json.dumps(report, indent=2) + '\n')
    temporary.replace(WORK / 'status.json')
    print(json.dumps(report), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    if not Path('/Volumes/MediaVault').is_mount() or not SSD.is_mount():
        raise ValueError('Both drives must be mounted')
    with (SOURCE / 'photo_index.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    expected = {r['relative_path'] for r in rows} | SUPPORT
    expected_dirs = {'photos'} | {'photos/' + r['deployment_id'] for r in rows}
    assert len(rows) == 226830 and len(expected) == 226837 and len(expected_dirs) == 29
    assert len({(r['deployment_id'], r['timestamp']) for r in rows}) == len(rows)
    assert not any(Path(r['relative_path']).stem.endswith('_02') for r in rows)
    files, directories = inventory(SOURCE)
    assert set(files) == expected and directories == expected_dirs
    assert all(size > 0 for size in files.values())
    summary = {'files': len(files), 'photos': len(rows), 'deployments': 28,
               'bytes': sum(files.values()), 'source': str(SOURCE)}
    if args.check_only:
        status('source_inventory_checked', **summary)
        return
    disk = plistlib.loads(subprocess.check_output(['diskutil', 'info', '-plist', str(SSD)]))
    assert disk['FilesystemType'].lower() == 'exfat' and not disk['Internal']
    target = SSD / 'publication_package'
    (WORK / 'source-inventory.json').write_text(json.dumps(files))
    status('copying', destination=str(target), **summary)
    with (WORK / 'rsync.log').open('a') as log:
        subprocess.run(['/usr/bin/rsync', '-rt', '--stats', '--exclude=.DS_Store',
                        '--exclude=._*', str(SOURCE), str(SSD) + '/'],
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    subprocess.run(['sync'], check=True)
    status('checking_inventory', destination=str(target), **summary)
    found, found_dirs = inventory(target, remove_finder_files=True)
    assert found == files, 'Destination file paths or sizes differ from source inventory'
    assert found_dirs == expected_dirs, 'Unexpected destination directories'
    current, current_dirs = inventory(SOURCE)
    assert current == files and current_dirs == directories, 'Source inventory changed during copy'
    for name in SUPPORT:
        assert (SOURCE / name).read_bytes() == (target / name).read_bytes(), name
    subprocess.run(['sync'], check=True)
    report = status('complete', destination=str(target), filesystem='exFAT',
                    file_paths_and_sizes_match=True, symlinks=0,
                    nested_deployment_directories=0, supporting_files_byte_match=True,
                    full_checksum_verification=False, **summary)
    (WORK / 'complete.json').write_text(json.dumps(report, indent=2) + '\n')
    archive = SOURCE.parents[1] / '_verification/exfat-delivery-2026-09-23.json'
    archive.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if WORK.exists():
            status('error', error=repr(error))
        raise
