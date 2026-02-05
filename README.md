# 💬 Chat Distribué - Django WebSocket Chat

## 📌 Description
Application de chat en temps réel développée avec Django et WebSockets pour un projet universitaire en systèmes distribués (MI RMSE).

## ✨ Fonctionnalités
- ✅ Chat en temps réel avec WebSockets
- ✅ Authentification utilisateur (inscription/connexion)
- ✅ Avatars personnalisés et bios
- ✅ Salons de discussion multiples
- ✅ Utilisateurs en ligne en temps réel
- ✅ Interface responsive (Bootstrap 5)
- ✅ Historique des messages

## 🛠️ Technologies
- **Backend** : Django, Django Channels, Daphne, SQLite
- **Frontend** : HTML, CSS, JavaScript, Bootstrap 5
- **Communication** : WebSockets (ASGI)

## 🚀 Installation Rapide

```bash
# 1. Cloner/initialiser
git clone [URL]  # ou créer un dossier
cd chat-distribue

# 2. Environnement virtuel
python -m venv venv
# Windows : venv\Scripts\activate
# Mac/Linux : source venv/bin/activate

# 3. Dépendances
pip install django channels channels-redis daphne pillow

# 4. Configuration
django-admin startproject chat_project .
python manage.py startapp accounts
python manage.py startapp chat

# 5. Migrations
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# 6. Lancer
python manage.py runserver
# Accès : http://localhost:8000