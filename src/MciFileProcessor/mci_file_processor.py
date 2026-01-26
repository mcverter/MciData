"""Processes MCI file and produces csv"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

import pdfplumber

from src.finite_machine_states.fsm_state import FsmState
from src.lines.lines import LineType, get_line_type_and_matches
from src.PropertyMci.address import Address
from src.PropertyMci.docket import Docket
from src.PropertyMci.property_mci import PropertyMci
from src.PropertyMci.work_item import WorkItem

if TYPE_CHECKING:
    import re


class MciFileProcessor:
    """Processes MCI file and produces csv"""

    current_docket: Docket | None

    def __init__(self, filepath: str) -> None:
        super().__init__()
        self.filepath = filepath

        # Track state of document processing
        self.fsm_state = FsmState.START_DOCUMENT

        # Record MCI Items
        self.current_address: Address | None = None
        self.current_docket: Docket | None = None
        self.current_work_item: WorkItem | None = None
        self.all_mcis: list[PropertyMci] = []

        # Validate results
        self.current_county: str | None = None
        self.county_counts = defaultdict(int)

    def add_new_property_mci(
        self, previous_work_item_can_be_blank: bool = False
    ) -> None:
        """
        Adds a new PropertyMci to array.
        Ensures that all required fields are supplied and that added PropertyMci is not a duplicate

        @param: previous_work_item_can_be_blank --
        The majority of PropertyMCIs are added when a Work Line is processed
        However, some properties have dockets with no Work Items.
        Such PropertyMCIs are added as soon as a new property is started
        or the end of the county section is encountered.
        For such cases, this parameter is set to True
        """
        # Ensure that Property MCI has all the required fields
        has_address_and_docket = self.current_address and self.current_docket
        # some dockets have no work orders at all
        has_work_order_or_null_work_order_allowed = (
            self.current_work_item or previous_work_item_can_be_blank
        )

        # Ensure that PropertyMCI is not a duplicate
        is_first_mci = (
            has_address_and_docket
            and has_work_order_or_null_work_order_allowed
            and len(self.all_mcis) == 0
        )
        is_different_from_previous_mci_and_previous_work_null = (
            previous_work_item_can_be_blank
            and has_address_and_docket
            and len(self.all_mcis) > 0
            and (
                self.all_mcis[-1].docket != self.current_docket
                or self.all_mcis[-1].address != self.current_address
            )
        )
        is_different_from_previous_mci_and_previous_work_not_null = (
            not previous_work_item_can_be_blank
            and has_address_and_docket
            and len(self.all_mcis) > 0
            and (
                self.all_mcis[-1].docket != self.current_docket
                or self.all_mcis[-1].address != self.current_address
                or self.all_mcis[-1].work_item != self.current_work_item
            )
        )

        should_add_property_mci = (
            is_first_mci
            or is_different_from_previous_mci_and_previous_work_not_null
            or is_different_from_previous_mci_and_previous_work_null
        )

        if should_add_property_mci and self.current_docket and self.current_address:
            self.all_mcis.append(
                PropertyMci(
                    address=self.current_address,
                    docket=self.current_docket,
                    work_item=self.current_work_item,
                )
            )
        self.current_work_item = None

    def set_street_address(self, line_matches: re.Match[str]) -> None:
        """Sets the street Address"""
        self.current_address = Address(street_address=line_matches.group(0))

    def set_property_county_and_docket(self, line_matches: re.Match[str]) -> None:
        """Completes Address information (borough, zip code) and adds Docket information"""
        if not self.current_address:
            raise Exception("Can't set borough because Address is not yet initialized")
        (
            neighborhood,
            zip_code,
            docket_no,
            case_status,
            closing_date,
            close_code,
            mci_per_room,
        ) = line_matches.groups()
        self.current_address.neighborhood = neighborhood
        self.current_address.county = self.current_county
        self.current_address.zip_code = zip_code
        self.current_docket = Docket(
            docket_number=docket_no,
            case_status=case_status,
            close_code=close_code,
            closing_date=closing_date,
            monthly_mci_incr_per_room=mci_per_room.lstrip() if mci_per_room else "",
        )

    def set_docket(self, line_matches: re.Match[str]) -> None:
        """Sets new Docket information for property that had used a different Docket"""
        (
            docket_no,
            case_status,
            closing_date,
            close_code,
            mci_per_room,
        ) = line_matches.groups()

        self.current_docket = Docket(
            docket_number=docket_no,
            case_status=case_status,
            close_code=close_code,
            closing_date=closing_date,
            monthly_mci_incr_per_room=mci_per_room.lstrip() if mci_per_room else "",
        )

    def set_work_line(self, line_matches: re.Match[str]) -> None:
        """Sets work type and costs"""
        mci_work, claim_cost, allow_cost = line_matches.groups()

        self.current_work_item = WorkItem(
            mci_work=mci_work,
            claim_cost=claim_cost,
            allow_cost=allow_cost.lstrip() if allow_cost is not None else "",
        )

    def set_page_county(self, line_matches: re.Match[str]) -> None:
        """To check county tallies, we set the current county being recorded"""
        self.current_county = line_matches.group(1)

    def increment_county_count(self) -> None:
        self.county_counts[self.current_county] += 1

    def check_county_count(self, line_matches: re.Match[str]) -> None:
        """Make sure county count equals number given at end of section"""
        count = int(line_matches.group(1))
        if self.county_counts[self.current_county] != count:
            raise Exception(f"County count mismatch for {self.current_county} county")

    def recheck_county_count(self, line_matches: re.Match[str]) -> None:
        """Make sure county count equals number given at end of full report"""
        county = line_matches.group(1)
        count = int(line_matches.group(2))
        if self.county_counts[county] != count:
            raise Exception(f"County count mismatch for {county} county")

    def check_document_tally(self, line_matches: re.Match[str]) -> None:
        """Ensure total number of properties equals number given in report"""
        count = int(line_matches.group(1))
        if count != sum(self.county_counts.values()):
            raise Exception("Total document count mismatch")

    def check_line_type_against_current_state(self, line_type: LineType) -> bool:
        """TODO"""
        """Verifies that the line type is appropriate for current FSM state"""
        if line_type and self.fsm_state:
            return True
        return False

    def process_file(self) -> list[PropertyMci]:
        """
        Processes all pages of pdf to construct a list of PropertyMCIs
        :return: List of PropertyMCIs derived from file
        """
        file_text = ""
        with pdfplumber.open(self.filepath) as pdf:
            for page in pdf.pages:
                file_text += page.extract_text()
        pdf.close()
        lines = file_text.split("\n")

        for line in lines:
            self.process_line(line)
        return self.all_mcis

    def process_line(self, line: str) -> None:
        """
        Processes each line of pdf in order to build a PropertyMCI and add it to internal list
        """
        line_type, line_matches = get_line_type_and_matches(line)

        if (
            line_type
            in [
                LineType.NO_LINE,
                LineType.NYS_DIVISION_HEADER,
                LineType.MAJOR_CAPITAL_HEADER,
                LineType.COLUMN_HEADER_1,
                LineType.COLUMN_HEADER_2,
                LineType.DASHES,
                LineType.DOUBLE_DASHES,
                LineType.OFFICE_OF_RENT_HEADER,
            ]
            or not line_matches
        ):
            return

        if not self.check_line_type_against_current_state(line_type):
            raise Exception(
                f"Unexpected line type {line_type} for current state {self.fsm_state}. Line is {line}"
            )

        match line_type:
            case LineType.STREET_ADDRESS_LINE:
                # Check whether we have concluded a docket with no work item when we encounter a new property
                self.add_new_property_mci(previous_work_item_can_be_blank=True)
                self.set_street_address(line_matches)
                self.fsm_state = FsmState.START_PROPERTY

            case LineType.BOROUGH_DOCKET_LINE:
                self.fsm_state = FsmState.UPDATE_DOCKET
                self.increment_county_count()
                self.set_property_county_and_docket(line_matches)

            # Docket Line indicates new docket number for previously used address
            case LineType.DOCKET_LINE:
                self.fsm_state = FsmState.UPDATE_DOCKET
                self.increment_county_count()
                self.set_docket(line_matches)

            case LineType.MCI_WORK_LINE:
                self.fsm_state = FsmState.ADD_WORK_ITEM
                self.set_work_line(line_matches)
                # Add MCI for each work line
                self.add_new_property_mci()

            case LineType.TOTAL_CASES_COUNTY_LINE:
                # Check whether we have concluded a docket with no work item when we reach County tally
                self.add_new_property_mci(previous_work_item_can_be_blank=True)
                self.check_county_count(line_matches)
                self.fsm_state = FsmState.END_COUNTY

            case LineType.COUNTY_DATE_HEADER:
                self.fsm_state = FsmState.START_COUNTY
                self.set_page_county(line_matches)

            case LineType.COUNT_PER_COUNTY_LINE:
                self.recheck_county_count(line_matches)

            case LineType.TOTAL_CASES_DOCUMENT_LINE:
                self.check_document_tally(line_matches)
                self.fsm_state = FsmState.END_DOCUMENT

            case _:
                raise Exception(f"Unexpected line type encountered. Line is ${line}")
