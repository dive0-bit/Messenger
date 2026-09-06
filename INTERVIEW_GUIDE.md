# Messenger Project: Interview Guide

## One-line explanation

This is a private real-time messaging application built with Django, Django REST Framework, Django Channels, WebSockets, SQLite, and session/JWT authentication.

## Main architecture

- `config/settings.py`: installed apps, middleware, database, REST authentication, ASGI and channel-layer configuration.
- `config/urls.py`: root URL dispatcher.
- `config/asgi.py`: combines normal HTTP requests with WebSocket requests through Channels.
- `accounts/`: registration, login, password reset, user APIs, profiles, and account templates.
- `chats/`: conversations, members, messages, REST APIs, WebSocket consumer, routing, and chat templates.
- `requirements.txt`: reproducible Python dependencies.
- `db.sqlite3`: local development database.

## Request flow

1. A user registers or logs in. Browser login creates a Django session; API clients can use JWT.
2. The home page loads users and conversations through REST endpoints.
3. Selecting a person creates or reuses a direct conversation.
4. Existing messages are loaded through REST.
5. The browser opens `/ws/conversations/<conversation_id>/` for live updates.
6. `ChatConsumer` checks authentication and conversation membership before accepting the socket.
7. A message is saved in the database and broadcast to the conversation group through the channel layer.
8. If the WebSocket is unavailable, the UI keeps the REST message endpoint as a fallback.

## Important design decisions

- REST is used for durable data retrieval and fallback behavior.
- WebSockets are used for low-latency live delivery.
- `AuthMiddlewareStack` shares the browser's Django session with the WebSocket consumer.
- Membership is checked before a user can read or send private messages.
- The in-memory channel layer is suitable for local development and one process. Redis with `channels_redis` is needed for multiple workers.
- `daphne` is installed and registered so the ASGI application can serve WebSocket traffic.

## How to run locally

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\chat\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

Open `http://127.0.0.1:8000/register/`. For a dedicated ASGI server, use:

```powershell
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

## Interview questions to prepare

### Why REST and WebSockets together?

REST is reliable for loading history and standard CRUD operations. WebSockets avoid polling and deliver new messages immediately. Keeping REST as fallback makes the application usable when a socket cannot connect.

### How is a private conversation protected?

The API and `ChatConsumer` both verify that the authenticated user belongs to the conversation. The consumer closes unauthorized sockets with code `4403`.

### Why ASGI instead of only WSGI?

WSGI handles normal request-response traffic. ASGI supports asynchronous protocols such as WebSockets, so the project uses `config.asgi:application` for real-time messaging.

### What would you improve for production?

- Replace SQLite with PostgreSQL.
- Replace the in-memory channel layer with Redis.
- Move secrets to environment variables.
- Configure `ALLOWED_HOSTS`, HTTPS, secure cookies, and CSRF settings.
- Serve static/media files through a production web server or object storage.
- Add pagination, rate limiting, unread counts, delivery/read receipts, and stronger automated tests.

## Useful validation commands

```powershell
python manage.py check
python manage.py test accounts chats
```