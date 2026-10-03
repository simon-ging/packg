"""Scan a folder of PDFs and report which ones contain user annotations, and which tool made them.

Skips Link / Widget / Popup / RichMedia annotations (hyperlinks, forms, media9 embeds), which
paper PDFs often have, and reports the rest: Highlight, Text (sticky comment), FreeText, Ink,
Underline, StrikeOut, Squiggly, Square, Stamp, ...

Tool guess per annotation (heuristic, from the annotation dict):
    zotero   /Zotero:Key present
    okular   /NM starts with "okular-"
    foxit    /Subj present + /NM uuid (Foxit Reader, "Typewriter" FreeText)
    pdfjs    Firefox / pdf.js: no /NM, no /Subj, has /Rotate key, and the file has an
             incremental update (second %%EOF). pdf.js does not touch /Producer or /ModDate.
    unknown  anything else

Usage:
    python -m packg.cli.check_pdf_annotations -b DIR
    python -m packg.cli.check_pdf_annotations -b DIR -a        # also list files without annotations
    python -m packg.cli.check_pdf_annotations -b DIR -v        # print every annotation
"""

import logging
from collections import Counter
from pathlib import Path

from attrs import define
from loguru import logger
from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from typedparser import VerboseQuietArgs, add_argument, TypedParser

IGNORED_SUBTYPES = {"/Link", "/Widget", "/Popup", "/RichMedia"}


@define
class Args(VerboseQuietArgs):
    base_dir: Path = add_argument(shortcut="-b", type=str, help="Folder with PDFs")
    recursive: bool = add_argument(shortcut="-r", action="store_true", help="Recurse into subdirs")
    show_all: bool = add_argument(
        shortcut="-a", action="store_true", help="Also list files without annotations"
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    # PyPDF2 spams "Object N 0 not defined." for dangling refs, which we handle ourselves
    logging.getLogger("PyPDF2").setLevel(logging.ERROR)

    if not args.base_dir.is_dir():
        raise FileNotFoundError(f"Not a directory: {args.base_dir}")
    pattern = "**/*.pdf" if args.recursive else "*.pdf"
    pdf_files = sorted(p for p in args.base_dir.glob(pattern) if p.is_file())
    if len(pdf_files) == 0:
        raise FileNotFoundError(f"No PDFs found in {args.base_dir} (pattern {pattern})")
    logger.info(f"Scanning {len(pdf_files)} PDFs in {args.base_dir}")

    n_annotated, n_failed = 0, 0
    tool_totals = Counter()
    for pdf_file in pdf_files:
        try:
            report = scan_pdf(pdf_file)
        except (PdfReadError, ValueError, KeyError, TypeError, OSError) as e:
            n_failed += 1
            logger.error(f"FAILED  {pdf_file.name}: {type(e).__name__}: {e}")
            continue
        annots = report["annots"]
        if len(annots) == 0:
            if args.show_all:
                print(f"-          {pdf_file.name}")
            continue
        n_annotated += 1
        subtype_counts = Counter(a["subtype"].lstrip("/") for a in annots)
        tool_counts = Counter(a["tool"] for a in annots)
        tool_totals.update(tool_counts)
        subtypes_str = ", ".join(f"{k}={v}" for k, v in sorted(subtype_counts.items()))
        tools_str = ", ".join(f"{k}={v}" for k, v in sorted(tool_counts.items()))
        authors = sorted({a["author"] for a in annots if a["author"]})
        flags = ["incremental"] if report["incremental"] else []
        flags.append(f"producer={report['producer']!r}")
        if authors:
            flags.append(f"authors={authors}")
        print(
            f"ANNOT {len(annots):4d}  {pdf_file.name}\n"
            f"            tools: {tools_str}   types: {subtypes_str}   {' '.join(flags)}"
        )
        for a in annots:
            logger.debug(
                f"    p{a['page']:<3d} {a['tool']:<8} {a['subtype']:<12} "
                f"author={a['author']!r} contents={a['contents']!r}"
            )

    print(f"\n{n_annotated}/{len(pdf_files)} PDFs have annotations, {n_failed} failed to parse")
    print(f"annotations per tool: {dict(tool_totals)}")
    if n_failed > 0:
        logger.warning(f"{n_failed} files could not be parsed, see errors above")


def scan_pdf(pdf_file: Path) -> dict:
    reader = PdfReader(pdf_file.as_posix())
    incremental = has_incremental_update(pdf_file)
    annots = []
    for page_num, page in enumerate(reader.pages, start=1):
        page_annots = page.get("/Annots")
        if page_annots is None:
            continue
        for ref in page_annots.get_object():
            annot = ref.get_object()
            if annot is None:
                logger.debug(f"{pdf_file.name} p{page_num}: dangling annotation ref {ref}")
                continue
            subtype = str(annot.get("/Subtype", "?"))
            if subtype in IGNORED_SUBTYPES:
                continue
            contents = annot.get("/Contents")
            annots.append(
                {
                    "page": page_num,
                    "subtype": subtype,
                    "tool": guess_tool(annot, incremental),
                    "author": str(annot["/T"]) if "/T" in annot else "",
                    "contents": str(contents)[:80] if contents else "",
                }
            )
    meta = reader.metadata
    producer = str(meta.get("/Producer", "")) if meta is not None else ""
    return {"annots": annots, "producer": producer, "incremental": incremental}


def guess_tool(annot, incremental: bool) -> str:
    if "/Zotero:Key" in annot:
        return "zotero"
    name = str(annot.get("/NM", ""))
    if name.startswith("okular-"):
        return "okular"
    if "/Subj" in annot and name:
        return "foxit"
    if not name and "/Subj" not in annot and "/Rotate" in annot and incremental:
        return "pdfjs"
    return "unknown"


def has_incremental_update(pdf_file: Path) -> bool:
    return pdf_file.read_bytes().count(b"%%EOF") > 1


if __name__ == "__main__":
    main()
