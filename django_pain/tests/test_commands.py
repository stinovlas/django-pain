"""Test management commands."""
from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from djmoney.money import Money

from django_pain.models import BankAccount, BankPayment, PaymentSymbols
from django_pain.parsers import BaseBankStatementParser


def get_payment(**kwargs):
    """Create payment object."""
    default = {
        'identifier': 'PAYMENT1',
        'account': None,
        'transaction_date': date(2018, 5, 9),
        'counter_account_number': '098765/4321',
        'amount': Money('42.00', 'CZK'),
    }
    default.update(kwargs)
    return BankPayment(**default)


class DummyPaymentsParser(BaseBankStatementParser):
    """Simple parser that just returns two fixed payments."""

    def parse(self, bank_statement):
        account = BankAccount.objects.get(account_number='123456/7890')
        return [
            get_payment(identifier='PAYMENT_1', account=account),
            get_payment(identifier='PAYMENT_2', account=account, amount=Money('370.00', 'CZK')),
        ]


class DummyExceptionParser(BaseBankStatementParser):
    """Simple parser that just throws account not exist exception."""

    def parse(self, bank_statement):
        raise BankAccount.DoesNotExist('Bank account ACCOUNT does not exist.')


class DummyPaymentsSymbolsParser(BaseBankStatementParser):
    """Simple parser that just returns fixed payment with symbols."""

    def parse(self, bank_statement):
        account = BankAccount.objects.get(account_number='123456/7890')
        payment = get_payment(identifier='PAYMENT_1', account=account)
        return [
            (payment, PaymentSymbols(payment=payment, variable_symbol='1234')),
        ]


class TestImportPayments(TestCase):
    """Test import_payments command."""

    def setUp(self):
        account = BankAccount(account_number='123456/7890', currency='CZK')
        account.save()
        self.account = account

    def test_import_payments(self):
        """Test import_payments command."""
        out = StringIO()
        call_command('import_payments', 'django_pain.tests.test_commands.DummyPaymentsParser', '--no-color', stdout=out)

        self.assertEqual(out.getvalue().strip().split('\n'), [
            'Payment ID PAYMENT_1 has been imported.',
            'Payment ID PAYMENT_2 has been imported.',
        ])

        self.assertQuerysetEqual(BankPayment.objects.values_list(
            'identifier', 'account', 'counter_account_number', 'transaction_date', 'amount', 'amount_currency'
        ), [
            ('PAYMENT_1', self.account.pk, '098765/4321', date(2018, 5, 9), Decimal('42.00'), 'CZK'),
            ('PAYMENT_2', self.account.pk, '098765/4321', date(2018, 5, 9), Decimal('370.00'), 'CZK'),
        ], transform=tuple, ordered=False)

    def test_account_not_exist(self):
        """Test command while account does not exist."""
        err = StringIO()
        with self.assertRaises(SystemExit):
            call_command('import_payments', 'django_pain.tests.test_commands.DummyExceptionParser', '--no-color',
                         stderr=err)

        self.assertEqual(err.getvalue().strip(), 'Bank account ACCOUNT does not exist.')

    def test_import_payments_with_symbols(self):
        """Test command for parser that returns payment related objects."""
        out = StringIO()
        call_command('import_payments', 'django_pain.tests.test_commands.DummyPaymentsSymbolsParser', '--no-color',
                     stdout=out)

        self.assertEqual(out.getvalue().strip(), 'Payment ID PAYMENT_1 has been imported.')

    def test_payment_already_exist(self):
        """Test command for payments that already exist in database."""
        out = StringIO()
        err = StringIO()
        call_command('import_payments', 'django_pain.tests.test_commands.DummyPaymentsParser', '--no-color', stdout=out)
        call_command('import_payments', 'django_pain.tests.test_commands.DummyPaymentsParser', '--no-color', stderr=err)

        self.assertEqual(err.getvalue().strip().split('\n'), [
            'Bank payment with this Payment ID and Account already exists.',
            'Bank payment with this Payment ID and Account already exists.',
        ])
