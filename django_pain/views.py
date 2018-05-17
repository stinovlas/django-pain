from django.views.generic import TemplateView

from .models import BankPayment


class PaymentListView(TemplateView):

    template_name = 'django_pain/payments_list.html'

    def get_context_data(self, **kwargs):
        context = kwargs
        context['payments'] = BankPayment.objects.all()
        return context
