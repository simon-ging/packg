import os
import shutil
import sys

import numpy as np
import pytest

from packg.cli import deduplicate_between_dirs, deduplicate_within_dir
from packg.iotools.file_dedup import (
    MethodC,
    dates_differ,
    find_candidates,
    find_date,
)

needs_pdftotext = pytest.mark.skipif(shutil.which("pdftotext") is None, reason="needs pdftotext")


@pytest.fixture(autouse=True)
def cache_dir(tmp_path, monkeypatch):
    # the folder index and the hashes are cached, keep that out of the real cache dir
    monkeypatch.setenv("PACKG_CACHE_DIR", (tmp_path / "cache").as_posix())


def make_pdf(path, text: str, producer: str) -> None:
    """A one page PDF with a line of text. The producer changes the bytes but not the text."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Producer ({producer}) >>".encode(),
    ]
    out = b"%PDF-1.4\n"
    offsets = []
    for number, content in enumerate(objects, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + content + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    out += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R /Info 6 0 R >>\n" % (len(objects) + 1)
    out += b"startxref\n%d\n%%%%EOF\n" % xref
    path.write_bytes(out)


def names(folder) -> list[str]:
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())


def run(module, monkeypatch, *argv) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", *map(str, argv)])
    module.main()


def test_find_candidates():
    sizes = np.array([100, 100, 105, 5000, 5400, 9000])
    exact = find_candidates(sizes, sizes, MethodC.EXACT)
    assert exact[0].tolist() == [True, True, False, False, False, False]
    approx = find_candidates(sizes, sizes, MethodC.APPROX)
    # 105 is within a kilobyte of 100, 5400 within 10% of 5000, 9000 is far from everything
    assert approx[0].tolist() == [True, True, True, False, False, False]
    assert approx[3].tolist() == [False, False, False, True, True, False]
    with pytest.raises(ValueError, match="Unknown method"):
        find_candidates(sizes, sizes, "fuzzy")


def test_dates():
    assert find_date("2024-10-03_report.pdf") == "2024-10-03"
    assert find_date("report_20241003_final.pdf") == "20241003"
    assert find_date("report.pdf") is None
    assert dates_differ("report_20241003_a.pdf", "report_20241104_a.pdf")
    assert not dates_differ("report_20241003_a.pdf", "report_20241003_b.pdf")
    assert not dates_differ("report_20241003_a.pdf", "report.pdf")


def test_within_dir_exact(tmp_path, monkeypatch):
    folder = tmp_path / "folder"
    (folder / "sub").mkdir(parents=True)
    (folder / "a.txt").write_text("same")
    (folder / "b.txt").write_text("same")
    (folder / "sub" / "c.txt").write_text("same")
    (folder / "d.txt").write_text("diff")  # same size, other content
    (folder / "e.txt").write_text("longer text")

    run(deduplicate_within_dir, monkeypatch, folder)
    assert len(names(folder)) == 5, "a dry run deletes nothing"
    run(deduplicate_within_dir, monkeypatch, folder, "-w")
    # the first of the group in name order is kept
    assert names(folder) == ["a.txt", "d.txt", "e.txt"]


def test_within_dir_respects_filters_and_dates(tmp_path, monkeypatch):
    folder = tmp_path / "folder"
    folder.mkdir()
    for name in ["x_20240101_.txt", "x_20240202_.txt", "keep.log", "other.log"]:
        (folder / name).write_text("same")
    run(deduplicate_within_dir, monkeypatch, folder, "-d", "-x", "*.log", "-w")
    # the two dated files differ by date, the log files are excluded from the search
    assert len(names(folder)) == 4
    run(deduplicate_within_dir, monkeypatch, folder, "-x", "*.log", "-r", "-w")
    assert names(folder) == ["keep.log", "other.log", "x_20240101_.txt"]


def test_between_dirs(tmp_path, monkeypatch):
    src, tgt = tmp_path / "src", tmp_path / "tgt"
    src.mkdir()
    tgt.mkdir()
    (src / "a.txt").write_text("same")
    (src / "only_src.txt").write_text("src!")
    (tgt / "renamed.txt").write_text("same")
    (tgt / "copy.txt").write_text("same")
    (tgt / "only_tgt.txt").write_text("tgt!")

    run(deduplicate_between_dirs, monkeypatch, src, tgt, "-w")
    assert len(names(src)) == 2 and len(names(tgt)) == 3, "without a side nothing is deleted"
    run(deduplicate_between_dirs, monkeypatch, src, tgt, "--delete_target")
    assert len(names(tgt)) == 3, "a dry run deletes nothing"
    with pytest.raises(ValueError, match="nothing remains"):
        run(deduplicate_between_dirs, monkeypatch, src, tgt, "--delete_source", "--delete_target")
    run(deduplicate_between_dirs, monkeypatch, src, tgt, "--delete_target", "-w")
    assert names(src) == ["a.txt", "only_src.txt"]
    assert names(tgt) == ["only_tgt.txt"]


@needs_pdftotext
def test_approx_finds_pdfs_with_the_same_text(tmp_path, monkeypatch):
    folder = tmp_path / "folder"
    folder.mkdir()
    make_pdf(folder / "a.pdf", "Hello duplicate world", "tool one")
    make_pdf(folder / "b.pdf", "Hello duplicate world", "another tool")
    make_pdf(folder / "c.pdf", "Hello different world", "tool one")
    # no text at all, like two different scans. They must not count as duplicates
    make_pdf(folder / "scan1.pdf", "", "scanner a")
    make_pdf(folder / "scan2.pdf", "", "scanner b")
    # not a PDF, so only an exact match counts
    (folder / "x.txt").write_text("almost the same text 1")
    (folder / "y.txt").write_text("almost the same text 2")

    run(deduplicate_within_dir, monkeypatch, folder, "-w")
    assert len(names(folder)) == 7, "the bytes differ, so exact finds nothing"
    run(deduplicate_within_dir, monkeypatch, folder, "-m", "approx", "-w")
    assert names(folder) == ["a.pdf", "c.pdf", "scan1.pdf", "scan2.pdf", "x.txt", "y.txt"]


@needs_pdftotext
def test_approx_between_dirs(tmp_path, monkeypatch):
    src, tgt = tmp_path / "src", tmp_path / "tgt"
    src.mkdir()
    tgt.mkdir()
    make_pdf(src / "a.pdf", "Hello duplicate world", "tool one")
    make_pdf(tgt / "export.pdf", "Hello duplicate world", "another tool")
    make_pdf(tgt / "other.pdf", "Hello different world", "another tool")
    run(deduplicate_between_dirs, monkeypatch, src, tgt, "-m", "approx", "--delete_source", "-w")
    assert names(src) == []
    assert names(tgt) == ["export.pdf", "other.pdf"]


def test_changed_file_is_hashed_again(tmp_path, monkeypatch):
    folder = tmp_path / "folder"
    folder.mkdir()
    (folder / "a.txt").write_text("same")
    (folder / "b.txt").write_text("same")
    run(deduplicate_within_dir, monkeypatch, folder)  # dry run, fills the hash cache
    # same name and size, other content. The cached hash of b.txt must not be trusted
    (folder / "b.txt").write_text("diff")
    stat = (folder / "b.txt").stat()
    os.utime(folder / "b.txt", ns=(stat.st_atime_ns, stat.st_mtime_ns + 10**9))
    run(deduplicate_within_dir, monkeypatch, folder, "-w")
    assert names(folder) == ["a.txt", "b.txt"]
    # and an unchanged duplicate is still found from the cache
    (folder / "c.txt").write_text("same")
    run(deduplicate_within_dir, monkeypatch, folder, "-r", "-w")
    assert names(folder) == ["a.txt", "b.txt"]
