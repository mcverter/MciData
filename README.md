This repo provides a simple script for parsing Major Capital Improvement Case files from the NYS Division of Housing and Community Renewal

This script is intended to be adapted for a larger project.  In its current form, it reads in all of the PDF files in a given `data` directory, extracts all of the MCI information and outputs it to a `csv` file in the `output` directory.

The script makes strong assumptions about the layout of the MCI files: each entry begins with a line containing the street address, followed by a line with the borough and other information about the property, followed by zero or more lines specifying each MCI work item and its associated costs.

To run the script, do the following 
1. Create a virtual environment
2. Install packages from `requirements.txt`
3. Run `python main.py`.  This will parse the file currently in the data directory and output the results to a csv file.
