import datetime
from dateutil import tz
import pandas as pd

from sysdata.config.private_directory import get_full_path_for_private_config
from sysobjects.production.trading_hours.trading_hours import (
    tradingHours,
    listOfTradingHours,
)
from syscore.fileutils import does_filename_exist
from sysdata.production.trading_hours import read_trading_hours
from syscore.dateutils import ISO_DATE_FORMAT

IB_CONFIG_TRADING_HOURS_FILE = "sysbrokers.IG.ig_config_trading_hours.yaml"
PRIVATE_CONFIG_TRADING_HOURS_FILE = get_full_path_for_private_config(
    "private_config_trading_hours.yaml"
)

MARKET_HOURS_DAY_COUNT = 5
DEFAULT_ZONE = "America/Chicago"


def get_saved_trading_hours():
    if does_filename_exist(PRIVATE_CONFIG_TRADING_HOURS_FILE):
        return read_trading_hours(PRIVATE_CONFIG_TRADING_HOURS_FILE)
    else:
        return read_trading_hours(IB_CONFIG_TRADING_HOURS_FILE)


def parse_trading_hours(
    trading_hours: dict,
) -> listOfTradingHours:
    now = datetime.datetime.now()
    list_of_open_times = []

    date_range = pd.date_range(now, periods=5, freq="B")
    for day in date_range:
        if trading_hours is None:
            list_of_open_times.append(
                build_hours_for_day(day, "00:00", "23:59", DEFAULT_ZONE)
            )
        else:
            for period in trading_hours.marketTimes:
                timezone = (
                    trading_hours.zone if "zone" in trading_hours else DEFAULT_ZONE
                )
                list_of_open_times.append(
                    build_hours_for_day(
                        day, period.openTime, period.closeTime, timezone
                    )
                )

    return listOfTradingHours(list_of_open_times)


def build_hours_for_day(dt: datetime, open: str, close: str, zone: str):
    day = dt.strftime("%Y-%m-%d")
    timezone = tz.gettz(zone)

    dt_open = datetime.datetime.strptime(f"{day} {open}:00", ISO_DATE_FORMAT)
    dt_open = dt_open.astimezone(timezone)
    dt_close = datetime.datetime.strptime(f"{day} {close}:00", ISO_DATE_FORMAT)
    dt_close = dt_close.astimezone(timezone)

    if dt_close < dt_open:
        return tradingHours(dt_open - datetime.timedelta(days=1), dt_close)
    else:
        return tradingHours(dt_open, dt_close)
