from datetime import date
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from djmoney.money import Money

from django_pain.models import BankAccount, BankPayment, PaymentSymbols
from django_pain.parsers import BaseBankStatementParser


def get_payment(**kwargs):
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

    def parse(self, bank_statement):
        account = BankAccount.objects.get(account_number='123456/7890')
        return [
            get_payment(identifier='PAYMENT_1', account=account),
            get_payment(identifier='PAYMENT_2', account=account, amount=Money('370.00', 'CZK')),
        ]


class DummyExceptionParser(BaseBankStatementParser):

    def parse(self, bank_statement):
        raise BankAccount.DoesNotExist('Bank account ACCOUNT does not exist.')


class DummyPaymentsSymbolsParser(BaseBankStatementParser):

    def parse(self, bank_statement):
        account = BankAccount.objects.get(account_number='123456/7890')
        payment = get_payment(identifier='PAYMENT_1', account=account)
        return [
            (payment, PaymentSymbols(payment=payment, variable_symbol='1234')),
        ]


class TestImportPayments(TestCase):

    def setUp(self):
        account = BankAccount(account_number='123456/7890', currency='CZK')
        account.save()
        self.account = account

    def test_import_payments(self):
        out = StringIO()
        call_command('import_payments', 'django_pain.tests.test_commands.DummyPaymentsParser', '--no-color', stdout=out)

        self.assertEqual(out.getvalue().strip().split('\n'), [
            'Payment ID PAYMENT_1 has been imported.',
            'Payment ID PAYMENT_2 has been imported.',
        ])

        payment1 = BankPayment.objects.get(identifier='PAYMENT_1')
        self.assertEqual(payment1.account, self.account)
        self.assertEqual(payment1.transaction_date, date(2018, 5, 9))
        self.assertEqual(payment1.amount, Money('42.00', 'CZK'))

        payment2 = BankPayment.objects.get(identifier='PAYMENT_2')
        self.assertEqual(payment2.account, self.account)
        self.assertEqual(payment2.transaction_date, date(2018, 5, 9))
        self.assertEqual(payment2.amount, Money('370.00', 'CZK'))

    def test_account_not_exist(self):
        err = StringIO()
        with self.assertRaises(SystemExit):
            call_command('import_payments', 'django_pain.tests.test_commands.DummyExceptionParser', '--no-color',
                         stderr=err)

        self.assertEqual(err.getvalue().strip(), 'Bank account ACCOUNT does not exist.')

    def test_import_payments_with_symbols(self):
        out = StringIO()
        call_command('import_payments', 'django_pain.tests.test_commands.DummyPaymentsSymbolsParser', '--no-color',
                     stdout=out)

        self.assertEqual(out.getvalue().strip(), 'Payment ID PAYMENT_1 has been imported.')

    def test_payment_already_exist(self):
        out = StringIO()
        err = StringIO()
        call_command('import_payments', 'django_pain.tests.test_commands.DummyPaymentsParser', '--no-color', stdout=out)
        call_command('import_payments', 'django_pain.tests.test_commands.DummyPaymentsParser', '--no-color', stderr=err)

        self.assertEqual(err.getvalue().strip().split('\n'), [
            'Payment ID PAYMENT_1 had already been imported.',
            'Payment ID PAYMENT_2 had already been imported.',
        ])
