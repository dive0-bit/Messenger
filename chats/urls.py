from django.urls import path
from .views import chat_home, conversation_delete, conversation_list, conversation_messages

urlpatterns = [
    path('home/', chat_home, name='home'),
    path('api/conversations/', conversation_list, name='conversation_list'),
    path('api/conversations/<int:conversation_id>/', conversation_delete, name='conversation_delete'),
    path('api/conversations/<int:conversation_id>/messages/', conversation_messages, name='conversation_messages'),
]
