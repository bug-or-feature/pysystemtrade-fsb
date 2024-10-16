import pandas as pd
import datetime

from syscore.pandas.merge_data_keeping_past_data import SPIKE_IN_DATA
from syscore.pandas.frequency import (
    sumup_business_days_over_pd_series_without_double_counting_of_closing_data,
)
from syscore.pandas.merge_data_keeping_past_data import merge_newer_data
from syscore.pandas.full_merge_with_replacement import full_merge_of_existing_data

PRICE_DATA_COLUMNS = sorted(
    [
        "Open.bid",
        "Open.ask",
        "High.bid",
        "High.ask",
        "Low.bid",
        "Low.ask",
        "Close.bid",
        "Close.ask",
        "Volume",
    ]
)
CLOSE_COLUMNS = ["Close.bid", "Close.ask"]
VOLUME_COLUMN = "Volume"


class FsbContractPrices(pd.DataFrame):
    """
    dataframe in specific format containing per contract FSB price information from IG
    """

    def __init__(self, price_data_as_df: pd.DataFrame):
        """
        :param data: pd.DataFrame or something that could be passed to it
        """

        _validate_price_data(price_data_as_df)
        price_data_as_df.index.name = "index"  # for arctic compatibility
        super().__init__(price_data_as_df)

    @classmethod
    def create_empty(cls):
        """
        Our graceful fail is to return an empty, but valid, dataframe
        """

        data = pd.DataFrame(columns=PRICE_DATA_COLUMNS)
        return FsbContractPrices(data)

    # @classmethod
    # def create_from_final_prices_only(
    #         cls, price_data_as_series: pd.Series
    # ):
    #     price_data_as_series = pd.DataFrame(
    #         price_data_as_series, columns=[FINAL_COLUMN]
    #     )
    #     price_data_as_series = price_data_as_series.reindex(columns=PRICE_DATA_COLUMNS)
    #     return FsbContractPrices(price_data_as_series)

    def return_final_prices(self):
        data = self[CLOSE_COLUMNS].mean(axis=1)
        return FsbContractFinalPrices(data)

    def _raw_volumes(self) -> pd.Series:
        data = self[VOLUME_COLUMN]

        return data

    def daily_volumes(self) -> pd.Series:
        volumes = self._raw_volumes()

        # stop double counting
        daily_volumes = (
            sumup_business_days_over_pd_series_without_double_counting_of_closing_data(
                volumes
            )
        )

        return daily_volumes

    def merge_with_other_prices(
        self,
        new_futures_per_contract_prices,
        only_add_rows=True,
        check_for_spike=False,
        keep_older: bool = True,
    ):
        """
        Merges self with new data.
        If only_add_rows is True,
        Otherwise: Any Nan in the existing data will be replaced (be careful!)

        :param new_futures_per_contract_prices: another futures per contract prices object
        :param keep_older: bool. Keep older data if not NaN (default). False : overwrite older data with non-NaN values. Applicable only to full merge (only_add_rows=False)
        :param check_for_spike Checks for data spikes.
        :return: merged futures_per_contract object
        """
        if only_add_rows:
            return self.add_rows_to_existing_data(
                new_futures_per_contract_prices, check_for_spike=check_for_spike
            )
        else:
            return self._full_merge_of_existing_data(
                new_futures_per_contract_prices,
                check_for_spike=check_for_spike,
                keep_older=keep_older,
            )

    def _full_merge_of_existing_data(
        self,
        new_futures_per_contract_prices,
        check_for_spike=False,
        keep_older: bool = True,
    ):
        """
        Merges self with new data.
        Any Nan in the existing data will be replaced (be careful!)

        :param new_futures_per_contract_prices: the new data
        :param check_for_spike Checks for data spikes.
        :param keep_older: bool. Keep older data (default).
        :return: updated data, doesn't update self
        """

        merged_data = full_merge_of_existing_data(
            self,
            new_futures_per_contract_prices,
            keep_older=keep_older,
            check_for_spike=check_for_spike,
            column_to_check_for_spike=CLOSE_COLUMNS[0],
        )

        if merged_data is SPIKE_IN_DATA:
            return SPIKE_IN_DATA

        return FsbContractPrices(merged_data)

    def remove_zero_volumes(self):
        new_data = self[self[VOLUME_COLUMN] > 0]
        return FsbContractPrices(new_data)

    def remove_zero_prices_if_zero_volumes(self):
        drop_it = (self[VOLUME_COLUMN] == 0) & (self[CLOSE_COLUMNS[0]] == 0.0)
        new_data = self[~drop_it]
        return FsbContractPrices(new_data)

    def remove_future_data(self):
        new_data = FsbContractPrices(self[self.index < datetime.datetime.now()])

        return new_data

    def add_rows_to_existing_data(
        self, new_futures_per_contract_prices, check_for_spike=True
    ):
        """
        Merges self with new data.
        Only newer data will be added

        :param new_futures_per_contract_prices: another futures per contract prices object

        :return: merged futures_per_contract object
        """

        merged_futures_prices = merge_newer_data(
            pd.DataFrame(self),
            new_futures_per_contract_prices,
            check_for_spike=check_for_spike,
            column_to_check_for_spike=CLOSE_COLUMNS[0],
        )

        if merged_futures_prices is SPIKE_IN_DATA:
            return SPIKE_IN_DATA

        merged_futures_prices = FsbContractPrices(merged_futures_prices)

        return merged_futures_prices


class FsbContractFinalPrices(pd.Series):
    """
    Just the final prices from a FSB contract
    """

    def __init__(self, data):
        super().__init__(data)


def _validate_price_data(data: pd.DataFrame):
    data_present = sorted(data.columns)

    try:
        assert data_present == PRICE_DATA_COLUMNS
    except AssertionError:
        raise Exception("FsbContractPrices has to conform to pattern")
