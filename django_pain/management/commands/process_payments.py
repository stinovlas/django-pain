"""Command for processing bank payments."""
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.utils import module_loading
from django.utils.dateparse import parse_datetime

from django_pain.constants import PaymentState
from django_pain.models import BankPayment


class Command(BaseCommand):
    """Import payments from bank."""

    help = 'Import payments from the bank. Bank statement should be provided on standard input.'

    def add_arguments(self, parser):
        """Command takes one argument - dotted path to parser class."""
        parser.add_argument('-f', '--from', dest='time_from', type=parse_datetime,
                            help="ISO datetime after which payments should be processed")
        parser.add_argument('-t', '--to', dest='time_to', type=parse_datetime,
                            help="ISO datetime before which payments should be processed")

    def handle(self, *args, **options):
        """Run command."""
        self.options = options

        payments = BankPayment.objects.filter(state=PaymentState.IMPORTED)
        if options['time_from'] is not None:
            payments = payments.filter(create_time__gte=options['time_from'])
        if options['time_to'] is not None:
            payments = payments.filter(create_time__lte=options['time_to'])

        processors = getattr(settings, 'PAIN_PROCESSORS', None)
        if processors is None:
            raise ImproperlyConfigured('Setting PAIN_PROCESSORS has to be present in order to run process_payments')

        for payment in payments:
            for processor_str in processors:
                processor_class = module_loading.import_string(processor_str)
                processor = processor_class()

                if processor.process_payment(payment):
                    payment.state = PaymentState.PROCESSED
                    payment.save()
                    break

            if payment.state != PaymentState.PROCESSED:
                payment.state = PaymentState.DEFERRED
                payment.save()
