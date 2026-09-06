from django.db import models
from django.contrib.auth.models import User


class Conversation(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Conversation {self.id}"


class ConversationMember(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - Conversation {self.conversation.id}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_conversation_member",
            ),
        ]
    
    
class Message(models.Model):
    conversation = models.ForeignKey(Conversation,on_delete=models.CASCADE)

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_read = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"