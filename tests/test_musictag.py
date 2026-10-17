"""Run:  python -m pytest tests   (needs ffmpeg only to build the test file)"""
import csv, os, shutil, subprocess, sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import musictag
import mutagen

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg needed to create test audio")

def make(path):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=d=1", path], check=True)

def test_main_artist():
    assert musictag.main_artist("Logic feat. Alessia Cara") == "Logic"
    assert musictag.main_artist("Zedd ft. Kehlani") == "Zedd"

def test_scan_then_apply(tmp_path):
    make(str(tmp_path / "a.mp3")); make(str(tmp_path / "b.m4a"))
    out = tmp_path / "t.csv"
    musictag.cmd_scan(str(tmp_path), str(out))
    rows = list(csv.DictReader(open(out, encoding="utf-8-sig")))
    for r in rows:
        r.update(title="T", artist="X feat. Y", year="2020", genre="Pop", conf="high")
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=musictag.FIELDS); w.writeheader(); w.writerows(rows)
    assert musictag.cmd_apply(str(tmp_path), str(out), write=False, backup_dir=None) == 0
    assert mutagen.File(str(tmp_path / "a.mp3"), easy=True).get("title") is None   # preview changed nothing
    assert musictag.cmd_apply(str(tmp_path), str(out), write=True, backup_dir=str(tmp_path / "bk")) == 0
    for n in ("a.mp3", "b.m4a"):
        m = mutagen.File(str(tmp_path / n), easy=True)
        assert m["title"] == ["T"] and m["albumartist"] == ["X"]
    assert (tmp_path / "bk" / "a.mp3").exists()
