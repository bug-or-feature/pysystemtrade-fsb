import io
import re
import urllib.parse
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup as Scraper

from syscore.dateutils import Frequency
from syslogging.logger import *
from syscore.exceptions import missingData

BARCHART_URL = "https://www.barchart.com/"

freq_mapping = {
    Frequency.Hour: "60",
    Frequency.Minutes_15: "15",
    Frequency.Minutes_5: "5",
    Frequency.Minute: "1",
}


class bcConnection(object):

    """
    Handles connection and config for getting info from Barchart.com
    """

    def __init__(self, log=get_logger("bcConnection")):
        log.info("Setting up Barchart connection", broker="Barchart")

        # start HTTP session
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0"})
        self._log = log

    def __repr__(self):
        return f"Barchart connection: {BARCHART_URL}"

    @property
    def log(self):
        return self._log

    def get_expiry_date_for_symbol(self, bc_symbol: str):
        """
        Get the actual expiry date for the given Barchart symbol

        This implementation just scrapes the info page for the given contract to grab the date
        :param futures_contract:
        :return: str
        """
        try:
            resp = self._get_overview(bc_symbol)
            if resp.status_code == 200:
                overview_soup = Scraper(resp.text, "html.parser")
                table = overview_soup.find(
                    name="div", attrs={"class": "commodity-profile"}
                )
                label = table.find(name="div", string="Expiration Date")
                expiry_date_raw = label.next_sibling.next_sibling  # whitespace counts
                match = re.search(
                    "(\\d{2}/\\d{2}/\\d{2})", expiry_date_raw.text
                )  # TODO compile pattern?
                expiry_date_clean = match.group()
                return expiry_date_clean
            if resp.status_code == 404:
                self.log.warning(
                    f"Missing Barchart page for {bc_symbol}, unable to get expiry"
                )

        except Exception as e:
            self.log.error("Error: %s" % e)
            return None

    def get_historical_futures_data_for_contract(
        self, instr_symbol: str, bar_freq: Frequency = Frequency.Day
    ) -> pd.DataFrame:
        """
        Get historical daily data
        :param instr_symbol: contract (where instrument has barchart metadata)
        :type instr_symbol: str
        :param bar_freq: frequency of price data requested
        :type bar_freq: Frequency, one of 'Day', 'Hour', 'Minutes_15', 'Minutes_5', 'Minute', 'Seconds_10'
        :return: df
        :rtype: pandas DataFrame
        """

        if bar_freq == Frequency.Second or bar_freq == Frequency.Seconds_10:
            raise NotImplementedError(
                f"Barchart supported data frequencies: {self._valid_freqs()}"
            )

        if instr_symbol is None:
            self.log.warning(
                f"get_historical_futures_data_for_contract() instr_symbol is required"
            )
            raise missingData

        try:
            # GET the futures quote chart page, scrape to get XSRF token
            # https://www.barchart.com/futures/quotes/GCM21/interactive-chart
            chart_url = (
                BARCHART_URL + f"futures/quotes/{instr_symbol}/interactive-chart"
            )
            chart_resp = self._session.get(chart_url)
            xsrf = urllib.parse.unquote(chart_resp.cookies["XSRF-TOKEN"])

            headers = {
                "content-type": "text/plain; charset=UTF-8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": chart_url,
                "x-xsrf-token": xsrf,
            }

            payload = {
                "symbol": instr_symbol,
                "maxrecords": "640",
                "volume": "contract",
                "order": "asc",
                "dividends": "false",
                "backadjust": "false",
                "daystoexpiration": "1",
                "contractroll": "combined",
            }

            if bar_freq == Frequency.Day:
                data_url = BARCHART_URL + "proxies/timeseries/historical/queryeod.ashx"
                payload["data"] = "daily"
            else:
                data_url = (
                    BARCHART_URL + "proxies/timeseries/historical/queryminutes.ashx"
                )
                payload["interval"] = freq_mapping[bar_freq]

            # get prices for instrument from BC internal API
            prices_resp = self._session.get(data_url, headers=headers, params=payload)
            if prices_resp.status_code != 200:
                raise Exception(f"response not OK: {prices_resp.reason}")

            ratelimit = prices_resp.headers["x-ratelimit-remaining"]
            if int(ratelimit) <= 15:
                time.sleep(20)
            self.log.debug(
                f"GET {data_url} {instr_symbol}, {prices_resp.status_code}, ratelimit {ratelimit}"
            )

            # read response into dataframe
            iostr = io.StringIO(prices_resp.text)
            df = pd.read_csv(iostr, header=None)

            # convert to expected format
            price_data_as_df = self._raw_barchart_data_to_df(
                df, bar_freq=bar_freq, log=self.log
            )

            if len(price_data_as_df) == 0:
                raise missingData(
                    f"Zero length Barchart price data found for {instr_symbol}"
                )

            self.log.debug(f"Latest price {price_data_as_df.index[-1]} with {bar_freq}")

            return price_data_as_df

        except Exception as ex:
            self.log.error(f"Problem getting historical data: {ex}")
            raise missingData

    def get_exchange_for_code(self, bc_code: str, contract_code="G24"):
        """
        Get the exchange for the given Barchart code

        Scrapes the info page for the given contract to grab the exchange
        :param futures_contract:
        :return: str
        """
        try:
            resp = self._get_overview(f"{bc_code}{contract_code}")
            if resp.status_code == 200:
                overview_soup = Scraper(resp.text, "html.parser")
                table = overview_soup.find(
                    name="div", attrs={"class": "commodity-profile"}
                )
                label = table.find(name="div", string="Exchange")
                exchange_raw = label.next_sibling.next_sibling  # whitespace counts
                exchange = exchange_raw.text.strip()
                return exchange
            if resp.status_code == 404:
                self.log.warning(
                    f"Barchart page for {bc_code}{contract_code} not found"
                )

        except Exception as e:
            self.log.error("Error: %s" % e)
            return None

    @staticmethod
    def _raw_barchart_data_to_df(
        price_data_raw: pd.DataFrame,
        log,
        bar_freq: Frequency = Frequency.Day,
    ) -> pd.DataFrame:
        if price_data_raw is None:
            log.warning("No historical price data from Barchart")
            raise missingData

        date_format = "%Y-%m-%d"

        if bar_freq == Frequency.Day:
            price_data_as_df = price_data_raw.iloc[:, [1, 2, 3, 4, 5, 7]].copy()
        else:
            price_data_as_df = price_data_raw.iloc[:, [0, 2, 3, 4, 5, 6]].copy()
            date_format = "%Y-%m-%d %H:%M"

        price_data_as_df.columns = ["index", "OPEN", "HIGH", "LOW", "FINAL", "VOLUME"]
        price_data_as_df["index"] = pd.to_datetime(
            price_data_as_df["index"], format=date_format
        )
        price_data_as_df.set_index("index", inplace=True)
        price_data_as_df.index = price_data_as_df.index.tz_localize(
            tz="US/Central"
        ).tz_convert("UTC")
        price_data_as_df.index = price_data_as_df.index.tz_localize(tz=None)

        return price_data_as_df

    def _get_overview(self, contract_id):
        """
        GET the futures overview page, eg https://www.barchart.com/futures/quotes/B6M21/overview
        :param contract_id: contract identifier
        :type contract_id: str
        :return: resp
        :rtype: HTTP response object
        """
        url = BARCHART_URL + "futures/quotes/%s/overview" % contract_id
        resp = self._session.get(url)
        self.log.debug(f"GET {url}, response {resp.status_code}")
        return resp

    @staticmethod
    def _valid_freqs():
        return [v.name for i, v in enumerate(Frequency) if not i >= 6]
