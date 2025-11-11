# core/choices.py
from django.db import models

class Role(models.TextChoices):
    PATIENT="PATIENT","Patient"; DOCTOR="DOCTOR","Doctor"
    STAFF="STAFF","Staff"; ADMIN="ADMIN","Admin"

class ApptStatus(models.TextChoices):
    PENDING="PENDING","Pending"; CONFIRMED="CONFIRMED","Confirmed"
    IN_PROGRESS="IN_PROGRESS","In progress"; COMPLETED="COMPLETED","Completed"
    CANCELLED="CANCELLED","Cancelled"; NO_SHOW="NO_SHOW","No-show"

class Source(models.TextChoices):
    PORTAL="PORTAL","Portal"; STAFF="STAFF","Staff"; CHATBOT="CHATBOT","Chatbot"

class ScheduleStatus(models.TextChoices):
    OPEN="OPEN","Open"; CLOSED="CLOSED","Closed"

class ItemType(models.TextChoices):
    CONSULTATION="CONSULTATION","Consultation"; DRUG="DRUG","Drug"; SERVICE="SERVICE","Service"

class InvoiceStatus(models.TextChoices):
    DRAFT="DRAFT","Draft"; UNPAID="UNPAID","Unpaid"; PAID="PAID","Paid"
    REFUNDED="REFUNDED","Refunded"; VOID="VOID","Void"

class ChatSender(models.TextChoices):
    USER="USER","User"; BOT="BOT","Bot"
