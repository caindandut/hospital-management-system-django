from django.db import models
from django.db.models import Sum, F, DecimalField, Value as V
from django.db.models.functions import Coalesce
from core.choices import InvoiceStatus, ItemType

class Invoices(models.Model):
    id = models.BigAutoField(primary_key=True)
    appointment = models.OneToOneField("appointments.Appointments", models.PROTECT, related_name="invoice")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=8, choices=InvoiceStatus.choices, default="UNPAID")
    created_by_user = models.ForeignKey("accounts.Users", models.DO_NOTHING, related_name="created_invoices")
    created_at = models.DateTimeField()
    printed_at = models.DateTimeField(blank=True, null=True)
    printed_by_user = models.ForeignKey("accounts.Users", models.DO_NOTHING, blank=True, null=True, related_name="printed_invoices")

    class Meta:
        managed = False
        db_table = 'invoices'

    def recompute_totals(self):
        total = (
            self.items.aggregate(
                s=Coalesce(
                    Sum(
                        F('quantity') * F('unit_price'),
                        output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                    V(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                )
            ).get('s') or 0
        )
        self.subtotal = total
        self.amount_due = total - (self.discount or 0)
        self.save(update_fields=["subtotal", "amount_due"])

class InvoiceItems(models.Model):
    id = models.BigAutoField(primary_key=True)
    invoice = models.ForeignKey(Invoices, models.CASCADE, related_name="items")
    item_type = models.CharField(max_length=12, choices=ItemType.choices)
    ref_id = models.BigIntegerField(blank=True, null=True)
    description = models.CharField(max_length=255)
    unit = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'invoice_items'

class Payments(models.Model):
    id = models.BigAutoField(primary_key=True)
    invoice = models.ForeignKey(Invoices, models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=4, default="CASH")  # chỉ tiền mặt
    paid_at = models.DateTimeField()
    received_by_user = models.ForeignKey("accounts.Users", models.PROTECT)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'payments'

class InvoicePrintLogs(models.Model):
    id = models.BigAutoField(primary_key=True)
    invoice = models.ForeignKey(Invoices, models.CASCADE)
    printed_by_user = models.ForeignKey("accounts.Users", models.PROTECT)
    printed_at = models.DateTimeField()
    copy_tag = models.CharField(max_length=8)
    note = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'invoice_print_logs'
