##########
#
# File parsed as Finite State Machine
#
# Each line of input possibly changes the state of the processing.
# Ensure that each new input is consistent with the current state of the machine
#
########
from enum import Enum


class FsmState(Enum):
    DOCUMENT_START = 1
    COUNTY_START = 2
    STREET_ADDRESS = 3
    WORK_ITEM = 4
    TOTAL_CASES_COUNTY = 5
    COUNTY_CASES = 6
    TOTAL_CASES_DOCUMENT = 7
