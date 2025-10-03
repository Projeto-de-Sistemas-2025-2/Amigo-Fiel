from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Conversation(models.Model):
    # Normalizamos a dupla: user_a.id < user_b.id para evitar duplicatas
    user_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_a')
    user_b = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations_as_b')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(db_index=True, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user_a', 'user_b'], name='unique_conv_pair'),
        ]
        indexes = [
            models.Index(fields=['last_message_at']),
        ]

    def save(self, *args, **kwargs):
        # garanta ordem a < b
        if self.user_a_id and self.user_b_id and self.user_a_id > self.user_b_id:
            self.user_a_id, self.user_b_id = self.user_b_id, self.user_a_id
        super().save(*args, **kwargs)

    def participants(self):
        return (self.user_a, self.user_b)

    def other_of(self, user):
        return self.user_b if user == self.user_a else self.user_a

    @staticmethod
    def for_users(u1, u2):
        a, b = (u1, u2) if u1.id < u2.id else (u2, u1)
        return Conversation.objects.get_or_create(user_a=a, user_b=b)[0]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_sent')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def mark_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])
