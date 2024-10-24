"""
Custom exceptions
"""


class missingInstrument(Exception):
    pass


class missingContract(Exception):
    pass


class missingData(Exception):
    pass


class missingFile(Exception):
    pass


class marketClosed(Exception):
    pass


class fillExceedsTrade(Exception):
    pass


class existingData(Exception):
    pass


class orderCannotBeModified(Exception):
    pass


class ContractNotFound(Exception):
    pass


class orderRejected(Exception):
    pass


class spreadTooWide(Exception):
    pass
