"""Payment views."""
from django.views.generic import TemplateView

from .models import BankPayment


class PaymentListView(TemplateView):
    """Payment list view."""

    template_name = 'django_pain/payments_list.html'

    def get_context_data(self, **kwargs):
        """Get context data."""
        context = super().get_context_data(**kwargs)
        context['payments'] = BankPayment.objects.all()
        return context
