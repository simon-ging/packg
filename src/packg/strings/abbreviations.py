from collections import defaultdict
from copy import deepcopy
from typing import List, Dict, Tuple


def create_unique_abbreviations(input_strings: List[str], seps=("_", ".")) -> Dict[str, str]:
    """

    Old version, splits input strings at "_" and "." and takes first letter of each word.

    lg         run.list_gpus
    pcbs       run.packaging.create_build_scripts

    Args:
        input_strings: list of strings to abbreviate
        seps: separator for splitting the input strings

    Returns:
        dict {input_string: abbreviation}
    """
    abbreviations = {}
    for name in input_strings:
        name_for_abbr = name
        for sep in seps[1:]:
            name_for_abbr = name_for_abbr.replace(sep, seps[0])
        words = name_for_abbr.split(seps[0])
        abbreviation = ""
        for word in words:
            abbreviation += word[0]
        if abbreviation in abbreviations:
            # enforce uniqueness
            i = 1
            while True:
                new_abbreviation = abbreviation + str(i)
                if new_abbreviation not in abbreviations:
                    abbreviation = new_abbreviation
                    break
                i += 1
        abbreviations[abbreviation] = name
    return abbreviations


def create_nested_abbreviations(input_strings: List[str], sep_dir=".") -> Dict[str, str]:
    """
    New version, keep the directory nesting and use minimal amount of letters

    l          run.list_gpus
    p.c        run.packaging.create_build_scripts

    Args:
        input_strings: list of strings to abbreviate
        sep_dir: separator for splitting the input strings into directories

    Returns:
        dict {input_string: abbreviation}
    """
    assert len(set(input_strings)) == len(input_strings), "Input strings must be unique"

    # split inputs and sort them into a nested dictionary, leaf nodes are empty dicts
    dct = {}
    for name in input_strings:
        parts = name.split(sep_dir)
        c_dct = dct
        for part in parts:
            if part not in c_dct:
                c_dct[part] = {}
            c_dct = c_dct[part]

    def _shorten_keys(keys: List[str]) -> List[Tuple[str, str]]:
        """For a given list of flat keys, find the shortest non-common prefix for each key.
        Returns a list of tuples (short_key, long_key)
        """
        if len(keys) == 0:
            return []
        longest_len = max(len(key) for key in keys)
        remaining_keys = deepcopy(keys)
        done_keys = []
        for k in range(1, longest_len + 1):
            # for a cutoff length k, sort the cut keys into buckets
            cut_keys = defaultdict(list)
            for key in remaining_keys:
                short_key = key[:k]
                cut_keys[short_key].append(key)

            # buckets with size 1 are done, for other buckets the cutoff needs to increase
            remaining_keys = []
            for short_key, t_keys in cut_keys.items():
                if len(t_keys) == 1:
                    done_keys.append((short_key, t_keys[0]))
                else:
                    remaining_keys.extend(t_keys)

            if len(remaining_keys) == 0:
                break
        else:
            raise ValueError("Could not find abbreviations")  # should not happen ever
        return done_keys

    def _recursive_shortcuts(dct_in, stem_short="", stem_long=""):
        """
        Given the nested dictionary, find the shortest non-common prefix for each nested key.
        Accumulate the short and long stems from the recursive calls.
        """
        if len(dct_in) == 0:
            return []
        keys = list(dct_in.keys())

        # shorten leafs and non-leafs separately as they dont need to be unique between each other
        key_is_leaf = {key: len(dct_in[key]) == 0 for key in keys}
        leaf_keys = [key for key, is_leaf in key_is_leaf.items() if is_leaf]
        non_leaf_keys = [key for key, is_leaf in key_is_leaf.items() if not is_leaf]
        short_leaf_keys = _shorten_keys(leaf_keys)
        short_non_leaf_keys = _shorten_keys(non_leaf_keys)

        return_strs = []
        for short_key, long_key in short_leaf_keys + short_non_leaf_keys:
            sub_stem_short = f"{stem_short}.{short_key}"
            sub_stem_long = f"{stem_long}.{long_key}"
            if key_is_leaf[long_key]:
                # leaf node, return the short and long total stems
                return_strs.append((sub_stem_short, sub_stem_long))
                continue
            # non-leaf node, recurse
            sub_strs = _recursive_shortcuts(dct_in[long_key], sub_stem_short, sub_stem_long)
            return_strs.extend(sub_strs)
        return return_strs

    # finally cut the first "." and return the dict
    return {s[1:]: l[1:] for s, l in _recursive_shortcuts(dct)}
