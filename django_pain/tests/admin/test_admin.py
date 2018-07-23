"""Test admin views."""
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase, override_settings

from django_pain.admin import BankPaymentAdmin
from django_pain.constants import PaymentState
from django_pain.models import BankPayment
from django_pain.tests.utils import get_account, get_payment


@override_settings(ROOT_URLCONF='django_pain.urls')
class TestBankAccountAdmin(TestCase):
    """Test BankAccountAdmin."""

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.account = get_account(account_number='123456/0300')
        self.account.save()

    def test_get_list(self):
        """Test GET request on model list."""
        self.client.force_login(self.admin)
        response = self.client.get('/admin/django_pain/bankaccount/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '123456/0300')


@override_settings(ROOT_URLCONF='django_pain.urls')
class TestBankPaymentAdmin(TestCase):
    """Test BankAccountAdmin."""

    def setUp(self):
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.request_factory = RequestFactory()

        self.account = get_account(account_name='My Account')
        self.account.save()
        self.imported_payment = get_payment(
            identifier='My Payment 1', account=self.account, state=PaymentState.IMPORTED
        )
        self.imported_payment.save()
        self.processed_payment = get_payment(
            identifier='My Payment 2', account=self.account, state=PaymentState.PROCESSED
        )
        self.processed_payment.save()

    def test_get_list(self):
        """Test GET request on model list."""
        self.client.force_login(self.admin)
        response = self.client.get('/admin/django_pain/bankpayment/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Payment 1')
        self.assertContains(response, 'My Payment 2')

    def test_get_fieldsets(self):
        """Test get_fieldsets method."""
        modeladmin = BankPaymentAdmin(BankPayment, admin.site)
        request = self.request_factory.get('/', {})
        request.user = self.admin

        fieldsets = modeladmin.get_fieldsets(request)
        self.assertEqual(fieldsets[1][1]['fields'], ('objective',))

        fieldsets = modeladmin.get_fieldsets(request, self.imported_payment)
        self.assertEqual(fieldsets[1][1]['fields'], ('processor', 'client_id'))

        fieldsets = modeladmin.get_fieldsets(request, self.processed_payment)
        self.assertEqual(fieldsets[1][1]['fields'], ('objective',))

    def test_account_name(self):
        """Test account_name method."""
        modeladmin = BankPaymentAdmin(BankPayment, admin.site)
        self.assertEqual(modeladmin.account_name(self.imported_payment), 'My Account')
