from sysdata.config.production_config import get_production_config
from syscore.fileutils import resolve_path_and_filename_for_package
from sysdata.csv.csv_futures_contract_prices import ConfigCsvFuturesPrices

from sysinit.futures.contract_prices_from_csv_to_arctic import (
    init_db_with_csv_futures_contract_prices_for_code,
)


# Time,Open,High,Low,Close,Volume
BARCHART_CONFIG = ConfigCsvFuturesPrices(
    input_date_index_name="Time",
    input_skiprows=0,
    input_skipfooter=0,
    input_date_format="%Y-%m-%dT%H:%M:%S%z",
    input_column_mapping=dict(
        OPEN="Open", HIGH="High", LOW="Low", FINAL="Close", VOLUME="Volume"
    ),
)

BACKUP_CONFIG = ConfigCsvFuturesPrices(input_skiprows=0, input_skipfooter=1)


def transfer_barchart_prices_to_arctic_single(instr, datapath):
    init_db_with_csv_futures_contract_prices_for_code(
        instr, datapath, csv_config=BARCHART_CONFIG
    )


if __name__ == "__main__":
    input("Will overwrite existing prices are you sure?! CTL-C to abort")
    datapath = resolve_path_and_filename_for_package(
        get_production_config().get_element_or_default("barchart_path", None)
    )

    # for instr in ['FED']:
    for instr in ["BOBL", "BUND", "EDOLLAR", "OAT", "SHATZ", "US5", "US30", "US30U"]:
        transfer_barchart_prices_to_arctic_single(instr, datapath=datapath)

    # transfer_barchart_prices_to_arctic_single_contract('US10', '20221200', datapath)
