"""
Called from sysproduction code in a while loop, each time it runs loops over strategies
For each strategy gets the required trades per instrument
It then passes these to the 'virtual' order queue
So called because it deals with instrument level trades, not contract implementation
"""

from sysexecution.orders.named_order_objects import zero_order
from sysdata.data_blob import dataBlob

from sysexecution.orders.list_of_orders import listOfOrders
from sysexecution.orders.instrument_orders import instrumentOrder
from sysexecution.order_stacks.instrument_order_stack import (
    zeroOrderException,
    minBetException,
)
from syslogging.logger import *
from sysproduction.data.positions import diagPositions
from sysproduction.data.orders import dataOrders
from sysproduction.data.controls import diagOverrides, dataLocks, dataPositionLimits
from sysproduction.data.fsb_instruments import diagFsbInstruments

name_of_main_generator_method = "get_and_place_orders"


class orderGeneratorForStrategy(object):
    """

    Order generators are strategy specific but have common methods used by the order handler

    """

    def __init__(self, data: dataBlob, strategy_name: str):
        self._strategy_name = strategy_name
        self._data = data
        data_orders = dataOrders(data)
        self._log = data.log
        self._data_orders = data_orders
        self._diag_instruments = diagFsbInstruments(self._data)

    @property
    def data(self) -> dataBlob:
        return self._data

    @property
    def strategy_name(self) -> str:
        return self._strategy_name

    @property
    def log(self):
        return self._log

    @property
    def data_orders(self):
        return self._data_orders

    @property
    def order_stack(self):
        return self.data_orders.db_instrument_stack_data

    @property
    def diag_instruments(self):
        return self._diag_instruments

    def get_and_place_orders(self):
        # THIS IS THE MAIN FUNCTION THAT IS RUN
        order_list = self.get_required_orders()
        order_list_with_overrides = self.apply_overrides_and_position_limits(order_list)
        self.submit_order_list(order_list_with_overrides)

    def get_required_orders(self) -> listOfOrders:
        raise Exception(
            "Need to inherit with a specific method for your type of strategy"
        )

    def get_actual_positions_for_strategy(self) -> dict:
        """
        Actual positions held by a strategy

        Useful to know, usually

        :return: dict, keys are instrument codes, values are positions
        """
        data = self.data
        strategy_name = self.strategy_name

        diag_positions = diagPositions(data)
        actual_positions = diag_positions.get_dict_of_actual_positions_for_strategy(
            strategy_name
        )

        return actual_positions

    def apply_overrides_and_position_limits(
        self, order_list: listOfOrders
    ) -> listOfOrders:
        new_order_list = [
            self.apply_overrides_and_position_limits_for_instrument_and_strategy(
                proposed_order
            )
            for proposed_order in order_list
        ]
        new_order_list = listOfOrders(new_order_list)

        return new_order_list

    def apply_overrides_and_position_limits_for_instrument_and_strategy(
        self, proposed_order: instrumentOrder
    ) -> instrumentOrder:
        revised_order = self.apply_overrides_for_instrument_and_strategy(proposed_order)
        new_order = self.adjust_order_for_position_limits(revised_order)

        return new_order

    def apply_overrides_for_instrument_and_strategy(
        self, proposed_order: instrumentOrder
    ) -> instrumentOrder:
        """
        Apply an override to a trade

        :param strategy_name: str
        :param instrument_code: str
        :return: int, updated position
        """

        diag_overrides = diagOverrides(self.data)
        diag_positions = diagPositions(self.data)

        instrument_strategy = proposed_order.instrument_strategy

        original_position = diag_positions.get_current_position_for_instrument_strategy(
            instrument_strategy
        )

        override = diag_overrides.get_cumulative_override_for_instrument_strategy(
            instrument_strategy
        )

        revised_order = override.apply_override(original_position, proposed_order)

        if revised_order.trade != proposed_order.trade:
            self.log.debug(
                "%s trade change from %s to %s because of override %s"
                % (
                    instrument_strategy.key,
                    str(revised_order.trade),
                    str(proposed_order.trade),
                    str(override),
                ),
                **proposed_order.log_attributes(),
                method="temp",
            )

        return revised_order

    def adjust_order_for_position_limits(
        self, order: instrumentOrder
    ) -> instrumentOrder:
        log_attrs = {**order.log_attributes(), "method": "temp"}

        data_position_limits = dataPositionLimits(self.data)
        new_order = data_position_limits.apply_position_limit_to_order(order)

        if new_order.trade != order.trade:
            if new_order.is_zero_trade():
                ## at position limit, can't do anything
                self.log.warning(
                    "Can't trade at all because of position limits %s" % str(order),
                    **log_attrs,
                )
            else:
                self.log.warning(
                    "Can't do trade of %s because of position limits,instead will do %s"
                    % (str(order), str(new_order.trade)),
                    **log_attrs,
                )

        return new_order

    def submit_order_list(self, order_list: listOfOrders):
        data_lock = dataLocks(self.data)
        for order in order_list:
            # try:
            # we allow existing orders to be modified
            log_attrs = {**order.log_attributes(), "method": "temp"}
            self.log.debug("Required order %s" % str(order), **log_attrs)

            instrument_locked = data_lock.is_instrument_locked(order.instrument_code)
            if instrument_locked:
                self.log.debug("Instrument locked, not submitting", **log_attrs)
                continue
            self.submit_order(order, test_mode=False)

    def submit_order(self, order: instrumentOrder, test_mode=False):
        log_attrs = {**order.log_attributes(), "method": "temp"}

        try:
            min_bet = self.diag_instruments.get_minimum_bet(
                order.instrument_code, self.log.name
            )
            if abs(order.as_single_trade_qty_or_error()) < min_bet:
                error_msg = (
                    f"Order size is "
                    f"{order.as_single_trade_qty_or_error()}, "
                    f"but min bet is {min_bet}",
                )
                self.log.warning(error_msg, **log_attrs)
                raise minBetException(error_msg)

            order_id = 0 if test_mode else self.order_stack.put_order_on_stack(order)
            log_attrs[INSTRUMENT_ORDER_ID_LABEL] = order_id
        except zeroOrderException:
            # we checked for zero already, which means that there is an existing order
            # on the stack
            # An existing order of the same size
            self.log.warning(
                "Ignoring new order as either zero size or it replicates an existing "
                "order on the stack",
                **log_attrs,
            )
        except minBetException:
            # less than minimum bet
            self.log.warning(
                "Ignoring new order as it is less than the minimum bet",
                **log_attrs,
            )

        else:
            if test_mode:
                self.log.debug(f"TEST MODE: not submitting order {order}", **log_attrs)
            else:
                self.log.debug(
                    "Added order %s to instrument order stack with order id %d"
                    % (str(order), order_id),
                    **log_attrs,
                )
