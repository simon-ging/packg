"""
Compress PDFs using ghostscript.

https://ghostscript.readthedocs.io/en/latest/VectorDevices.html#creating-a-pdf-x-3-document
https://stackoverflow.com/questions/30534442/ghostscript-dpdfsettings-shortcut

Example gs command:
    gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH \
        -sOutputFile=out.pdf in.pdf

/screen selects low-resolution output similar to the Acrobat Distiller (up to version X) ?Screen Optimized? setting.
/ebook selects medium-resolution output similar to the Acrobat Distiller (up to version X) ?eBook? setting.
/printer selects output similar to the Acrobat Distiller ?Print Optimized? (up to version X) setting.
/prepress selects output similar to Acrobat Distiller ?Prepress Optimized? (up to version X) setting.
/default selects output intended to be useful across a wide variety of uses, possibly at the expense of a larger output file.

Notes:
    - If the PDF cannot be read e.g. "**** Error: Couldn't get page info. Output may be incorrect."
      it is repaired with pdftk and compressed again.

Usage:
    python -m packg.cli.compress_pdfs /path/to/pdfs -o /path/to/compressed
"""

from pathlib import Path

from attrs import define
from loguru import logger

from packg.log import SHORTEST_FORMAT, configure_logger, get_logger_level_from_args
from packg.system import systemcall, systemcall_with_assert
from packg.typext import PathType
from typedparser import TypedParser, VerboseQuietArgs, add_argument


def get_gs_cmd(in_f, out_f):
    return (
        f"gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dPDFSETTINGS=/printer "
        f'-dNOPAUSE -dQUIET -dBATCH -sOutputFile="{Path(out_f).as_posix()}" '
        f'"{Path(in_f).as_posix()}"'
    )


def get_compression_ratio_between_files(in_f: PathType, out_f: PathType, verbose=True):
    in_size = Path(in_f).stat().st_size
    out_size = Path(out_f).stat().st_size
    comp_ratio = out_size / in_size
    if verbose:
        print(
            f"#     compressed {in_size / 1024 ** 2:.1f}MB -> {out_size / 1024 ** 2:.1f}MB "
            f"({comp_ratio:.1%} compression)"
        )
    return comp_ratio


@define
class Args(VerboseQuietArgs):
    input_path: Path = add_argument(
        "input_path",
        type=Path,
        help="If directory, will use --glob_str to search for pdfs. If single PDF file, will "
        "compress that file and ignore --glob_str",
    )
    glob_str: str = add_argument(
        shortcut="-g", default="*.pdf", type=str, help="glob string to find files"
    )
    output_dir: Path = add_argument(
        shortcut="-o",
        default="_done",
        type=str,
        help="Where the compressed files go, relative paths are inside the input dir",
    )


def main():
    parser = TypedParser.create_parser(Args, description=__doc__)
    args: Args = parser.parse_args()
    configure_logger(level=get_logger_level_from_args(args), format=SHORTEST_FORMAT)
    logger.info(f"{args}")

    out, _err, retcode = systemcall("gs --version")
    if retcode != 0:
        raise RuntimeError("Found no gs executable, install ghostscript")
    print(f"Found gs version {out.strip()}")

    # determine input
    if args.input_path.is_file():
        logger.info(f"Input file: {args.input_path}")
        input_files = [args.input_path]
        base_dir = args.input_path.parent
    elif args.input_path.is_dir():
        input_files = list(args.input_path.glob(args.glob_str))
        logger.info(
            f"Input dir {args.input_path} glob str {args.glob_str} found "
            f"{len(input_files)} files"
        )
        base_dir = args.input_path
    else:
        raise RuntimeError(f"Input path {args.input_path} is neither file nor dir")

    # determine output
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = base_dir / output_dir
    logger.info(f"Output dir: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    comp_ratios = {}
    for f in input_files:
        if not f.is_file() or f.suffix != ".pdf":
            print(f"Skip {f} (no pdf)")
            continue

        out_f = output_dir / f.name
        print(f"# In: {f} out: {out_f}")
        if out_f.is_file():
            print(f"#     already exists.")
            comp_ratios[f.name] = get_compression_ratio_between_files(f, out_f)
            continue

        gs_cmd = get_gs_cmd(f, out_f)
        print(gs_cmd)
        out, err, _retcode = systemcall(gs_cmd)
        # the return code is 0 even if gs fails, so the output is searched for errors
        if "error:" in out.lower():
            print(f"{out}")
            print(f"ERR: {err}")
            print(f"    # This file is probably corrupt now (e.g. missing pages)! Deleting...")
            out_f.unlink()

            # rewrite the source with pdftk, which repairs it, and compress the repaired file
            print(f"Running pdftk")
            repaired_dir = base_dir / "temp_decorrupted"
            repaired_dir.mkdir(exist_ok=True)
            repaired_f = repaired_dir / f.name
            systemcall_with_assert(f'pdftk "{f.as_posix()}" output "{repaired_f.as_posix()}"')

            out, err, _retcode = systemcall_with_assert(get_gs_cmd(repaired_f, out_f))
            assert "error:" not in out.lower(), f"gs failed again: {out}"

        comp_ratios[f.name] = get_compression_ratio_between_files(f, out_f)

    # analyze processed files
    already_compressed = 0
    for f_name, f_comp in comp_ratios.items():
        if f_comp > 0.75:
            already_compressed += 1
        else:
            print(f"     {f_comp:6.1%} {f_name}")
    print(f"Compressed {len(comp_ratios)} files, {already_compressed} were already compressed")


if __name__ == "__main__":
    main()
