---
title: FileMetaExtractor (file stats + EXIF)
tags: [files, exif, metadata]
sourceRefs: [mailforen/modules/forensic/filemeta.py]
lastReviewed: 2026-10-29
---

# `FileMetaExtractor` (`mailforen/modules/forensic/filemeta.py`)

Singleton `file_meta`. Local filesystem only.

```python
extract(self, file_path: Path) -> Dict
human_size(self, size_bytes) -> str
```

## Output
`filename`, `path` (absolute), `size_bytes`, `size_human`, `created` (`st_ctime`),
`modified` (`st_mtime`), `accessed` (`st_atime`), `extension` (lowercased suffix). A missing
file returns `{"error": "File not found"}`.

EXIF is read with `exifread.process_file` **only** for `.jpg/.jpeg/.tiff/.tif`, skipping
`JPEGThumbnail`, `TIFFThumbnail`, `Filename`, `EXIF MakerNote`; values are stringified and
added as `results["exif"]` when non-empty.

## Gotchas
- `st_ctime` on Linux is **inode change time, not creation time** — labelled `created` here.
- `human_size` loops `["B","KB","MB","GB"]` and falls through to `f"{x:.1f} TB"` after the
  loop, but the value returned in that branch has already been divided by 1024⁴, so the TB
  figure is correct only by accident of loop structure; verify before reusing.
- No hashing (MD5/SHA-256) and no `python-magic` MIME detection, even though
  `python-magic` is a declared dependency. Evidence-grade identification would need both —
  see [[concepts/known-gaps]].
