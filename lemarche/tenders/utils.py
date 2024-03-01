from lemarche.tenders import constants as tender_constants


def find_amount_ranges(amount, operation):
    """
    Returns the keys from AMOUNT_RANGE that match a given operation on a specified amount.

    :param amount: The amount to compare against.
    :param operation: The operation to perform ('lt', 'lte', 'gt', 'gte').
    :return: A list of matching keys.
    """
    amount = int(amount)
    if operation == "lt":
        if amount < tender_constants.AMOUNT_RANGE_CHOICE_EXACT.get(tender_constants.AMOUNT_RANGE_0_1):
            return [tender_constants.AMOUNT_RANGE_0_1]
        return [key for key, value in tender_constants.AMOUNT_RANGE_CHOICE_EXACT.items() if value < amount]
    elif operation == "lte":
        if amount <= tender_constants.AMOUNT_RANGE_CHOICE_EXACT.get(tender_constants.AMOUNT_RANGE_0_1):
            return [tender_constants.AMOUNT_RANGE_0_1]
        return [key for key, value in tender_constants.AMOUNT_RANGE_CHOICE_EXACT.items() if value <= amount]
    elif operation == "gt":
        if amount >= tender_constants.AMOUNT_RANGE_CHOICE_EXACT.get(tender_constants.AMOUNT_RANGE_1000_MORE):
            return [tender_constants.AMOUNT_RANGE_1000_MORE]
        return [key for key, value in tender_constants.AMOUNT_RANGE_CHOICE_EXACT.items() if value > amount]
    elif operation == "gte":
        if amount >= tender_constants.AMOUNT_RANGE_CHOICE_EXACT.get(tender_constants.AMOUNT_RANGE_1000_MORE):
            return [tender_constants.AMOUNT_RANGE_1000_MORE]
        return [key for key, value in tender_constants.AMOUNT_RANGE_CHOICE_EXACT.items() if value >= amount]
    else:
        raise ValueError("Unrecognized operation. Use 'lt', 'lte', 'gt', or 'gte'.")
