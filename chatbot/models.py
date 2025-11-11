from django.db import models
from core.choices import ChatSender

class ChatbotSessions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey("accounts.Users", models.SET_NULL, blank=True, null=True)
    session_token = models.CharField(unique=True, max_length=64)
    channel = models.CharField(max_length=3, default='WEB')
    locale = models.CharField(max_length=10, default='vi')
    state = models.CharField(max_length=6, default='ACTIVE')
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'chatbot_sessions'

class ChatbotMessages(models.Model):
    id = models.BigAutoField(primary_key=True)
    session = models.ForeignKey(ChatbotSessions, models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=4, choices=ChatSender.choices)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'chatbot_messages'

class ChatbotFaqs(models.Model):
    id = models.BigAutoField(primary_key=True)
    question = models.CharField(max_length=500)
    answer = models.TextField()
    tags = models.CharField(max_length=255, blank=True, null=True)
    locale = models.CharField(max_length=10, default='vi')
    enabled = models.IntegerField(default=1)

    class Meta:
        managed = False
        db_table = 'chatbot_faqs'
