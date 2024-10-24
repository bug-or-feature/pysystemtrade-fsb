import pandas as pd

from syscore.fileutils import (
    resolve_path_and_filename_for_package,
    files_with_extension_in_pathname,
)
from syscore.constants import arg_not_supplied, status, success
from syscore.pandas.pdutils import pd_readcsv
from sysdata.futures_spreadbet.fsb_epic_history_data import FsbEpicsHistoryData
from syslogging.logger import *
from sysobjects.epic_history import FsbEpicsHistory


EPIC_HISTORY_DIRECTORY = "fsb.epic_history_csv"
DATE_INDEX_NAME = "Date"


class CsvFsbEpicHistoryData(FsbEpicsHistoryData):
    def __init__(
        self,
        datapath=arg_not_supplied,
        log=get_logger("CsvFsbEpicHistoryData"),
    ):
        super().__init__(log=log)

        if datapath is arg_not_supplied:
            self._datapath = EPIC_HISTORY_DIRECTORY
        else:
            self._datapath = datapath

    def __repr__(self):
        return f"FSB epic history data from {self._datapath}"

    # @property
    # def datapath(self):
    #     return self.datapath

    def get_list_of_instruments(self) -> list:
        # return ["BUXL_fsb", "CAD_fsb", "CRUDE_W_fsb", "EUROSTX_fsb", "GOLD_fsb", "NASDAQ_fsb", "NZD_fsb", "US10_fsb"]
        return files_with_extension_in_pathname(self._datapath, ".csv")

    def get_epic_history(self, instrument_code: str) -> FsbEpicsHistory:
        df = self._read_epic_history(instrument_code)
        return FsbEpicsHistory(df)

    def update_epic_history(
        self,
        instrument_code: str,
        epic_history: FsbEpicsHistory,
        remove_duplicates=True,
    ):
        filename = self._filename_given_instrument_code(instrument_code)
        if remove_duplicates:
            epic_history = epic_history.drop_duplicates()
        epic_history.to_csv(filename, index_label="Date")

        self.log.debug(
            f"Written epic history for {instrument_code} to {filename}",
            instrument_code=instrument_code,
        )

    def _read_epic_history(self, instrument_code: str) -> pd.DataFrame:
        filename = self._filename_given_instrument_code(instrument_code)

        try:
            instr_all_price_data = pd_readcsv(filename, date_index_name=DATE_INDEX_NAME)
        except OSError:
            self.log.warning(
                f"Can't find epic history file {filename} or error reading",
                instrument_code=instrument_code,
            )
            return FsbEpicsHistory.create_empty()

        return instr_all_price_data

    def add_epics_history(
        self, instrument_code: str, epics_history: FsbEpicsHistory
    ) -> status:
        filename = self._filename_given_instrument_code(instrument_code)
        epics_history.to_csv(filename, index_label=DATE_INDEX_NAME)

        self.log.debug(
            "Written epic history prices for %s to %s" % (instrument_code, filename),
            instrument_code=instrument_code,
        )

        return success

    def _filename_given_instrument_code(self, instrument_code: str):
        return resolve_path_and_filename_for_package(
            self._datapath, f"{instrument_code}.csv"
        )
