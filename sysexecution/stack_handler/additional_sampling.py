from syscore.exceptions import missingData
from sysexecution.stack_handler.stackHandlerCore import stackHandlerCore
from sysobjects.contracts import futuresContract


class stackHandlerAdditionalSampling(stackHandlerCore):
    def refresh_additional_sampling_all_instruments(self):
        try:
            all_contracts = self.get_all_instruments_priced_contracts()
            # all_contracts = [futuresContract.from_two_strings("AUD_fsb","20230300")]
            for contract in all_contracts:
                self.refresh_sampling_for_contract(contract)
        except Exception as ex:
            self.data.log.error(f"Problem with additional sampling: {ex}")

    def get_all_instruments_priced_contracts(self):
        ## Cache for speed
        priced_contracts = getattr(self, "_all_priced_contracts", None)
        if priced_contracts is None:
            priced_contracts = self._get_all_instruments_priced_contracts_from_db()
            self._all_priced_contracts = priced_contracts

        return priced_contracts

    def _get_all_instruments_priced_contracts_from_db(self):
        instrument_list = self._get_all_instruments()
        data_contracts = self.data_contracts

        priced_contracts = [
            futuresContract(
                instrument_code, data_contracts.get_priced_contract_id(instrument_code)
            )
            for instrument_code in instrument_list
        ]

        return priced_contracts

    def _get_all_instruments(self):
        diag_prices = self.diag_prices
        instrument_list = diag_prices.get_list_of_instruments_in_multiple_prices()
        # instrument_list = ["FTSE100_fsb"]

        return instrument_list

    def refresh_sampling_for_contract(self, contract: futuresContract):
        okay_to_sample = self.is_contract_currently_okay_to_sample(contract)
        if not okay_to_sample:
            return None

        self.refresh_sampling_without_checks(contract)

    def is_contract_currently_okay_to_sample(self, contract: futuresContract) -> bool:
        try:
            epic = self.data.db_market_info.get_epic_for_contract(contract)
            status = self.data.db_market_info.get_status_for_epic(epic)
            okay_to_sample = status == "TRADEABLE"
            return okay_to_sample
        except:
            return False

    def refresh_sampling_without_checks(self, contract: futuresContract):
        try:
            average_spread = self.get_average_spread(contract)
        except missingData:
            pass
        else:
            self.add_spread_data_to_db(contract, average_spread)

    def get_average_spread(self, contract: futuresContract) -> float:
        data_broker = self.data_broker
        tick_data = data_broker.get_recent_bid_ask_tick_data_for_contract_object(
            contract
        )

        average_spread = tick_data.average_bid_offer_spread(remove_negative=True)

        ## Shouldn't happen, but just in case
        if average_spread < 0.0:
            raise missingData("Average spread should not be negative")

        return average_spread

    def add_spread_data_to_db(self, contract: futuresContract, average_spread: float):
        ## we store by instrument
        instrument_code = contract.instrument_code
        update_prices = self.update_prices

        update_prices.add_spread_entry(instrument_code, spread=average_spread)

    def debug_get_all_priced_epics(self):
        all_contracts = self.get_all_instruments_priced_contracts()
        # all_contracts = [futuresContract.from_two_strings("AUD_fsb", "20230900")]
        for contract in all_contracts:
            epic = self.data.db_market_info.get_epic_for_contract(contract)
            print(f"'{epic}', ")
