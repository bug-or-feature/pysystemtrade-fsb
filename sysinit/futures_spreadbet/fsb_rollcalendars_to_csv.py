import sys

from syscore.interactive.input import true_if_answer_is_yes
from syscore.fileutils import resolve_path_and_filename_for_package
from syscore.constants import arg_not_supplied
from syscore.pdutils import print_full
from syscore.text import remove_suffix
from sysdata.arctic.arctic_futures_per_contract_prices import (
    arcticFuturesContractPriceData,
)
from sysdata.config.production_config import get_production_config
from sysdata.csv.csv_roll_calendars import csvRollCalendarData
from sysdata.csv.csv_roll_parameters import csvRollParametersData
from sysdata.csv.csv_futures_contract_prices import csvFuturesContractPriceData
from sysobjects.roll_calendars import rollCalendar
from sysinit.futures_spreadbet.fsb_contract_prices import (
    build_import_config,
    build_norgate_import_config,
)
from sysobjects.contracts import futuresContract as fc
from sysobjects.dict_of_futures_per_contract_prices import dictFuturesContractPrices

"""
Generate a 'best guess' roll calendar based on some price data for individual contracts

"""


def build_and_write_roll_calendar(
    instrument_code,
    output_datapath=arg_not_supplied,
    check_before_writing=True,
    input_prices=arg_not_supplied,
    input_config=arg_not_supplied,
    write=True,
    use_futures=False,
    filter_after=arg_not_supplied,
):
    if output_datapath is arg_not_supplied:
        print(
            "*** WARNING *** This will overwrite the provided roll calendar. Might be better to use a temporary directory!"
        )
    else:
        if write:
            print(f"{instrument_code}: writing to {output_datapath}")

    if input_prices is arg_not_supplied:
        prices = arcticFuturesContractPriceData()
    else:
        prices = input_prices

    if input_config is arg_not_supplied:
        rollparameters = csvRollParametersData()
    else:
        rollparameters = input_config

    csv_roll_calendars = csvRollCalendarData(output_datapath)

    if use_futures:
        instrument_code = remove_suffix(instrument_code, "_fsb")
        print(f"Calculating roll calendar from futures prices: {instrument_code}")
    dict_of_all_futures_contract_prices = prices.get_merged_prices_for_instrument(
        instrument_code
    )

    if filter_after is not arg_not_supplied:
        dict_of_all_futures_contract_prices = dictFuturesContractPrices(
            [
                (
                    date_str,
                    prices,
                )
                for date_str, prices in dict_of_all_futures_contract_prices.items()
                if int(date_str) >= int(filter_after)
            ]
        )

    dict_of_futures_contract_prices = dict_of_all_futures_contract_prices.final_prices()

    roll_parameters_object = rollparameters.get_roll_parameters(
        instrument_code=instrument_code
    )

    # might take a few seconds
    print("Prepping roll calendar... might take a few seconds")
    roll_calendar = rollCalendar.create_from_prices(
        dict_of_futures_contract_prices, roll_parameters_object
    )

    # checks - this might fail
    roll_calendar.check_if_date_index_monotonic()

    # this should never fail
    roll_calendar.check_dates_are_valid_for_prices(dict_of_futures_contract_prices)

    # Write to csv
    # Will not work if an existing calendar exists

    if check_before_writing:
        check_happy_to_write = true_if_answer_is_yes(
            "Are you ok to write this csv to path %s/%s.csv? [might be worth writing and hacking manually]?"
            % (csv_roll_calendars.datapath, instrument_code)
        )
    else:
        check_happy_to_write = True

    if check_happy_to_write and write:
        print("Adding roll calendar")
        csv_roll_calendars.add_roll_calendar(
            instrument_code, roll_calendar, ignore_duplication=True
        )
    else:
        print("Not writing")

    return roll_calendar


def check_saved_roll_calendar(
    instrument_code, input_datapath=arg_not_supplied, input_prices=arg_not_supplied
):
    if input_datapath is None:
        print(
            "This will check the roll calendar in the default directory : are you are that's what you want to do?"
        )

    csv_roll_calendars = csvRollCalendarData(input_datapath)

    roll_calendar = csv_roll_calendars.get_roll_calendar(instrument_code)

    if input_prices is arg_not_supplied:
        prices = arcticFuturesContractPriceData()
    else:
        prices = input_prices

    dict_of_all_futures_contract_prices = prices.get_all_prices_for_instrument(
        instrument_code
    )
    dict_of_futures_contract_prices = dict_of_all_futures_contract_prices.final_prices()

    print(roll_calendar)

    # checks - this might fail
    roll_calendar.check_if_date_index_monotonic()

    # this should never fail
    roll_calendar.check_dates_are_valid_for_prices(dict_of_futures_contract_prices)

    return roll_calendar


def show_expected_rolls_for_config(
    instrument_code,
    path=arg_not_supplied,
    input_prices=arg_not_supplied,
    use_futures=False,
):
    rollparameters = csvRollParametersData(datapath=path)
    roll_parameters_object = rollparameters.get_roll_parameters(instrument_code)
    if input_prices is arg_not_supplied:
        prices = arcticFuturesContractPriceData()
    else:
        prices = input_prices

    if use_futures:
        instrument_code = remove_suffix(instrument_code, "_fsb")
        print(f"Calculating roll calendar from futures prices: {instrument_code}")
    dict_of_all_futures_contract_prices = prices.get_merged_prices_for_instrument(
        instrument_code
    )
    dict_of_futures_contract_prices = dict_of_all_futures_contract_prices.final_prices()
    approx_roll_calendar = rollCalendar.create_approx_from_prices(
        dict_of_futures_contract_prices, roll_parameters_object
    )

    print(f"Approx roll calendar for: {instrument_code}")
    print_full(approx_roll_calendar.tail(30))


if __name__ == "__main__":
    args = None
    if len(sys.argv) > 1:
        args = sys.argv[1]

    if args is not None:
        method = sys.argv[1]

    # XXX_fsb
    instr_code = "SONIA3_fsb"

    # run with database prices
    prices = arcticFuturesContractPriceData()

    # run with csv prices
    # prices = csvFuturesContractPriceData(
    #     datapath=resolve_path_and_filename_for_package(
    #         get_production_config().get_element_or_default("barchart_path", "")
    #         # get_production_config().get_element_or_missing_data("norgate_path")
    #         # get_production_config().get_element_or_default("backup_path", "")
    #     ),
    #     config=build_import_config(instr_code)
    #     # config=build_norgate_import_config(instr_code)
    # )

    # prices.get_prices_at_frequency_for_instrument("CHFJPY", Frequency.Day)

    # blah = prices.get_prices_at_frequency_for_contract_object(
    #     fc.from_two_strings("CHFJPY", "20210900"),
    #     Frequency.Day,
    # )

    if method == "build":
        build_and_write_roll_calendar(
            instrument_code=instr_code,
            output_datapath="fsb.roll_calendars_csv",
            input_prices=prices,
            check_before_writing=False,
            input_config=csvRollParametersData(datapath="fsb.csvconfig"),
            use_futures=False,
            filter_after="20200300",
        )
    else:
        show_expected_rolls_for_config(
            instrument_code=instr_code,
            path="fsb.csvconfig",
            input_prices=prices,
            use_futures=False,
        )

    # check_saved_roll_calendar("AUD",
    #     #input_datapath='data.futures_spreadbet.roll_calendars_csv',
    #     input_datapath='sysinit.futures.tests.data.aud',
    #     input_prices=csvFuturesContractPriceData())
