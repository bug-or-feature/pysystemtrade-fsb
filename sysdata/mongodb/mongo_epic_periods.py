import pymongo

from syscore.constants import arg_not_supplied
from sysdata.mongodb.mongo_generic import mongoDataWithSingleKey

from sysdata.futures_spreadbet.epic_periods_data import epicPeriodsData
from syslogging.logger import *


COLLECTION_NAME = "epic_periods"


class mongoEpicPeriodsData(epicPeriodsData):
    """
    Read and write mongo data class for epic periods
    """

    def __init__(
        self, mongo_db=arg_not_supplied, log=get_logger("mongoEpicPeriodsData")
    ):
        super().__init__(log=log)
        mongo_data = mongoDataWithSingleKey(
            COLLECTION_NAME, "instrument_code", mongo_db=mongo_db
        )
        self._mongo_data = mongo_data

    def __repr__(self):
        return f"mongoEpicPeriodsData {str(self.mongo_data)}"

    @property
    def mongo_data(self):
        return self._mongo_data

    def update_epic_periods(self, instr_code: str, epic_periods: dict):
        self.log.debug(f"Updating epic periods for '{instr_code}'")
        self._save(instr_code, epic_periods, allow_overwrite=True)

    def add_epic_periods(self, instr_code: str, epic_periods: dict):
        self.log.debug(f"Adding epic periods for '{instr_code}'")
        self._save(instr_code, epic_periods)

    def get_epic_periods_for_instrument_code(self, instr_code: str):
        doc = self.mongo_data.collection.find_one(
            {"instrument_code": instr_code},
            {
                "_id": 0,
                "epic_periods": 1,
            },
        )
        return doc["epic_periods"]

    def get_list_of_instruments(self):
        results = []
        for doc in self.mongo_data.collection.find().sort(
            "timestamp", pymongo.ASCENDING
        ):
            results.append(doc["instrument_code"])

        return results

    def delete_epic_periods_for_instrument_code(self, instr_code: str):
        self.mongo_data.collection.delete_one({"instrument_code": instr_code})

    def _save(self, instrument_code: str, epic_periods: dict, allow_overwrite=True):
        self.mongo_data.add_data(
            instrument_code, epic_periods, allow_overwrite=allow_overwrite
        )
