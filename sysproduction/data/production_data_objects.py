# from sysdata.parquet.parquet_adjusted_prices import parquetFuturesAdjustedPricesData
# from sysdata.parquet.parquet_capital import parquetCapitalData
# from sysdata.parquet.parquet_futures_per_contract_prices import (
#     parquetFuturesContractPriceData,
# )
# from sysdata.parquet.parquet_multiple_prices import parquetFuturesMultiplePricesData
# from sysdata.parquet.parquet_spotfx_prices import parquetFxPricesData
# from sysdata.parquet.parquet_spreads import parquetSpreadsForInstrumentData
# from sysdata.parquet.parquet_optimal_positions import parquetOptimalPositionData
# from sysdata.parquet.parquet_historic_strategy_positions import (
#     parquetStrategyPositionData,
# )
# from sysdata.parquet.parquet_historic_contract_positions import (
#     parquetContractPositionData,
# )


from sysdata.arctic.arctic_adjusted_prices import arcticFuturesAdjustedPricesData
from sysdata.arctic.arctic_capital import arcticCapitalData
from sysdata.arctic.arctic_futures_per_contract_prices import (
    arcticFuturesContractPriceData,
)

# from sysdata.futures_spreadbet.mixed_futures_per_contract_prices import (
#     mixedFuturesContractPriceData,
# )
from sysdata.arctic.arctic_multiple_prices import arcticFuturesMultiplePricesData
from sysdata.arctic.arctic_spotfx_prices import arcticFxPricesData
from sysdata.arctic.arctic_optimal_positions import arcticOptimalPositionData
from sysdata.arctic.arctic_spreads import arcticSpreadsForInstrumentData
from sysdata.arctic.arctic_historic_contract_positions import arcticContractPositionData
from sysdata.arctic.arctic_historic_strategy_positions import arcticStrategyPositionData


from sysdata.arctic.arctic_fsb_epics_history import ArcticFsbEpicHistoryData
from sysdata.arctic.arctic_fsb_per_contract_prices import ArcticFsbContractPriceData

from sysdata.mongodb.mongo_futures_contracts import mongoFuturesContractData
from sysdata.mongodb.mongo_process_control import mongoControlProcessData
from sysdata.mongodb.mongo_order_stack import (
    mongoInstrumentOrderStackData,
    mongoContractOrderStackData,
    mongoBrokerOrderStackData,
)
from sysdata.mongodb.mongo_historic_orders import (
    mongoStrategyHistoricOrdersData,
    mongoContractHistoricOrdersData,
    mongoBrokerHistoricOrdersData,
)
from sysdata.mongodb.mongo_roll_state_storage import mongoRollStateData
from sysdata.mongodb.mongo_spread_costs import mongoSpreadCostData
from sysdata.mongodb.mongo_market_info import mongoMarketInfoData
from sysdata.mongodb.mongo_epic_periods import mongoEpicPeriodsData

from sysdata.csv.csv_instrument_data import csvFuturesInstrumentData
from sysdata.csv.csv_roll_parameters import csvRollParametersData

# from sysdata.config.production_config import get_production_config


FUTURES_CONTRACT_PRICE_DATA = "futures_contract_price_data"
FUTURES_MULTIPLE_PRICE_DATA = "futures_multiple_price_data"
FUTURES_ADJUSTED_PRICE_DATA = "futures_adjusted_price_data"
CAPITAL_DATA = "capital_data"
CONTRACT_POSITION_DATA = "contract_position_data"
STRATEGY_POSITION_DATA = "strategy_position_data"
OPTIMAL_POSITION_DATA = "optimal_position_data"
HISTORIC_SPREAD_DATA = "historic_spread_data"
STORED_SPREAD_DATA = "stored_spread_data"
FX_DATA = "fx_data"
ROLL_PARAMETERS_DATA = "roll_parameters_data"
FUTURES_CONTRACT_DATA = "futures_contract_data"
PROCESS_CONTROL_DATA = "process_control_data"
FUTURES_INSTRUMENT_DATA = "futures_instrument_data"
INSTRUMENT_ORDER_STACK_DATA = "instrument_order_stack_data"
CONTRACT_ORDER_STACK_DATA = "contract_order_stack_data"
BROKER_ORDER_STACK_DATA = "broker_order_stack_data"
STRATEGY_HISTORIC_ORDERS_DATA = "strategy_historic_orders_data"
CONTRACT_HISTORIC_ORDERS_DATA = "contract_historic_orders_data"
BROKER_HISTORIC_ORDERS_DATA = "broker_historic_orders_data"
ROLL_STATE_DATA = "roll_state_data"
FSB_EPIC_HISTORY_DATA = "fsb_epic_history_data"
FSB_CONTRACT_PRICE_DATA = "fsb_contract_price_data"
MARKET_INFO_DATA = "market_info_data"
EPIC_PERIODS_DATA = "epic_periods_data"

use_production_classes = {
    FX_DATA: arcticFxPricesData,
    ROLL_PARAMETERS_DATA: csvRollParametersData,
    FUTURES_INSTRUMENT_DATA: csvFuturesInstrumentData,
    FUTURES_CONTRACT_DATA: mongoFuturesContractData,
    STORED_SPREAD_DATA: mongoSpreadCostData,
    FUTURES_CONTRACT_PRICE_DATA: arcticFuturesContractPriceData,
    # FUTURES_CONTRACT_PRICE_DATA: mixedFuturesContractPriceData,
    FUTURES_MULTIPLE_PRICE_DATA: arcticFuturesMultiplePricesData,
    FUTURES_ADJUSTED_PRICE_DATA: arcticFuturesAdjustedPricesData,
    CAPITAL_DATA: arcticCapitalData,
    CONTRACT_POSITION_DATA: arcticContractPositionData,
    STRATEGY_POSITION_DATA: arcticStrategyPositionData,
    OPTIMAL_POSITION_DATA: arcticOptimalPositionData,
    HISTORIC_SPREAD_DATA: arcticSpreadsForInstrumentData,
    STRATEGY_HISTORIC_ORDERS_DATA: mongoStrategyHistoricOrdersData,
    CONTRACT_HISTORIC_ORDERS_DATA: mongoContractHistoricOrdersData,
    BROKER_HISTORIC_ORDERS_DATA: mongoBrokerHistoricOrdersData,
    INSTRUMENT_ORDER_STACK_DATA: mongoInstrumentOrderStackData,
    CONTRACT_ORDER_STACK_DATA: mongoContractOrderStackData,
    BROKER_ORDER_STACK_DATA: mongoBrokerOrderStackData,
    ROLL_STATE_DATA: mongoRollStateData,
    PROCESS_CONTROL_DATA: mongoControlProcessData,
    FSB_EPIC_HISTORY_DATA: ArcticFsbEpicHistoryData,
    FSB_CONTRACT_PRICE_DATA: ArcticFsbContractPriceData,
    MARKET_INFO_DATA: mongoMarketInfoData,
    EPIC_PERIODS_DATA: mongoEpicPeriodsData,
}


def get_class_for_data_type(data_type: str):
    # config = get_production_config().get_element_or_arg_not_supplied("use_production_classes")
    # value = config[data_type]
    # classobj = globals()[value]
    # return classobj
    return use_production_classes[data_type]
