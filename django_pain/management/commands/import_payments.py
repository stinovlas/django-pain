"""Command for importing payments from bank."""
import importlib
import sys
from typing import Sequence

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

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
            raise CommandError(e)

        for payment_parts in payments:
            try:
                with transaction.atomic():
                    if isinstance(payment_parts, Sequence):
                        payment = payment_parts[0]
                        payment_related_objects = payment_parts[1:]
                    else:
                        payment = payment_parts
                        payment_related_objects = ()

                    payment.full_clean()
                    payment.save()
                    for rel in payment_related_objects:
                        for field in [f.name for f in rel._meta.get_fields()]:
                            # Django does not refresh object references before saving the objects
                            # into database. Therefore we need to do that manually.
                            # See https://code.djangoproject.com/ticket/8892
                            setattr(rel, field, getattr(rel, field))
                        rel.full_clean()
                        rel.save()
            except ValidationError as error:
                if options['verbosity'] >= 1:
                    for message in error.messages:
                        self.stderr.write(self.style.WARNING(message))
            else:
                if options['verbosity'] >= 2:
                    self.stdout.write(self.style.SUCCESS('Payment ID %s has been imported.' % payment.identifier))
