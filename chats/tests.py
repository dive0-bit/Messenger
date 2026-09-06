from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from channels.testing import WebsocketCommunicator
from rest_framework.test import APIClient

from config.asgi import application
from .models import Conversation, ConversationMember, Message


class ChatApiTests(TestCase):
	def setUp(self):
		self.alice = User.objects.create_user("alice", password="password123")
		self.bob = User.objects.create_user("bob", password="password123")
		self.eve = User.objects.create_user("eve", password="password123")
		self.client = APIClient()
		self.client.login(username="alice", password="password123")

	def test_user_can_create_and_reuse_direct_conversation(self):
		response = self.client.post("/api/conversations/", {"recipient_id": self.bob.id}, format="json")
		self.assertEqual(response.status_code, 201)
		conversation_id = response.data["id"]

		second_response = self.client.post("/api/conversations/", {"recipient_id": self.bob.id}, format="json")
		self.assertEqual(second_response.status_code, 200)
		self.assertEqual(second_response.data["id"], conversation_id)
		self.assertEqual(Conversation.objects.count(), 1)
		self.assertEqual(ConversationMember.objects.count(), 2)

	def test_member_can_send_and_read_message(self):
		conversation = Conversation.objects.create()
		ConversationMember.objects.create(conversation=conversation, user=self.alice)
		ConversationMember.objects.create(conversation=conversation, user=self.bob)

		send_response = self.client.post(
			f"/api/conversations/{conversation.id}/messages/",
			{"content": " Hello Bob "},
			format="json",
		)
		self.assertEqual(send_response.status_code, 201)
		self.assertEqual(send_response.data["content"], "Hello Bob")
		self.assertEqual(send_response.data["sender_username"], "alice")

		read_response = self.client.get(f"/api/conversations/{conversation.id}/messages/")
		self.assertEqual(read_response.status_code, 200)
		self.assertEqual(read_response.data[0]["content"], "Hello Bob")

	def test_non_member_cannot_read_messages(self):
		conversation = Conversation.objects.create()
		ConversationMember.objects.create(conversation=conversation, user=self.bob)
		Message.objects.create(conversation=conversation, sender=self.bob, content="Private")

		response = self.client.get(f"/api/conversations/{conversation.id}/messages/")
		self.assertEqual(response.status_code, 404)

	def test_member_can_delete_conversation_and_messages(self):
		conversation = Conversation.objects.create()
		ConversationMember.objects.create(conversation=conversation, user=self.alice)
		ConversationMember.objects.create(conversation=conversation, user=self.bob)
		Message.objects.create(conversation=conversation, sender=self.alice, content="Delete me")

		response = self.client.delete(f"/api/conversations/{conversation.id}/")

		self.assertEqual(response.status_code, 204)
		self.assertFalse(Conversation.objects.filter(id=conversation.id).exists())
		self.assertFalse(Message.objects.filter(content="Delete me").exists())

	def test_non_member_cannot_delete_conversation(self):
		conversation = Conversation.objects.create()
		ConversationMember.objects.create(conversation=conversation, user=self.bob)

		response = self.client.delete(f"/api/conversations/{conversation.id}/")

		self.assertEqual(response.status_code, 404)
		self.assertTrue(Conversation.objects.filter(id=conversation.id).exists())

	def test_chat_home_renders_for_authenticated_user(self):
		response = self.client.get("/home/")
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, "Messenger")


class ChatWebsocketTests(TransactionTestCase):
	def test_member_can_send_message_over_websocket(self):
		alice = User.objects.create_user("socket-alice", password="password123")
		conversation = Conversation.objects.create()
		ConversationMember.objects.create(conversation=conversation, user=alice)

		async def exercise_socket():
			communicator = WebsocketCommunicator(application, f"/ws/conversations/{conversation.id}/")
			communicator.scope["user"] = alice
			connected, _ = await communicator.connect()
			self.assertTrue(connected)
			await communicator.send_json_to({"type": "message", "content": "Hello over websocket"})
			payload = await communicator.receive_json_from()
			self.assertEqual(payload["type"], "message")
			self.assertEqual(payload["message"]["content"], "Hello over websocket")
			await communicator.disconnect()

		import asyncio
		asyncio.run(exercise_socket())
		self.assertTrue(Message.objects.filter(content="Hello over websocket").exists())
