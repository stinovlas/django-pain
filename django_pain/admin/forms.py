"""Django admin forms."""
from django import forms
from django.utils import module_loading
from django.utils.translation import gettext as _
from djmoney.forms.fields import MoneyField
from djmoney.settings import CURRENCY_CHOICES

from django_pain.constants import PaymentState
from django_pain.models import BankAccount, BankPayment


class FixedMoneyField(MoneyField):
    """
    Fix MoneyField from django-money.

    MoneyField is subclass of MultiValueField, which expects field value to be
    instance of tuple or list. Money is neither, so we have to fix the clean
    method and convert Money value to tuple.
    """

    def clean(self, value):
        """Convert Money to tuple."""
        return super().clean(value=(value.amount, value.currency))


class BankAccountForm(forms.ModelForm):
    """Admin form for BankAccount model."""

    class Meta:
        """Meta class."""

        fields = '__all__'
        model = BankAccount
        widgets = {
            'account_number': forms.TextInput(),
            'account_name': forms.TextInput(),
            'currency': forms.Select(choices=CURRENCY_CHOICES),
        }


class BankPaymentForm(forms.ModelForm):
    """Admin form for BankPayment model."""

    amount = FixedMoneyField()
    client_id = forms.CharField(label=_('Client ID'), required=False)

    def __init__(self, *args, **kwargs):
        """Initialize form and disble most of the fields."""
        super().__init__(*args, **kwargs)
        for key, value in self.fields.items():
            if key not in ('processor', 'client_id'):
                value.disabled = True

    def clean(self):
        """
        Check whether payment processor has been set.

        If so, assign payment to chosen payment processor and note the result.
        """
        cleaned_data = super().clean()
        if cleaned_data['processor']:
            processor_class = module_loading.import_string(cleaned_data['processor'])
            processor = processor_class()
            result = processor.assign_payment(self.instance, cleaned_data['client_id'])
            if result.result:
                cleaned_data['state'] = PaymentState.PROCESSED
                cleaned_data['objective'] = result.objective
                return cleaned_data
            else:
                raise forms.ValidationError(_('Unable to assign payment'), code='unable_to_assign')

    def save(self, commit=True):
        """Manually assign payment objective and save payment."""
        if 'state' in self.cleaned_data:
            self.instance.state = self.cleaned_data['state']
            self.instance.objective = self.cleaned_data['objective']
        return super().save(commit=commit)

    class Meta:
        """Meta class."""

        fields = '__all__'
        model = BankPayment

        widgets = {
            'processor': forms.Select(choices=BankPayment.objective_choices())
        }
