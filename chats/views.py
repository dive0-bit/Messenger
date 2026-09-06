from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, ConversationMember, Message
from accounts.models import Profiles
from .serializers import MessageSerializer


def _is_member(conversation_id, user):
    return ConversationMember.objects.filter(
        conversation_id=conversation_id, user=user,
    ).exists()


def _conversation_data(conversation, user):
    other_member = conversation.conversationmember_set.exclude(user=user).select_related("user").first()
    last_message = conversation.message_set.select_related("sender").order_by("-created_at").first()
    other_profile = getattr(other_member.user, "profiles", None) if other_member else None
    return {
        "id": conversation.id,
        "participant": other_member.user.username if other_member else "Conversation",
        "participant_id": other_member.user_id if other_member else None,
        "participant_picture": other_profile.profile_picture.url if other_profile and other_profile.profile_picture else "",
        "last_message": last_message.content if last_message else "No messages yet",
        "last_message_at": last_message.created_at if last_message else conversation.created_at,
    }


@login_required
def chat_home(request):
    users = User.objects.exclude(id=request.user.id).order_by("username")
    profile, _ = Profiles.objects.get_or_create(user=request.user)
    for user in users:
        user_profile = getattr(user, "profiles", None)
        user.profile_picture_url = user_profile.profile_picture.url if user_profile and user_profile.profile_picture else ""
    return render(request, "accounts/home.html", {
        "chat_users": users,
        "profile": profile,
    })


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def conversation_list(request):
    if request.method == "GET":
        conversations = Conversation.objects.filter(
            conversationmember__user=request.user,
        ).prefetch_related("conversationmember_set", "message_set")
        data = [_conversation_data(conversation, request.user) for conversation in conversations]
        data.sort(key=lambda item: item["last_message_at"], reverse=True)
        return Response(data)

    if request.method == "DELETE":
        # DELETE is handled by conversation_delete view via URL routing
        # This shouldn't be reached, but just in case:
        return Response(
            {"detail": "Use DELETE /api/conversations/{id}/ instead"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # POST - Create new conversation
    recipient_id = request.data.get("recipient_id")
    try:
        recipient = User.objects.get(id=recipient_id)
    except (User.DoesNotExist, TypeError, ValueError):
        return Response({"detail": "Choose a valid user."}, status=status.HTTP_400_BAD_REQUEST)

    if recipient == request.user:
        return Response({"detail": "You cannot start a conversation with yourself."}, status=status.HTTP_400_BAD_REQUEST)

    existing = Conversation.objects.filter(
        conversationmember__user=request.user,
    ).filter(
        conversationmember__user=recipient,
    ).first()
    if existing:
        return Response(_conversation_data(existing, request.user), status=status.HTTP_200_OK)

    with transaction.atomic():
        conversation = Conversation.objects.create()
        ConversationMember.objects.bulk_create([
            ConversationMember(conversation=conversation, user=request.user),
            ConversationMember(conversation=conversation, user=recipient),
        ])
    return Response(_conversation_data(conversation, request.user), status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def conversation_messages(request, conversation_id):
    if not _is_member(conversation_id, request.user):
        return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        messages = Message.objects.filter(
            conversation_id=conversation_id,
        ).select_related("sender").order_by("created_at")
        return Response(MessageSerializer(messages, many=True).data)

    serializer = MessageSerializer(data=request.data)
    if serializer.is_valid():
        message = serializer.save(
            conversation_id=conversation_id,
            sender=request.user,
        )
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def conversation_delete(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
    except Conversation.DoesNotExist:
        return Response(
            {"detail": "Conversation not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user is a member
    if not _is_member(conversation_id, request.user):
        return Response(
            {"detail": "You do not have permission to delete this conversation."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    conversation.delete()
    return Response({"detail": "Conversation deleted successfully."}, status=status.HTTP_200_OK)