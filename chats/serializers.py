from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'sender_username',
            'content', 'created_at', 'is_read',
        ]
        read_only_fields = ['conversation', 'sender', 'is_read']

    def validate_content(self, value):
        content = value.strip()
        if not content:
            raise serializers.ValidationError("Message cannot be empty.")
        return content