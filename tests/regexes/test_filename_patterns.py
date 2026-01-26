from src.regexes.filename_patterns import is_valid_input_filename

months = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]
year = "1984"
filetypes = ["txt", "pdf"]


def test_return_true_when_valid_month():
    for month in months:
        valid_filename = f"{month}-{year}-mci-closed-case-report.pdf"
        assert is_valid_input_filename(valid_filename)


def test_return_false_when_invalid_month():
    invalid_filename = f"zoomzember-{year}-mci-closed-case-report.pdf"
    assert not is_valid_input_filename(invalid_filename)


def test_return_true_when_filetype_valid():
    for filetype in filetypes:
        valid_filename = f"april-{year}-mci-closed-case-report.{filetype}"
        assert is_valid_input_filename(valid_filename)


def test_return_false_when_filetype_invalid():
    invalid_filename = f"april-{year}-mci-closed-case-report.mp3"
    assert not is_valid_input_filename(invalid_filename)


def test_return_true_when_direct_path_valid():
    for filetype in filetypes:
        valid_filename = f"april-22-DirectFeed-{year}-mci-closed-case-report.{filetype}"
        assert is_valid_input_filename(valid_filename)


# def test_return_true_when_direct_path_invalid():
#     for filetype in filetypes:
#         valid_filename = f"april-{year}-mci-closed-case-report.{filetype}"
#         assert is_valid_input_filename(valid_filename)
