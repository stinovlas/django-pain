"""Base bank statement parser module."""
from abc import ABC, abstractmethod


class AbstractBankStatementParser(ABC):
    """Bank statement parser."""

    @abstractmethod
    def parse(self, bank_statement):
        """
        Parse bank statement.

        Each parser class has to implement this method. Result is either iterator
        returning BankPayment objects or iterator returning sequence.

        If result is iterator of sequences, first element of each sequence has to
        be BankPayment object. Other elements (if any) should be other payment
        related objects such as PaymentSymbols.

        If bank account does not exist in database, parser should raise
        BankAccount.DoesNotExist exception.
        """
