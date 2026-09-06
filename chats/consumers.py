from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from .models import Conversation, ConversationMember, Message


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"conversation_{self.conversation_id}"

        if not await self.user_can_access():
            await self.close(code=4403)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") != "message":
            await self.send_json({"type": "error", "detail": "Unsupported event type."})
            return

        message_text = content.get("content", "").strip()
        if not message_text:
            await self.send_json({"type": "error", "detail": "Message cannot be empty."})
            return

        message = await self.create_message(message_text)
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.message", "message": message},
        )

    async def chat_message(self, event):
        await self.send_json({"type": "message", "message": event["message"]})

    @database_sync_to_async
    def user_can_access(self):
        user = self.scope.get("user")
        return (
            user is not None
            and not isinstance(user, AnonymousUser)
            and user.is_authenticated
            and ConversationMember.objects.filter(
                conversation_id=self.conversation_id,
                user=user,
            ).exists()
        )

    @database_sync_to_async
    def create_message(self, content):
        message = Message.objects.create(
            conversation_id=self.conversation_id,
            sender=self.scope["user"],
            content=content,
        )
        return {
            "id": message.id,
            "conversation": message.conversation_id,
            "sender": message.sender_id,
            "sender_username": message.sender.username,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "is_read": message.is_read,
        }


