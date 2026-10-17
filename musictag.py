#!/usr/bin/env python3
"""
musictag - scan and bulk-fix music file tags (MP3 / M4A) from a CSV.

Workflow
  1. scan   : read the current tags of every song in a folder -> CSV
  2. (you)  : fill in / correct title, artist, album, year, genre in the CSV
              (by hand, with Claude, Gemini, a spreadsheet...)
  3. apply  : write the CSV back into the files (dry-run by default)

Usage
  python musictag.py scan  "C:\\path\\to\\music"  tags.csv
  python musictag.py apply "C:\\path\\to\\music"  tags.csv            # preview only
  python musictag.py apply "C:\\path\\to\\music"  tags.csv --write    # really write
"""
import argparse
import csv
import logging
import os
import re
import shutil
import sys

try:
    import mutagen
    from mutagen.easyid3 import EasyID3
    from mutagen.easymp4 import EasyMP4
    from mutagen.id3 import ID3, ID3NoHeaderError
except ImportError:
    sys.exit("mutagen is not installed. Run:  pip install -r requirements.txt")

AUDIO_EXT = (".mp3", ".m4a", ".mp4", ".aac")
FIELDS = ["file", "title", "artist", "album", "year", "genre", "conf", "length_s"]
log = logging.getLogger("musictag")


# ---------------------------------------------------------------- helpers
def audio_files(folder):
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith(AUDIO_EXT) and os.path.isfile(os.path.join(folder, name)):
            yield name


def open_easy(path):
    """Open with the right tag format based on the REAL file type, not the
    extension (some '.mp3' downloads are actually MP4/AAC inside)."""
    real = mutagen.File(path)
    if real is None:
        raise ValueError("not a readable audio file")
    if type(real).__name__ == "MP3":
        try:
            return EasyID3(path)
        except ID3NoHeaderError:
            ID3().save(path)          # file had no tag block yet
            return EasyID3(path)
    return EasyMP4(path)


def main_artist(artist):
    """'Logic feat. Alessia Cara' -> 'Logic' (used as Album Artist)."""
    return re.split(r"\s+(?:feat\.|ft\.|featuring)\s+", artist, flags=re.I)[0].strip()


# ---------------------------------------------------------------- scan
def cmd_scan(folder, out_csv):
    rows, errors = [], 0
    for name in audio_files(folder):
        path = os.path.join(folder, name)
        row = {"file": name}
        try:
            m = mutagen.File(path, easy=True)
            if m is None:
                raise ValueError("unreadable")
            row["length_s"] = round(m.info.length) if m.info else ""
            for k_csv, k_tag in (("title", "title"), ("artist", "artist"), ("album", "album"),
                                 ("year", "date"), ("genre", "genre")):
                v = m.get(k_tag)
                row[k_csv] = "; ".join(map(str, v)) if v else ""
        except Exception as e:  # keep going, report at the end
            errors += 1
            log.warning("could not read %s: %s", name, e)
            row["conf"] = "error"
        rows.append(row)

    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:   # utf-8-sig opens cleanly in Excel
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    log.info("scanned %d files (%d unreadable) -> %s", len(rows), errors, out_csv)


# ---------------------------------------------------------------- apply
def cmd_apply(folder, in_csv, write, backup_dir):
    with open(in_csv, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    done, skipped, failed = 0, 0, []
    for r in rows:
        name = (r.get("file") or "").strip()
        if not name or r.get("conf", "").strip().lower() in ("unknown", "skip", "error"):
            skipped += 1
            continue
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            failed.append((name, "file not found"))
            continue

        new = {k: (r.get(k) or "").strip() for k in ("title", "artist", "album", "genre")}
        new["date"] = (r.get("year") or "").strip()
        if new["artist"]:
            new["albumartist"] = main_artist(new["artist"])
        new = {k: v for k, v in new.items() if v}       # never blank out existing tags

        if not write:
            log.info("[preview] %s -> %s", name, new)
            done += 1
            continue
        try:
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(path, os.path.join(backup_dir, name))
            m = open_easy(path)
            for k, v in new.items():
                m[k] = v
            m.save()
            done += 1
        except Exception as e:
            failed.append((name, str(e)[:100]))

    verb = "written" if write else "would be written (preview - add --write to apply)"
    log.info("%d %s, %d skipped, %d failed", done, verb, skipped, len(failed))
    for name, err in failed:
        log.error("FAILED %s: %s", name, err)
    return 1 if failed else 0


# ---------------------------------------------------------------- cli
def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="read current tags into a CSV")
    s.add_argument("folder")
    s.add_argument("csv")

    a = sub.add_parser("apply", help="write tags from a CSV into the files")
    a.add_argument("folder")
    a.add_argument("csv")
    a.add_argument("--write", action="store_true", help="actually change files (default: preview only)")
    a.add_argument("--backup", metavar="DIR", help="copy each original file here before changing it")

    args = p.parse_args()
    if not os.path.isdir(args.folder):
        sys.exit(f"folder not found: {args.folder}")
    if args.cmd == "scan":
        cmd_scan(args.folder, args.csv)
        return 0
    return cmd_apply(args.folder, args.csv, args.write, args.backup)


if __name__ == "__main__":
    sys.exit(main())
