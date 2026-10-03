"""
Takes a folder of a latex project and merges it into a single main.tex file.
Removes all subfolders and moves all images into the target root folder.
"""

import os
import re
import shutil
from pathlib import Path

from attrs import define

from typedparser import TypedParser, add_argument


@define
class Args:
    src_root: str = add_argument(
        "--src_root",
        type=str,
        default="TEMP_latex_source",
        help="Source directory containing the main tex and includes",
    )
    dst_root: str = add_argument(
        "--dst_root",
        type=str,
        default="TEMP_latex_merged",
        help="Destination directory for merged tex and images",
    )
    main_tex: str = add_argument(
        "--main_tex", type=str, default="main.tex", help="Main tex file name (entry point)"
    )


# Regex patterns
INCLUDE_PATTERN = re.compile(r"\\(input|include)\{([^}]+)\}")
GRAPHICS_PATTERN = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")


def main():
    parser = TypedParser.create_parser(
        Args, description="Merge and flatten a LaTeX project with includes and images."
    )
    args: Args = parser.parse_args()
    src_root = Path(args.src_root)
    dst_root = Path(args.dst_root)
    main_tex = args.main_tex
    src_main = src_root / main_tex
    dst_main = dst_root / main_tex
    shutil.rmtree(dst_root, ignore_errors=True)
    os.makedirs(dst_root)
    # 1. Read and expand all includes
    tex_content = Path(src_main).read_text(encoding="utf-8")
    expanded_tex = expand_includes(tex_content, src_root)
    # 2. Move all referenced images and update paths
    merged_tex, _ = find_and_move_images(expanded_tex, src_root, dst_root)
    # 3. Remove unused \newcommand definitions
    merged_tex = remove_unused_newcommands(merged_tex)
    # 4. Write merged tex
    with open(dst_main, "w", encoding="utf-8") as f:
        f.write(merged_tex)
    print(f"Merged tex written to {dst_main}")


def expand_includes(tex_content, base_dir, included_files=None):
    if included_files is None:
        included_files = set()

    def replacer(match):
        cmd, rel_path = match.groups()
        # Always resolve relative to the current file's directory (base_dir)
        candidate_paths = [
            (base_dir / rel_path).resolve(),
            (base_dir / (rel_path + ".tex")).resolve() if not rel_path.endswith(".tex") else None,
        ]
        abs_path = None
        for p in candidate_paths:
            if p and p.exists():
                abs_path = p
                break
        if abs_path is None:
            raise ValueError(f"File not found for include: {rel_path} (tried: {candidate_paths})")
        if abs_path in included_files:
            raise ValueError(f"Double include detected: {rel_path}")
        included_files.add(abs_path)
        content = abs_path.read_text(encoding="utf-8")
        return expand_includes(content, base_dir, included_files)

    return INCLUDE_PATTERN.sub(replacer, tex_content)


def find_and_move_images(tex_content, src_dir, dst_dir):
    images_moved = set()

    def img_replacer(match):
        img_path = match.group(1)
        # Try with and without extension
        candidates = [src_dir / img_path]
        for ext in [".jpg", ".jpeg", ".png"]:
            candidates.append(src_dir / (img_path + ext))
        src_img = None
        img_name = None
        for candidate in candidates:
            if candidate.exists():
                src_img = candidate
                img_name = os.path.basename(candidate)
                break
        if src_img is None:
            raise ValueError(f"Image not found: {img_path} (tried: {[str(c) for c in candidates]})")
        dst_img = dst_dir / img_name
        shutil.copy2(src_img, dst_img)
        images_moved.add(img_name)
        # Always update the path in the tex to be just the filename
        return match.group(0).replace(img_path, img_name)

    new_tex = GRAPHICS_PATTERN.sub(img_replacer, tex_content)
    return new_tex, images_moved


def remove_unused_newcommands(tex_content):
    # Find all \newcommand{\foo} or \newcommand\foo
    newcommand_pattern = re.compile(
        r"^(\\newcommand\s*(?:\{\\(\w+)\}|\\(\w+))[^\n]*)", re.MULTILINE
    )
    commands = []
    for match in newcommand_pattern.finditer(tex_content):
        full_def = match.group(1)
        cmd = match.group(2) or match.group(3)
        if cmd:
            commands.append((full_def, cmd))
    # Count usage of each command (as \\foo)
    usage_counts = {}
    for full_def, cmd in commands:
        # Look for \\foo not immediately followed by a letter (to avoid partial matches)
        usage_pattern = re.compile(rf"\\{cmd}(?![A-Za-z])")
        # Exclude the definition itself
        content_wo_def = tex_content.replace(full_def, "")
        count = len(list(usage_pattern.finditer(content_wo_def)))
        usage_counts[cmd] = count
    # Print sorted usage counts
    print("\\newcommand usage counts (descending):")
    for cmd, count in sorted(usage_counts.items(), key=lambda x: -x[1]):
        print(f"  \\{cmd}: {count}")
    # Remove unused newcommands
    to_remove = [full_def for (full_def, cmd) in commands if usage_counts[cmd] == 0]
    for full_def in to_remove:
        tex_content = tex_content.replace(full_def + "\n", "")
        tex_content = tex_content.replace(full_def, "")
    return tex_content


if __name__ == "__main__":
    main()
