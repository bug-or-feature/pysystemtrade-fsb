import pandas as pd


def print_full(x):
    """
    Prints out a pd dataframe with no truncation, then sets display options back to their defaults
    :param x:
    :type x:
    """
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 2000)
    # pd.set_option('display.float_format', '{:20,.2f}'.format)
    pd.set_option("display.max_colwidth", None)
    print(x)
    pd.reset_option("display.max_rows")
    pd.reset_option("display.max_columns")
    pd.reset_option("display.width")
    pd.reset_option("display.float_format")
    pd.reset_option("display.max_colwidth")


if __name__ == "__main__":
    import doctest

    doctest.testmod()
