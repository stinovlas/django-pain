"""Command for importing payments from bank."""
import importlib
import sys

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import IntegrityError

from django_pain.models import BankAccount


class Command(BaseCommand):
    """Import payments from bank."""

    help = 'Import payments from the bank. Bank statement should be provided on standard input.'

    def add_arguments(self, parser):
        """Command takes one argument - dotted path to parser class."""
        parser.add_argument('parser', type=str, help='dotted path to parser class')

    @staticmethod
    def get_parser(parser_path):
        """Get parser instance from parser path argument."""
        module_name, class_name = parser_path.rsplit('.', 1)

        parser_module = importlib.import_module(module_name)
        parser_class = getattr(parser_module, class_name)
        return parser_class()

    def handle(self, *args, **options):
        """Run command."""
        parser = self.get_parser(options['parser'])

        try:
            payments = parser.parse(sys.stdin)
        except BankAccount.DoesNotExist as e:
            self.stderr.write(self.style.ERROR(str(e)))
            sys.exit(1)

        for payment_parts in payments:
            try:
                with transaction.atomic():
                    if type(payment_parts) is tuple:
                        payment = payment_parts[0]
                        payment_related_objects = payment_parts[1:]
                    else:
                        payment = payment_parts
                        payment_related_objects = ()

                    payment.save()
                    for rel in payment_related_objects:
                        for field in [f.name for f in rel._meta.get_fields()]:
                            # Django does not refresh object references before saving the objects
                            # into database. Therefore we need to do that manually.
                            # See https://code.djangoproject.com/ticket/8892
                            setattr(rel, field, getattr(rel, field))
                        rel.save()
            except IntegrityError as e:
                self.stderr.write(self.style.WARNING('Payment ID %s had already been imported.' % payment.identifier))
            else:
                self.stdout.write(self.style.SUCCESS('Payment ID %s has been imported.' % payment.identifier))
