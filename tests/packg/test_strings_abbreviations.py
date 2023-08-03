from packg.strings import create_unique_abbreviations, create_nested_abbreviations


def test_create_unique_abbrevations():
    all_pairs = [
        (["script_1"], ["s1"]),
        (["script_1", "script_2", "script_3"], ["s1", "s2", "s3"]),
        (
            [
                "script_1",
                "sub.another_script_1",
                "sub.yet_another_script_1",
                "also_script_1",
            ],
            ["s1", "sas1", "syas1", "as1"],
        ),
    ]
    for script_names, ref_abbrev_list in all_pairs:
        cand_abbrev_dict = create_unique_abbreviations(script_names)
        _assert_abbrevs(cand_abbrev_dict, ref_abbrev_list, script_names)


def test_create_nested_abbrevations():
    all_pairs = [
        (["script_1"], ["s"]),
        (
            ["script_1", "sub.script_2", "sub.script_3", "sub.else"],
            ["s", "s.script_2", "s.script_3", "s.e"],
        ),
        (
            ["sub.script_1", "sib.script_1", "fub.script_1", "sub.scr5_script"],
            ["su.scri", "si.s", "f.s", "su.scr5"],
        ),
    ]
    for script_names, ref_abbrev_list in all_pairs:
        cand_abbrev_dict = create_nested_abbreviations(script_names)
        _assert_abbrevs(cand_abbrev_dict, ref_abbrev_list, script_names)


def _assert_abbrevs(candidate_dict, reference_abbrevs, input_script_names):
    ref_both = dict(zip(reference_abbrevs, input_script_names))
    assert candidate_dict == ref_both
