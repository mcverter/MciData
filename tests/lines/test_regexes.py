from src.lines.regexes import array_to_regex_or


def test_array_to_regex_or():
    alternates = [
        "this",
        "that",
        "other",
    ]
    assert array_to_regex_or(alternates) == "(this|that|other)"
