# 🌌 Smart Keyboard Converter AI

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Flask Version](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/database-MongoDB-brightgreen.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

> A super-premium, next-generation Single Page Application (SPA) designed to seamlessly convert text typed in the wrong keyboard layout (e.g., typing English characters while the keyboard is set to Arabic, or vice-versa) back into its intended layout. Powered by instant offline layout mapping and advanced AI (OpenRouter LLM fallback) to handle grammatical corrections and contextual adjustments.

---

## ✨ Features

### ⌨️ Layout & Conversion Engine
* **Instant Offline Conversion**: Real-time client-side keyboard layout character translation.
* **Layout Editor**: Add custom key mappings, duplicate existing mappings, import layout files, and export custom mappings as portable JSON files.
* **Dual-Language support**: RTL (Right-to-Left) and LTR layout translations (e.g., English to Arabic and vice-versa).
* **AI-Assisted Corrections**: Intelligent, contextual spelling correction using OpenRouter API models (`meta-llama/llama-3.3-70b-instruct:free`).

### 🛍️ Community Marketplace
* **Layout Discovery**: Search, browse, and filter public layouts by name, tags, and languages.
* **Dynamic Rating System**: Submit layout reviews with premium, interactive gold star hover selections.
* **Interactive Comments Feed**: Write layout notes, comment on community creations, and toggle collapsed comment panels (Show More/Less) to protect visual layout structures from comment clutter.
* **Favorites Registry**: Mark community layouts as favorites to keep them on your dashboard.

### 🛡️ Enterprise-Grade Security
* **Double-Layer Verification**: Signed-in and email-verified users are verified dynamically before they can publish layouts, export configurations, or comment/rate on the marketplace.
* **CSRF Protection**: All write endpoints are validated against CSRF token headers using HttpOnly cookie security.
* **Input Validation**: Strict schema enforcement using Pydantic classes on the API layer.
* **Rate Limiting**: Flask-Limiter prevents brute-force logins and registry flooding.

---

## 🎨 Technology Stack

* **Backend**: Flask, PyMongo (MongoDB), Flask-JWT-Extended, Flask-Mail (SMTP notification system), Flask-Limiter, Pydantic (data parsing).
* **Frontend**: Vanilla HTML5, CSS3 Cosmic Glassmorphism, Vanilla Javascript SPA architecture.
* **AI Integration**: OpenRouter API client wrapper with smart model fallback mapping.
* **Deployment**: Docker, Gunicorn production server, PM2.

---

## 📁 Repository Structure

```
.
├── app.py                      # Flask Application Entrypoint
├── Dockerfile                  # Production Container Configuration
├── requirements.txt            # Python Dependencies
├── configuration/              # Settings & Initialization
│   ├── config.py               # Env Configuration Parser
│   └── db.py                   # MongoDB Indexing & Init
├── middleware/                 # Request & Response Interceptors
│   └── security_headers.py     # CORS & Security Headers
├── models/                     # Data Schemas
│   └── schemas.py              # Pydantic Input Schemas
├── repositories/               # Database Queries & Logic
│   ├── base.py                 # Abstract Base Repository
│   ├── layout_repository.py    # Layouts & Marketplace Queries
│   ├── user_repository.py      # Users Management
│   └── history_repository.py   # Log History Stats
├── routes/                     # Blueprint API Endpoints
│   ├── auth.py                 # Auth & Profile
│   ├── converter.py            # AI & Base Conversions
│   ├── layouts.py              # User Layout Editor
│   └── marketplace.py          # Marketplace & Ratings
├── services/                   # Business Services
│   ├── auth_service.py         # Google OAuth & Sessions
│   └── mail_service.py         # SMTP Verification Mailer
├── static/                     # Frontend Static Assets
│   ├── css/
│   │   └── style.css           # Custom Glassmorphic Stylesheet
│   └── js/
│       ├── api.js              # Fetch Wrapper & CSRF Injector
│       ├── app.js              # SPA Routing & Navigation
│       ├── editor.js           # Layout Mapping Editor
│       └── marketplace.js      # Community Ratings & Details
└── templates/
    └── index.html              # Main SPA Layout Template
```

---

## 🚀 Getting Started

### 📋 Prerequisites
* Python 3.11+
* MongoDB 6.0+

### ⚙️ Environment Configuration
Create a `.env` file in the root directory:

```env
FLASK_ENV=development
FLASK_SECRET_KEY=your-flask-secret-key
MONGO_URI=mongodb://127.0.0.1:27017/
MONGO_DB=keyboard_converter
JWT_SECRET_KEY=your-jwt-secret-key

# SMTP Credentials
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME="Keyboard Converter"

# AI Integration
AI_ENABLED=True
OPENROUTER_API_KEY=your-openrouter-key
DEFAULT_AI_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Google OAuth Integration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-domain.site/auth/google/callback
```

### 💻 Installation

1. Clone the repository and navigate into it:
   ```bash
   git clone <repository-url>
   cd keyboard-converter
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the development server:
   ```bash
   python3 app.py
   ```
   The application will be running at [http://127.0.0.1:5454](http://127.0.0.1:5454).

---

## 🐳 Docker Deployment

The application is fully containerized and runs securely as a non-root user.

1. Build the Docker image:
   ```bash
   docker build -t keyboard-converter .
   ```

2. Run the Docker container:
   ```bash
   docker run -d -p 5454:5454 --env-file .env keyboard-converter
   ```

---

## 🛠️ Production PM2 Process Management

To manage and reload processes with PM2:

1. Register and start the application under PM2:
   ```bash
   pm2 start app.py --name keyboard-converter --interpreter .venv/bin/python3
   ```

2. Monitor logs in real time:
   ```bash
   pm2 logs keyboard-converter
   ```

3. Restart app and reload configs:
   ```bash
   pm2 restart keyboard-converter --update-env
   ```

---

## 🔒 Security Architectures

1. **CSRF & XSS Protection**: Submits JWT tokens inside Secure HttpOnly cookies while verifying CSRF matching headers on the script client wrapper.
2. **MongoDB Text Index Safety**: All collections are protected from injection using MongoDB text indexes with `language_override="none"` to prevent language validator bypass.
3. **Pydantic Validation Guard**: Restricts string lengths and limits numeric inputs across all routes to prevent memory leaks and Denial of Service (DoS) attacks.
4. **Verified Middleware Checks**: Restricts critical community actions to registered users who have completed SMTP email verification.
