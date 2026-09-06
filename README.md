# Messenger

A real-time web messenger built with Django, Django REST Framework, Django Channels, and vanilla JavaScript.

## Features

- User registration, login, logout, and password reset flow
- User profiles with bio and profile pictures
- One-to-one conversations
- REST API for conversations and messages
- Real-time messaging with WebSockets
- Responsive layout for desktop and mobile browsers

## Tech Stack

- Python and Django
- Django REST Framework
- Django Channels and Daphne
- SQLite for local development
- HTML, CSS, and vanilla JavaScript

## Local Setup

```powershell
python -m venv chat
.\chat\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000/` and register two accounts to test messaging.

For testing from another device on the same Wi-Fi network:

```powershell
python manage.py runserver 0.0.0.0:8000
```

Then open `http://YOUR_LAPTOP_IP:8000/` on the other device. Add the laptop IP to `DJANGO_ALLOWED_HOSTS` in `.env` when needed.

## Project Structure

- `accounts/`: authentication, profiles, templates, and frontend assets
- `chats/`: conversations, messages, REST endpoints, and WebSocket consumer
- `config/`: Django and ASGI configuration
- `requirements.txt`: Python dependencies

This project is intended for local learning and portfolio demonstration. Production deployment requires secure secrets, a production database, HTTPS, and a persistent channel layer.

## Deploy on Render with Docker

1. Push the repository to GitHub.
2. In Render, choose **New > Blueprint** and select this repository.
3. Render will use `render.yaml` and the included `Dockerfile`.
4. After deployment, open the generated `https://*.onrender.com` URL and register a user.

The included configuration creates a Render Redis Key Value service and uses it for WebSocket channel communication. SQLite data is still suitable only for a portfolio demo; use PostgreSQL for persistent production data.