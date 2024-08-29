import shutil
from packg.log import logger


def format_pseudo_table(items, max_width=None, padding=2):
    if len(items) == 0:
        logger.warning(f"(Empty table supplied to format_pseudo_table)")
        return ""
    if max_width is None:
        max_width = shutil.get_terminal_size().columns
    max_item_length = max(len(item) for item in items)
    num_columns = max_width // (max_item_length + padding)
    num_rows = (len(items) + num_columns - 1) // num_columns
    # Print items in a pseudo-table format
    lines = []
    for row in range(num_rows):
        row_items = [
            items[row + num_rows * col]
            for col in range(num_columns)
            if row + num_rows * col < len(items)
        ]
        lines.append("".join(f"{item:<{max_item_length + padding}}" for item in row_items))
    return "\n".join(lines)


def main():
    # todo turn into test file
    # todo test witg empty list
    items = [
        "file1.txt",
        "file2.jpg",
        "file3.pdf",
        "file4.do4234cx",
        "file5.mp3",
        "file6.png",
        "file7.zip",
        "file8.tsdfsar.gz",
        "file9.mov",
        "file10.avi",
        "file11.mkv",
        "file12.234txt",
        "file13.jpg",
        "file14.pdf",
        "file15.docx",
        "file16.mp3",
        "file17.png",
        "filsfde18.zip",
        "fi234234le19.tar.gz",
        "filesdfasdasdf20.mov",
    ]
    here_output = format_pseudo_table(items)
    print(here_output)
    gt_output = """\
file1.txt             file8.tsdfsar.gz      file15.docx           
file2.jpg             file9.mov             file16.mp3            
file3.pdf             file10.avi            file17.png            
file4.do4234cx        file11.mkv            filsfde18.zip         
file5.mp3             file12.234txt         fi234234le19.tar.gz   
file6.png             file13.jpg            filesdfasdasdf20.mov  
file7.zip             file14.pdf       """
    assert here_output.strip() == gt_output.strip()


if __name__ == "__main__":
    main()
