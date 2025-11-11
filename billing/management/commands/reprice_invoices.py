from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField

from billing.models import Invoices, InvoiceItems
from doctors.pricing import get_consultation_fee


class Command(BaseCommand):
    help = "Reprice consultation fees on invoices based on doctor rank normalization and recalculate totals."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Process all invoices (default: only UNPAID)")

    @transaction.atomic
    def handle(self, *args, **options):
        qs = Invoices.objects.all() if options.get("all") else Invoices.objects.filter(status="UNPAID")
        updated = 0
        for inv in qs.select_related("appointment__doctor"):
            doctor = getattr(inv.appointment, "doctor", None)
            if not doctor:
                continue
            expected_fee = get_consultation_fee(doctor)

            allow_item_edit = inv.status == "UNPAID"

            # Find consultation item
            consult_item = InvoiceItems.objects.filter(invoice=inv, item_type="CONSULTATION").first()
            if allow_item_edit:
                if not consult_item:
                    # Create if missing
                    consult_item = InvoiceItems(
                        invoice=inv,
                        item_type="CONSULTATION",
                        ref_id=getattr(doctor, "id", None),
                        description="Phí khám bệnh",
                        unit=None,
                        quantity=1,
                        unit_price=expected_fee,
                    )
                    consult_item.save()
                    updated += 1
                elif consult_item.unit_price != expected_fee:
                    consult_item.unit_price = expected_fee
                    consult_item.save(update_fields=["unit_price"])
                    updated += 1

            # Recompute totals from quantity * unit_price
            agg = InvoiceItems.objects.filter(invoice=inv).aggregate(
                total=Sum(
                    ExpressionWrapper(F("quantity") * F("unit_price"),
                                      output_field=DecimalField(max_digits=12, decimal_places=2))
                )
            )
            total = agg.get("total") or 0
            if inv.status == "UNPAID":
                inv.subtotal = total
                inv.amount_due = total
                inv.save(update_fields=["subtotal", "amount_due"])

        self.stdout.write(self.style.SUCCESS(f"Repriced invoices. Updated items: {updated}"))


