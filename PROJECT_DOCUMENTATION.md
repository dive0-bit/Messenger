# Messenger Project Documentation

## 1. Overview

Messenger is a Django 6.1.1 application for private, direct user conversations. It provides:

- HTML pages for registration, login, password reset, and the chat screen.
- Django REST Framework APIs for users, conversations, conversation history, and JWT login.
- Authenticated WebSocket messaging through Django Channels.
- SQLite persistence for users, profiles, conversations, members, and messages.
- Profile picture upload and avatar display for the current user, people list, and conversations.
- Django admin registrations for profiles and chat records.

The chat page uses REST for initial data and history, and WebSockets for live message delivery. The REST message-create endpoint remains available as an API fallback, while the browser composer uses WebSockets.

## 2. Quick Start

From the project root on Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\chat\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

Open `http://127.0.0.1:8000/register/` and create two users. Log in as one user, choose the other user, and send a message.

For a WebSocket-capable ASGI server, use Daphne:

```powershell
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

`python manage.py runserver` is useful for ordinary HTTP development, but this project should be started with Daphne when testing live WebSockets. Daphne loads `config.asgi:application`; that ASGI application contains both the HTTP Django application and the WebSocket router.

The current channel layer is in-memory and is intended for development or a single process. For multiple workers, configure Redis with `channels_redis` and replace `CHANNEL_LAYERS` in `config/settings.py`.

## 3. Folder and File Map

```text
Messenger/
|-- manage.py                    Django command-line entry point
|-- db.sqlite3                   Local SQLite database
|-- requirements.txt             Reproducible Python dependencies
|-- PROJECT_DOCUMENTATION.md     This documentation
|-- config/
|   |-- __init__.py              Python package marker
|   |-- settings.py              Django apps, middleware, database, DRF, ASGI settings
|   |-- urls.py                  Root URL dispatcher
|   |-- asgi.py                  HTTP and WebSocket ASGI router
|   `-- wsgi.py                  WSGI entry point for traditional HTTP servers
|-- accounts/
|   |-- apps.py                  Accounts AppConfig
|   |-- models.py                Profiles model
|   |-- serializers.py           User and registration serializers
|   |-- views.py                 Browser auth, registration, user and password-reset views
|   |-- urls.py                  Browser, user API, JWT, and password-reset routes
|   |-- admin.py                 Registers Profiles in admin
|   |-- tests.py                 Registration, login, and password-reset tests
|   |-- migrations/0001_initial.py
|   `-- templates/accounts/
|       |-- login.html           Login form
|       |-- register.html         Registration form
|       |-- home.html             Main chat UI and WebSocket client
|       |-- forgot_password.html  Password reset request form
|       |-- password_reset_email.html
|       |-- password_reset_done.html
|       |-- password_reset_confirm.html
|       `-- password_reset_complete.html
|-- chats/
|   |-- apps.py                  Chats AppConfig
|   |-- models.py                Conversation, member, and message models
|   |-- serializers.py           Message API serializer and validation
|   |-- views.py                 Conversation and message REST views
|   |-- urls.py                  Chat REST routes
|   |-- consumers.py             Authenticated async WebSocket consumer
|   |-- routing.py               WebSocket URL patterns
|   |-- admin.py                 Registers chat models in admin
|   |-- tests.py                 REST deletion and WebSocket tests
|   `-- migrations/
|       |-- 0001_initial.py      Conversation and ConversationMember tables
|       |-- 0002_message.py       Message table
|       `-- 0003_...py           Unique conversation/member constraint
`-- profile_pictures/            Uploaded profile-image directory
```

The `chat/` directory is the local Python virtual environment. Its generated `Lib/`, `Include/`, and `Scripts/` contents are dependencies and should not be treated as application source.

## 4. Application Working

### Browser flow

1. A user registers at `/register/` or `/api/register/`.
2. The browser login at `/login/` creates a Django session. API clients can obtain JWT tokens from `/api/login/`.
3. `/home/` renders the list of other users. The page loads existing conversations using `GET /api/conversations/`.
4. Clicking a user calls `POST /api/conversations/`. Existing direct conversations are reused; otherwise a conversation and two members are created atomically.
5. Selecting a conversation loads history through `GET /api/conversations/<id>/messages/`.
6. The browser opens `ws://host/ws/conversations/<id>/` (or `wss://` under HTTPS). Session cookies are accepted by `AuthMiddlewareStack`.
7. A composer message is sent as a JSON WebSocket event. The consumer validates, persists, and broadcasts it to every connected member of that conversation.
8. Each browser receives the broadcast and appends the message without reloading the page.
9. The delete button calls `DELETE /api/conversations/<id>/`. Any member may delete that conversation; database cascade removes its members and messages.

### Authentication and authorization

- Browser views use Django session authentication.
- REST APIs accept session authentication and JWT authentication as configured in `REST_FRAMEWORK`.
- Conversation history and message creation require conversation membership.
- WebSocket connections require an authenticated session user who is a member of the requested conversation.
- Non-members receive REST `404` for protected conversation resources and WebSocket close code `4403`.
- Conversation deletion is member-only. It deletes the whole conversation for all participants, not just a local copy.

## 5. REST API

All API paths are rooted at `/`.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/register/` | Public | Create a user; password minimum is 8 characters |
| `GET` | `/api/users/` | Default DRF permission | List users |
| `POST` | `/api/login/` | Public | Return JWT access and refresh tokens |
| `POST` | `/api/token/refresh/` | Public | Refresh a JWT access token |
| `POST` | `/profile/update/` | Browser session | Upload profile picture and update bio |
| `GET` | `/api/conversations/` | Authenticated | List the current user's conversations, newest first |
| `POST` | `/api/conversations/` | Authenticated | Create or reuse a direct conversation using `recipient_id` |
| `DELETE` | `/api/conversations/<id>/` | Conversation member | Delete conversation, members, and messages |
| `GET` | `/api/conversations/<id>/messages/` | Conversation member | Return messages in chronological order |
| `POST` | `/api/conversations/<id>/messages/` | Conversation member | REST fallback for creating a message |

Example delete request with a session client:

```http
DELETE /api/conversations/12/
X-CSRFToken: <csrf-token>
Cookie: sessionid=<session>; csrftoken=<csrf-token>
```

Successful deletion returns `204 No Content`. An unknown conversation or a conversation where the user is not a member returns `404`.

Example message response:

```json
{
  "id": 31,
  "conversation": 12,
  "sender": 4,
  "sender_username": "alice",
  "content": "Hello Bob",
  "created_at": "2026-09-05T10:30:00+00:00",
  "is_read": false
}
```

## 6. WebSocket Contract

### What is used and why

The realtime feature is built from these pieces:

| Component | Location | Role |
|---|---|---|
| Django Channels | `requirements.txt` | Adds WebSocket and channel-layer support to Django |
| Daphne | `requirements.txt` | ASGI server that accepts HTTP and WebSocket connections |
| ASGI protocol router | `config/asgi.py` | Sends HTTP to Django and WebSockets to Channels |
| `AuthMiddlewareStack` | `config/asgi.py` | Reads the Django session cookie during the WebSocket handshake |
| `URLRouter` | `config/asgi.py` | Matches a socket URL to a consumer |
| WebSocket routing | `chats/routing.py` | Maps `/ws/conversations/<id>/` to `ChatConsumer` |
| `AsyncJsonWebsocketConsumer` | `chats/consumers.py` | Receives and sends JSON asynchronously |
| `database_sync_to_async` | `chats/consumers.py` | Runs Django ORM queries safely from async code |
| Channel group | `chats/consumers.py` | Broadcasts a message to every connected member of one conversation |
| Browser `WebSocket` API | `accounts/templates/accounts/home.html` | Opens the socket, sends JSON, receives broadcasts, and updates the UI |
| In-memory channel layer | `config/settings.py` | Routes group messages during local single-process development |

The message path is:

```text
Browser WebSocket
  -> Daphne ASGI server
  -> ProtocolTypeRouter
  -> AuthMiddlewareStack
  -> URLRouter
  -> ChatConsumer
  -> database_sync_to_async
  -> Message table
  -> conversation_<id> channel group
  -> all connected conversation members
```

### ASGI routing example

`config/asgi.py` separates ordinary HTTP traffic from WebSocket traffic:

```python
application = ProtocolTypeRouter({
  "http": django_application,
  "websocket": AuthMiddlewareStack(
    URLRouter(websocket_urlpatterns),
  ),
})
```

The browser session cookie is important here. `AuthMiddlewareStack` converts it into `scope["user"]`, which the consumer checks before accepting the connection.

### URL routing example

`chats/routing.py` maps the conversation id from the URL into the consumer:

```python
websocket_urlpatterns = [
  path(
    "ws/conversations/<int:conversation_id>/",
    ChatConsumer.as_asgi(),
  ),
]
```

### Consumer example

The consumer first checks membership, then joins a group. When it receives a message, it saves the message and broadcasts it:

```python
async def receive_json(self, content, **kwargs):
  message_text = content.get("content", "").strip()
  message = await self.create_message(message_text)
  await self.channel_layer.group_send(
    self.group_name,
    {"type": "chat.message", "message": message},
  )

async def chat_message(self, event):
  await self.send_json({
    "type": "message",
    "message": event["message"],
  })
```

`type: "chat.message"` is a Channels event name. Channels converts the dot to an underscore and calls the `chat_message()` method. This is how one incoming message reaches all open browser sockets in the same group.

### Browser client example

The chat page chooses `ws://` for HTTP and `wss://` for HTTPS:

```javascript
const scheme = window.location.protocol === "https:" ? "wss" : "ws";
const socket = new WebSocket(
  `${scheme}://${window.location.host}/ws/conversations/${conversation.id}/`
);

socket.onopen = () => {
  socket.send(JSON.stringify({
    type: "message",
    content: "Hello Bob"
  }));
};

socket.onmessage = event => {
  const payload = JSON.parse(event.data);
  appendMessage(payload.message);
};
```

### Why the page can show REST fallback

The UI displays `Realtime connection unavailable. Messages use REST fallback.` when the browser cannot establish a WebSocket. This normally means the page was opened against a WSGI-only server, the wrong Python environment, a proxy is not forwarding WebSocket upgrade requests, or the user is not authenticated.

When this happens, the composer sends the same message through:

```http
POST /api/conversations/<conversation_id>/messages/
Content-Type: application/json

{"content": "Hello Bob"}
```

For local realtime testing, start the correct server from the project root:

```powershell
.\chat\Scripts\Activate.ps1
daphne -b 127.0.0.1 -p 8000 config.asgi:application
```

Then refresh `/home/`, select a conversation, and wait until the composer becomes enabled. The current development setup uses `InMemoryChannelLayer`, so all browser tabs must connect to this same Daphne process. A multi-process deployment needs Redis.

### Endpoint

```text
ws://127.0.0.1:8000/ws/conversations/<conversation_id>/
```

Use `wss://` when the site is served over HTTPS. The browser must send the authenticated Django session cookie during the handshake.

### Client to server

```json
{
  "type": "message",
  "content": "Hello Bob"
}
```

The consumer trims content and rejects blank messages. Unsupported event types return:

```json
{
  "type": "error",
  "detail": "Unsupported event type."
}
```

### Server to client

```json
{
  "type": "message",
  "message": {
    "id": 31,
    "conversation": 12,
    "sender": 4,
    "sender_username": "alice",
    "content": "Hello Bob",
    "created_at": "2026-09-05T10:30:00+00:00",
    "is_read": false
  }
}
```

The consumer uses the group name `conversation_<id>`. Every connected member receives messages written to that group. `ChatConsumer` uses `database_sync_to_async` for ORM access so database work does not block the async event loop.

## 7. Database Information

### Profile picture flow

Profile images are stored by Django's `ImageField` below:

```text
profile_pictures/profile_pictures/<generated-file-name>
```

The development media configuration is:

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "profile_pictures"
```

In development, `config/urls.py` serves `/media/` directly. The home page uploads using multipart form data:

```html
<form method="post" action="/profile/update/" enctype="multipart/form-data">
  <input type="file" name="profile_picture" accept="image/*">
  <textarea name="bio"></textarea>
  <button type="submit">Save profile</button>
</form>
```

The page displays `profile.profile_picture.url` for the signed-in user and sends `participant_picture` in conversation data. Users without an image show their first username initial instead. For production, serve `MEDIA_ROOT` through a web server or object storage rather than Django's development media handler.

The configured database is SQLite:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

### Tables and important columns

#### `auth_user`
Django's built-in user table. Relevant columns are `id`, `username`, `email`, password hash, and account status fields. It is referenced by profiles, conversation members, and messages.

#### `accounts_profiles`
- `id`: primary key
- `user_id`: one-to-one foreign key to `auth_user`, cascade delete
- `bio`: optional text, maximum 500 characters
- `profile_picture`: optional uploaded image under `profile_pictures/`
- `created_at`: automatic creation timestamp

#### `chats_conversation`
- `id`: primary key
- `created_at`: automatic creation timestamp

#### `chats_conversationmember`
- `id`: primary key
- `conversation_id`: foreign key to conversation, cascade delete
- `user_id`: foreign key to `auth_user`, cascade delete
- `joined_at`: automatic creation timestamp
- unique constraint on `(conversation_id, user_id)`

#### `chats_message`
- `id`: primary key
- `conversation_id`: foreign key to conversation, cascade delete
- `sender_id`: foreign key to `auth_user`, cascade delete
- `content`: message text
- `created_at`: automatic creation timestamp
- `is_read`: boolean, default `false`

## 8. ER Diagram

```mermaid
erDiagram
    AUTH_USER ||--o| ACCOUNTS_PROFILE : has
    AUTH_USER ||--o{ CONVERSATION_MEMBER : joins
    CONVERSATION ||--o{ CONVERSATION_MEMBER : contains
    CONVERSATION ||--o{ MESSAGE : contains
    AUTH_USER ||--o{ MESSAGE : sends

    AUTH_USER {
        bigint id PK
        varchar username
        varchar email
        varchar password_hash
    }
    ACCOUNTS_PROFILE {
        bigint id PK
        bigint user_id FK UK
        text bio
        varchar profile_picture
        datetime created_at
    }
    CONVERSATION {
        bigint id PK
        datetime created_at
    }
    CONVERSATION_MEMBER {
        bigint id PK
        bigint conversation_id FK
        bigint user_id FK
        datetime joined_at
    }
    MESSAGE {
        bigint id PK
        bigint conversation_id FK
        bigint sender_id FK
        text content
        datetime created_at
        boolean is_read
    }
```

## 9. Code Responsibilities

- `config/settings.py`: registers Django, DRF, Channels, both local apps, SQLite, session/JWT authentication, and the development in-memory channel layer.
- `config/urls.py`: includes the account and chat route collections.
- `config/asgi.py`: sends HTTP traffic to Django and WebSocket traffic through `AuthMiddlewareStack` and `chats.routing`.
- `accounts/views.py`: handles browser login/logout/registration, API registration, user listing, and development password reset links.
- `accounts/serializers.py`: shapes user responses and creates users from API registration data.
- `chats/views.py`: checks membership, creates/reuses conversations, returns message history, stores REST messages, and deletes member-owned conversations.
- `chats/serializers.py`: controls message output and trims/rejects empty content.
- `chats/consumers.py`: controls WebSocket connection authorization, message persistence, group broadcast, and disconnect cleanup.
- `chats/routing.py`: maps `/ws/conversations/<id>/` to `ChatConsumer`.
- `accounts/templates/accounts/home.html`: renders the UI and contains the browser-side REST/WebSocket client.
- `*/tests.py`: verifies authentication-related flows, REST chat behavior, deletion ownership, and WebSocket persistence/broadcast.

## 10. Tests and Checks

Run all tests:

```powershell
python manage.py test
```

Run only chat tests:

```powershell
python manage.py test chats
```

Run Django configuration checks:

```powershell
python manage.py check
```

The implemented chat suite covers:

- Creating and reusing a direct conversation.
- Sending and reading REST messages.
- Blocking non-member history access.
- Allowing a member to delete a conversation and cascading messages.
- Blocking a non-member from deleting a conversation.
- Sending and persisting a message through WebSocket.

## 11. Production Notes

Before deployment:

1. Move `SECRET_KEY` to an environment variable and set `DEBUG = False`.
2. Set real `ALLOWED_HOSTS` and HTTPS/CSRF settings.
3. Use PostgreSQL or another production database instead of SQLite for concurrent workloads.
4. Replace `InMemoryChannelLayer` with Redis (`channels_redis`) when running multiple ASGI workers or servers.
5. Serve uploaded media and static files through a proper web server or object storage.
6. Configure a real email backend for password reset instead of the console backend.
7. Consider adding soft-delete, audit logs, and a separate per-message delete API if users should remove only their own messages rather than the entire conversation.
8. The current WebSocket handshake uses Django sessions. A token-authenticated WebSocket middleware is needed if a separate SPA or mobile client must authenticate sockets with JWT.
