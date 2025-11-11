from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import InvoiceItems


@receiver([post_save, post_delete], sender=InvoiceItems)
def recompute_invoice_totals(sender, instance, **kwargs):
    try:
        instance.invoice.recompute_totals()
    except Exception:
        pass


