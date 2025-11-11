from django.core.management.base import BaseCommand
from billing.models import Invoices


class Command(BaseCommand):
    help = "Recompute subtotal/amount_due for all invoices"

    def handle(self, *args, **options):
        count = 0
        for inv in Invoices.objects.all():
            try:
                inv.recompute_totals()
                count += 1
            except Exception as e:
                self.stderr.write(f"Failed invoice #{inv.id}: {e}")
        self.stdout.write(self.style.SUCCESS(f"Recomputed {count} invoices"))


