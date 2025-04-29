import shutil
from typing import List


def format_pseudo_table(
    items: List[str], max_width: int = None, padding: int = 2, indent: int = 0
) -> str:
    """Format a list of strings into a pseudo-table with multiple columns.

    Args:
        items: List of strings to format
        max_width: Maximum width of the table (defaults to terminal width)
        padding: Number of spaces between columns
        indent: Number of spaces to indent the entire table

    Returns:
        Formatted string with items arranged in columns
    """
    if not isinstance(items, list):
        raise ValueError("Expected list of strings, got string")

    if len(items) == 0:
        return ""
    items = [str(item) for item in items]

    if max_width is None:
        max_width = shutil.get_terminal_size().columns

    # Find the longest item
    max_item_len = max(len(item) for item in items)

    # Calculate number of columns that will fit
    # Each column needs max_item_len + padding space, except last column
    usable_width = max_width - indent

    # If we can't fit even one item, force single column
    if max_item_len > usable_width:
        num_cols = 1
    else:
        # Try to fit as many columns as possible
        # Each column needs max_item_len + padding space
        num_cols = max(1, (usable_width + padding) // (max_item_len + padding))
        # If we can't fit at least two items with padding, force single column
        if num_cols == 1 or (num_cols == 2 and max_item_len * 2 + padding > usable_width):
            num_cols = 1

    # Format items into rows
    result = []
    if num_cols == 1:
        # Single column mode: one item per line
        for item in items:
            result.append(" " * indent + item)
    else:
        # Multi-column mode
        # Calculate number of rows needed
        num_rows = (len(items) + num_cols - 1) // num_cols

        for row in range(num_rows):
            line = " " * indent
            for col in range(num_cols):
                idx = col * num_rows + row
                if idx < len(items):
                    item = items[idx]
                    if col > 0:
                        line += " " * padding
                    # Don't pad the last column
                    if col == num_cols - 1:
                        line += item
                    else:
                        line += item.ljust(max_item_len)
            result.append(line)

    return "\n".join(result)
