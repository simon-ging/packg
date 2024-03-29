r"""
pattern:
    match(string, pos, endpos) -> re.Match | None - Determine if RE matches at beginning of string.
    fullmatch(string, pos, endpos) - same but the entire string must match
    search(string, pos, endpos) - return first match in the string
    findall(string, pos, endpos) - find all matching, nonoverlapping substrings
    finditer, same but iterator instead of list.
    split(string) - same as str.split
    sub: replace
    subn: replace and return number of replacements

match object:
    group(0) - the entire match
    group(i) - the i-th parenthesized expression
    groups() - all parenthesized expressions
    __getitem__(i) - same as group(i)
    groupdict() - named groups
        m = re.match(r"(?P<first_name>\w+) (?P<last_name>\w+)", "Malcolm Reynolds")
        m.groupdict()  # {'first_name': 'Malcolm', 'last_name': 'Reynolds'}


"""