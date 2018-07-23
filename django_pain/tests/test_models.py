"""Test models."""
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings
from djmoney.money import Money

from django_pain.models import BankAccount, BankPayment


class TestBankAccount(SimpleTestCase):
    """Test BankAccount model."""

    def test_str(self):
        """Test string representation."""
        account = BankAccount(account_number='123', currency='USD')
        self.assertEqual(str(account), '123')


class TestBankPayment(SimpleTestCase):
    """Test BankPayment model."""

    def test_constraint_success(self):
        """Test clean method with not violated constraint."""
        account = BankAccount(account_number='123', currency='USD')
        payment = BankPayment(identifier='PAYMENT', account=account, amount=Money('999.00', 'USD'))
        payment.clean()

    def test_constraint_error(self):
        """Test clean method with violated constraint."""
        account = BankAccount(account_number='123', currency='USD')
        payment = BankPayment(identifier='PAYMENT', account=account, amount=Money('999.00', 'CZK'))
        with self.assertRaises(ValidationError, msg='Bank payment PAYMENT is in different currency (CZK) '
                                                    'than bank account 123 (USD).'):
            payment.clean()

    @override_settings(PAIN_PROCESSORS=['django_pain.tests.utils.DummyPaymentProcessor'])
    def test_objective_choices(self):
        self.assertEqual(BankPayment.objective_choices(), [
            ('', '----------'),
            ('django_pain.tests.utils.DummyPaymentProcessor', 'Dummy objective'),
        ])
