from sysdata.data_blob import dataBlob

from syscore.constants import arg_not_supplied
from sysproduction.reporting.reporting_functions import body_text
from sysproduction.reporting.api import reportingApi

HEADER_TEXT = body_text(
    "List of markets which should be marked as untradeable "
    "due to risk, liquidity or cost issues"
)


def remove_fsb_markets_report(
    data: dataBlob = arg_not_supplied,
):
    if data is arg_not_supplied:
        data = dataBlob()

    reporting_api = reportingApi(data)

    formatted_output = [
        reporting_api.terse_header("Remove FSB markets report"),
        HEADER_TEXT,
    ]

    list_of_func_names = [
        "body_text_existing_markets_remove",
        "body_text_removed_markets_addback",
        "body_text_expensive_markets",
        "body_text_too_safe_markets",
        "body_text_explain_safety",
        "body_text_all_recommended_bad_markets",
        "body_text_all_recommended_bad_markets_clean_slate",
    ]

    for func_name in list_of_func_names:
        func = getattr(reporting_api, func_name)
        formatted_output.append(func())
        formatted_output.append(body_text("\n\n"))

    formatted_output.append(reporting_api.footer())

    return formatted_output


if __name__ == "__main__":
    remove_fsb_markets_report()
