"""Test admin forms."""
from django.test import TestCase

from django_pain.admin.forms import BankPaymentForm
from django_pain.constants import PaymentState
from django_pain.processors import ProcessPaymentResult
from django_pain.tests.utils import DummyPaymentProcessor, get_account, get_payment


class SuccessPaymentProcessor(DummyPaymentProcessor):
    def assign_payment(self, payment, client_id):
        return ProcessPaymentResult(result=True, objective='Generous bribe')


class FailurePaymentProcessor(DummyPaymentProcessor):
    def assign_payment(self, payment, client_id):
        return ProcessPaymentResult(result=False, objective='Not so generous bribe')


class TestBankPaymentForm(TestCase):
    """Test BankPaymentForm."""

    def setUp(self):
        self.account = get_account()
        self.account.save()
        self.payment = get_payment(account=self.account, state=PaymentState.IMPORTED)
        self.payment.save()

    def test_disabled_fields(self):
        """Test disabled fields."""
        form = BankPaymentForm()
        for field in form.fields:
            if field in ('processor', 'client_id'):
                self.assertFalse(form.fields[field].disabled)
            else:
                self.assertTrue(form.fields[field].disabled)

    def test_clean_success(self):
        """Test clean method success."""
        form = BankPaymentForm(data={
            'processor': 'django_pain.tests.admin.test_forms.SuccessPaymentProcessor',
            'client_id': '',
        }, instance=self.payment)
        self.assertTrue(form.is_valid())

    def test_clean_failure(self):
        """Test clean method failure."""
        form = BankPaymentForm(data={
            'processor': 'django_pain.tests.admin.test_forms.FailurePaymentProcessor',
            'client_id': '',
        }, instance=self.payment)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'__all__': ['Unable to assign payment']})

    def test_clean_exception(self):
        """Test clean method exception."""
        form = BankPaymentForm(data={
            'processor': 'django_pain.tests.admin.test_forms.NotExistingPaymentProcessor',
            'client_id': '',
        }, instance=self.payment)
        with self.assertRaises(ImportError):
            form.is_valid()

    def test_save_processed(self):
        """Test manual assignment save method."""
        form = BankPaymentForm(data={
            'processor': 'django_pain.tests.admin.test_forms.SuccessPaymentProcessor',
            'client_id': '',
        }, instance=self.payment)
        form.is_valid()
        payment = form.save(commit=False)
        self.assertEqual(payment.state, PaymentState.PROCESSED)
        self.assertEqual(payment.objective, 'Generous bribe')
