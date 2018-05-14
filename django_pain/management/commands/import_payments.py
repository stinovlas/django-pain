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
        parser.add_argument('-p', '--parser', type=str, required=True, help='dotted path to parser class')
        parser.add_argument('input_file', nargs='*', type=str, help='input file with bank statement')

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

        input_files = options['input_file']
        if not input_files:
            input_files = ['-']

        for input_file in input_files:
            if input_file == '-':
                handle = sys.stdin
            else:
                handle = open(input_file)

            try:
                payments = parser.parse(handle)
            except BankAccount.DoesNotExist as e:
                raise CommandError(e)
            else:
                self.save_payments(payments, **options)
            finally:
                handle.close()

    def save_payments(self, payments, **options):
        """Save payments and related objects to database."""
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
