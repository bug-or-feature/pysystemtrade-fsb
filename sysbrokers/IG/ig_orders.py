from sysbrokers.broker_execution_stack import brokerExecutionStackData
from sysbrokers.IG.ig_translate_broker_order_objects import IgTradeWithContract
from sysbrokers.IG.ig_connection import IGConnection
from sysbrokers.IG.ig_utils import convert_ig_date
from syscore.constants import arg_not_supplied, success
from sysdata.data_blob import dataBlob
from sysdata.futures.contracts import futuresContractData
from sysdata.futures.instruments import futuresInstrumentData
from sysdata.futures_spreadbet.market_info_data import marketInfoData
from sysexecution.order_stacks.broker_order_stack import orderWithControls
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.orders.list_of_orders import listOfOrders
from sysexecution.orders.named_order_objects import missing_order
from sysexecution.tick_data import tickerObject
from sysexecution.trade_qty import tradeQuantity
from syslogging.logger import *


class IgOrderWithControls(orderWithControls):
    def __init__(
        self,
        trade_result: IgTradeWithContract,
        broker_conn: IGConnection,
        broker_order: brokerOrder = None,
        instrument_code: str = None,
        ticker_object: tickerObject = None,
    ):
        if broker_order is None:
            # This might happen if for example we are getting the orders from
            #   IB
            # broker_order = create_broker_order_from_trade_with_contract(
            #     trade_result, instrument_code
            # )

            print("Hopefully this scenario not needed yet for FSBs")

        super().__init__(
            control_object=trade_result,
            broker_order=broker_order,
            ticker_object=ticker_object,
        )

        self._broker_conn = broker_conn

    @property
    def trade_with_contract_from_IB(self):
        return self._control_object

    @property
    def broker_connection(self) -> IGConnection:
        return self._broker_conn

    def update_order(self):
        # Update the broker order using the control object
        # Can be used when first submitted, or when polling objects
        # Basically copies across the details from the control object that are
        # likely to be updated

        # self.ibclient.refresh()
        # ib_broker_order = create_broker_order_from_trade_with_contract(
        #     self.trade_with_contract_from_IB, self.order.instrument_code
        # )
        updated_broker_order = add_trade_info_to_broker_order(
            self.order, self.control_object
        )

        self._order = updated_broker_order

    def broker_limit_price(self):
        raise NotImplementedError("Not implemented! build it now")
        # self.ibclient.refresh()
        # ib_broker_order = create_broker_order_from_trade_with_contract(
        #     self.trade_with_contract_from_IB, self.order.instrument_code
        # )
        # if ib_broker_order.limit_price == 0.0:
        #     broker_limit_price = None
        # else:
        #     broker_limit_price = ib_broker_order.limit_price
        #
        # return broker_limit_price


class IgExecutionStackData(brokerExecutionStackData):
    def __init__(
        self,
        broker_conn: IGConnection,
        data: dataBlob,
        log=get_logger("IgExecutionStackData"),
    ):
        super().__init__(log=log, data=data)
        self._broker_conn = broker_conn

    def __repr__(self):
        return f"IG orders {self.broker_conn}"

    @property
    def broker_conn(self) -> IGConnection:
        return self._broker_conn

    @property
    def traded_object_store(self) -> dict:
        store = getattr(self, "_traded_object_store", None)
        if store is None:
            store = self._traded_object_store = {}

        return store

    def _add_order_with_controls_to_store(
        self, order_with_controls: IgOrderWithControls
    ):
        storage_key = order_with_controls.order.broker_tempid
        self.traded_object_store[storage_key] = order_with_controls

    @property
    def futures_contract_data(self) -> futuresContractData:
        return self.data.broker_futures_contract

    @property
    def futures_instrument_data(self) -> futuresInstrumentData:
        return self.data.broker_futures_instrument

    @property
    def market_info_data(self) -> marketInfoData:
        return self.data.db_market_info

    def get_list_of_broker_orders_with_account_id(
        self, account_id: str = arg_not_supplied
    ) -> listOfOrders:
        # list_of_control_objects = self._get_list_of_broker_control_orders(
        #     account_id=account_id
        # )
        # order_list = [
        #     order_with_control.order for order_with_control in list_of_control_objects
        # ]
        #
        # order_list = listOfOrders(order_list)

        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=3)
        filter = "type==POSITION"

        orders_df = self.broker_conn.get_activity(start, end, filter=filter)

        order_records = orders_df.to_dict(orient="records")

        orders = []
        for rec in order_records:
            epic = rec["epic"]
            if rec["period"] == "DFB":
                continue
            else:
                period_date = datetime.datetime.strptime(
                    f"01-{rec['period']}", "%d-%b-%y"
                )
                contract = f"{period_date.strftime('%Y%m')}00"

            direction = rec["direction"]
            if direction == "BUY":
                fill_qty = tradeQuantity(float(rec["size"]))
            else:
                fill_qty = tradeQuantity(-float(rec["size"]))

            trade = brokerOrder(
                "",
                self.data.db_market_info.instr_code[epic],
                contract,
                fill_qty,
                fill=fill_qty,
                filled_price=float(rec["level"]),
                fill_datetime=rec["date"],
                commission=0.0,
            )

            orders.append(trade)

        order_list = listOfOrders(orders)

        return order_list

    def _get_dict_of_broker_control_orders(
        self, account_id: str = arg_not_supplied
    ) -> dict:
        raise NotImplementedError("Not implemented! build it now")

    # def _get_list_of_broker_control_orders(
    #     self, account_id: str = arg_not_supplied
    # ) -> list:
    #     """
    #     Get list of broker orders from IG, and return as list of orders with controls
    #
    #     :return: list of brokerOrder objects
    #     """
    #
    #     list_of_raw_orders_as_trade_objects = self.broker_conn.broker_get_orders(
    #         account_id=account_id
    #     )
    #
    #     broker_order_with_controls_list = [
    #         self._create_broker_control_order_object(broker_trade_object_results)
    #         for broker_trade_object_results in list_of_raw_orders_as_trade_objects
    #     ]
    #
    #     broker_order_with_controls_list = [
    #         broker_order_with_controls
    #         for broker_order_with_controls in broker_order_with_controls_list
    #         if broker_order_with_controls is not missing_order
    #     ]
    #
    #     return broker_order_with_controls_list

    def _create_broker_control_order_object(
        self, trade_with_contract_from_broker: IgTradeWithContract
    ):
        raise NotImplementedError("Not implemented! build it now")

    def get_list_of_orders_from_storage(self) -> listOfOrders:
        dict_of_stored_orders = self._get_dict_of_orders_from_storage()
        list_of_orders = listOfOrders(dict_of_stored_orders.values())

        return list_of_orders

    def _get_dict_of_orders_from_storage(self) -> dict:
        raise NotImplementedError("Not implemented! build it now")

    def _get_dict_of_control_orders_from_storage(self) -> dict:
        raise NotImplementedError("Not implemented! build it now")

    def put_order_on_stack(self, broker_order: brokerOrder) -> IgOrderWithControls:
        """
        :param broker_order: key properties are instrument_code, contract_id, quantity
        :return: ibOrderWithControls or missing_order
        """

        epic = self.market_info_data.get_epic_for_contract(
            broker_order.futures_contract
        )
        expiry_info = self.market_info_data.get_expiry_details(epic)

        broker_order.order_info["epic"] = epic
        broker_order.order_info["expiry_key"] = expiry_info[0]

        order_result = self._send_broker_order_to_ig(broker_order)
        order_time = datetime.datetime.now()

        if order_result is missing_order:
            return missing_order

        placed_broker_order_with_controls = IgOrderWithControls(
            order_result,
            broker_conn=self.broker_conn,
            broker_order=broker_order,
        )

        placed_broker_order_with_controls.order.submit_datetime = order_time

        # We do this so the tempid is accurate
        placed_broker_order_with_controls.update_order()

        # We do this so we can cancel stuff and get things back more easily
        self._add_order_with_controls_to_store(placed_broker_order_with_controls)

        return placed_broker_order_with_controls

    def _send_broker_order_to_ig(
        self, broker_order: brokerOrder
    ) -> IgTradeWithContract:
        """
        :param broker_order: key properties are instrument_code, contract_id, quantity
        :return: tradeWithContract object or missing_order
        """

        log_attrs = {**broker_order.log_attributes(), "method": "temp"}
        self.log.debug(
            "Going to submit order %s to IG" % str(broker_order),
            **log_attrs,
        )

        trade_list = broker_order.trade
        order_type = broker_order.order_type
        limit_price = broker_order.limit_price
        epic = broker_order.order_info["epic"]
        expiry_key = broker_order.order_info["expiry_key"]

        try:
            placed_broker_trade_object = self.broker_conn.broker_submit_order(
                trade_list=trade_list,
                epic=epic,
                expiry_key=expiry_key,
                order_type=order_type,
                limit_price=limit_price,
            )
        except Exception as exc:
            self.log.warning(f"Problem submitting broker order: {exc}", **log_attrs)
            placed_broker_trade_object = missing_order

        if placed_broker_trade_object is missing_order:
            self.log.warning("Couldn't submit order", **log_attrs)
            return missing_order

        self.log.debug("Order submitted to IG", **log_attrs)

        return placed_broker_trade_object

    def match_db_broker_order_to_order_from_brokers(
        self, broker_order_to_match: brokerOrder
    ) -> brokerOrder:
        raise NotImplementedError("Not implemented! build it now")

    def match_db_broker_order_to_control_order_from_brokers(
        self, broker_order_to_match: brokerOrder
    ) -> IgOrderWithControls:
        raise NotImplementedError("Not implemented! build it now")

    def cancel_order_on_stack(self, broker_order: brokerOrder):
        raise NotImplementedError("Not implemented! build it now")

    def cancel_order_given_control_object(
        self, broker_orders_with_controls: IgOrderWithControls
    ):
        original_order_object = broker_orders_with_controls.control_object.trade.order
        print(f"cancel_order_given_control_object(): {original_order_object}")
        # nothing to do here with IG market orders, will need later for limit orders
        # self.ib_client.ib_cancel_order(original_order_object)

        return success

    def check_order_is_cancelled(self, broker_order: brokerOrder) -> bool:
        raise NotImplementedError("Not implemented! build it now")

    def check_order_is_cancelled_given_control_object(
        self, broker_order_with_controls: IgOrderWithControls
    ) -> bool:
        status = self.get_status_for_control_object(broker_order_with_controls)
        cancellation_status = status == "REJECTED"

        return cancellation_status

    def _get_status_for_trade_object(self, original_trade_object) -> str:
        return original_trade_object.orderStatus.status

    def modify_limit_price_given_control_object(
        self, broker_order_with_controls: IgOrderWithControls, new_limit_price: float
    ) -> IgOrderWithControls:
        raise NotImplementedError("Not implemented! build it now")

    def check_order_can_be_modified_given_control_object_throw_error_if_not(
        self, broker_order_with_controls: IgOrderWithControls
    ):
        raise NotImplementedError("Not implemented! build it now")

    def get_status_for_control_object(
        self, broker_order_with_controls: IgOrderWithControls
    ) -> str:
        control_object = broker_order_with_controls.control_object
        status = control_object.get_attr("dealStatus")

        return status

    def get_recent_activity(self, start, end, filter):
        return self._broker_conn.get_activity(start, end, filter=filter)


def add_trade_info_to_broker_order(
    broker_order: brokerOrder, broker_order_result
) -> brokerOrder:
    new_broker_order = copy(broker_order)

    # SUCCESS
    # {
    #   'date': '2023-07-21T07:57:09.021', 'status': 'OPEN', 'reason': 'SUCCESS',
    #   'dealStatus': 'ACCEPTED', 'epic': 'IR.D.FGBL.Month1.IP', 'expiry': 'SEP-23',
    #   'dealReference': 'PUSMEZ6C32STYQ3', 'dealId': 'DIAAAAMWCJP4CA6',
    #   'affectedDeals': [
    #       {'dealId': 'DIAAAAMWCJP4CA6', 'status': 'OPENED'}
    #   ],
    #   'level': 13301.0, 'size': 2.38, 'direction': 'BUY', 'stopLevel': None,
    #   'limitLevel': None, 'stopDistance': None, 'limitDistance': None,
    #   'guaranteedStop': False, 'trailingStop': False, 'profit': None,
    #   'profitCurrency': None
    # }

    # FAILURE
    # {
    #     'date': '2023-07-25T00:15:04.265', 'status': None,
    #     'reason': 'MARKET_CLOSED_WITH_EDITS', 'dealStatus': 'REJECTED', 'epic':
    #     'CO.D.KC.Month1.IP', 'expiry': None,
    #     'dealReference': 'N42RA9MXX3STYQ3', 'dealId': 'DIAAAAMWV8MMEA2',
    #     'affectedDeals': [], 'level': None, 'size': None, 'direction': 'BUY',
    #     'stopLevel': None, 'limitLevel': None, 'stopDistance': None,
    #     'limitDistance': None, 'guaranteedStop': False, 'trailingStop': False,
    #     'profit': None, 'profitCurrency': None
    # }

    trade_result = broker_order_result._attrs

    success = True if trade_result["dealStatus"] == "ACCEPTED" else False

    # dealReference: id returned by IG in response to open order request. You make
    # another request to /confirms with this ID to get status, eg
    #     /confirms/VN68DYYNHVYTYP5

    # dealId is the (supposedly) unique ID per transaction. So for a normal buy/sell
    # trade there would be two. Currently /confirms on a close returns the wrong one.
    # /history/activity and /history/transactions report correctly

    new_broker_order.broker_tempid = trade_result["dealReference"]
    new_broker_order.broker_permid = trade_result["dealId"]

    if success:
        new_broker_order.order_info["affected_deals"] = trade_result["affectedDeals"]
        size = float(trade_result["size"])
        if trade_result["direction"] == "SELL":
            size = -size
        new_broker_order.fill_order(
            tradeQuantity(size),
            float(trade_result["level"]),
            convert_ig_date(trade_result["date"]),
        )

    else:
        new_broker_order.algo_comment = (
            f"{trade_result['dealStatus']}: {trade_result['reason']}"
        )
        new_broker_order.submit_datetime = convert_ig_date(trade_result["date"])
        new_broker_order.deactivate()

    return new_broker_order
