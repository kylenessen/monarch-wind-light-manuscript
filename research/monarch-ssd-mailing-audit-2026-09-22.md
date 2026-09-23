# MonarchSSD mailing audit

The drive is not ready to mail. The audit did not change any files on MonarchSSD or MediaVault.

The canonical release index lists 226,830 photographs. Only 111,698 are currently accessible in the release. The five ordinary deployment folders remain present. The other 23 deployment folders are absolute symbolic links to the removed raw, VSFB_2025_Deployment_Review and corrected_photos directories. Those links account for 115,132 unavailable indexed photographs. The user confirmed deleting the target directories. The SSD Trash is empty and the volume has no APFS snapshots.

Source files were located on MediaVault for every unavailable photo record. Of these, 78,355 already have their release filenames. Another 33,804 map to original camera files through the saved export inventory. The remaining 2,973 are TGR1 photographs whose corrected names and EXIF times can be recreated from data/release_working/tgr1_photo_times.csv and tools/prepare_tgr1_photos.py. All 2,973 original TGR1 EXIF timestamps match that saved mapping. Every located source is nonempty, and no source path was assigned to multiple release records. These source files total 154.36 GB. They have not yet been copied or fully checked for content integrity.

The six CSV files and metadata.xml match the corresponding repository and OneDrive review files byte for byte. The data tables retain their expected row counts, have no blank cells and parse without malformed rows. The metadata still awaits the release DOI and publication date. These administrative placeholders do not account for the missing photos.

Recovery should populate actual deployment directories inside publication_package/photos using exactly the records in photo_index.csv. Existing valid photos should be retained. The TGR1 correction must preserve the recorded reconstruction rather than substituting its incorrect original camera timestamps. Recovered copies should be checked against their sources, with full index coverage and no symbolic links in the delivery package. Historical extras and excluded photos should not be brought back into the release.

The SSD is formatted as APFS. The user thinks the recipient is likely to use Windows. Apple lists [ExFAT as Windows compatible](https://support.apple.com/guide/disk-utility/file-system-formats-dsku19ed921c/mac). A compatible shipping drive or volume is needed. Reformatting this SSD would require first securing and verifying its remaining contents elsewhere. No reformatting was performed.

Outside the release, the drive contains Pictures and monarch-knowledge-base folders, plus a OneDrive shortcut pointing to the local computer. That shortcut will not supply any OneDrive files to the recipient. Other local-computer links exist within the unrelated knowledge-base software files. This audit did not copy, delete or reorganize those materials.

The accompanying JSON records file hashes, counts, deployment source coverage and remaining limitations. The audit establishes a source mapping for recovery, not a completed restoration or a full image-integrity check.
