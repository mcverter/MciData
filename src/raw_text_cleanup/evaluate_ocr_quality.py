import os.path
import pathlib
import sys

from src.lines.lines import is_well_formed_line

BASE_DIR = pathlib.Path(__file__).parent.parent.parent
INPUT_DOCUMENT_BASE_DIR = os.path.join(BASE_DIR, "data", "DirectFeed")
DEFAULT_INPUT_FILENAME = "DirectFeed-12-february-2026-mci-closed-case-report.txt"


def check_ocr_file(filename: str) -> None:
    with open(filename) as ocr:
        lines = ocr.readlines()
        total_lines = len(lines)
        well_formed_lines = 0
        for line in lines:
            if not is_well_formed_line(line):
                print("Bad line: " + line)
            else:
                well_formed_lines += 1
        print(
            f"Well-formed: {well_formed_lines}. Total: {total_lines}. Accuracy:{well_formed_lines / total_lines}"
        )


if __name__ == "__main__":
    filename = DEFAULT_INPUT_FILENAME
    filename_argv_number = 3
    if len(sys.argv) == filename_argv_number and sys.argv[1] == "-f":
        filename = sys.argv[2]
    check_ocr_file(os.path.join(INPUT_DOCUMENT_BASE_DIR, filename))
