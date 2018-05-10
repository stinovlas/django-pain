"""Base bank statement parser module."""


class BaseBankStatementParser(object):
    """Bank statement parser."""

    def parse(self, bank_statement):
        """
        Parse bank statement.

        Each parser class has to implement this method. Result is either list
        of BankPayment objects or list of tuples.

        If result is list of tuples, first element of each tuple has to be
        BankPayment object. Other elements (if any) should be other payment
        related objects such as PaymentSymbols.

        If bank account does not exist in database, parser should raise
        BankAccount.DoesNotExist exception.
        """
        raise NotImplementedError
