##########
#
# File parsed as Finite State Machine
#
# Each line of input possibly changes the state of the processing.
# Ensure that each new input is consistent with the current state of the machine
# This is still WIP
#
########
from enum import Enum


class FsmState(Enum):
    """Document Processing State"""

    START_DOCUMENT = 1
    START_COUNTY = 2
    START_PROPERTY = 3
    UPDATE_DOCKET = 4
    ADD_WORK_ITEM = 5
    END_PROPERTY = 6
    END_COUNTY = 7
    ADD_COUNTY_TALLY = 8
    END_DOCUMENT = 9
