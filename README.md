# 🐳 Docker Status Dashboard

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

Een lichtgewicht, moderne Docker container monitoring dashboard met een prachtige **Gruvbox** thema, PWA ondersteuning, en real-time logs.

![Dashboard Preview](https://via.placeholder.com/800x400/282828/ebdbb2?text=Docker+Status+Dashboard)

---

## ✨ Features

### 📊 **Dashboard**
- 🔴🟢 **Container Status** - Real-time status van alle containers
- 💻 **CPU Usage** - Systeem CPU percentage
- 🧠 **RAM Usage** - Geheugen verbruik
- 💾 **Disk Usage** - Opslag ruimte
- ⏱️ **Uptime** - Systeem uptime

### 📝 **Live Logs**
- Bekijk container logs direct in de browser
- Tot 200 regels per request
- Auto-scroll naar laatste regels
- Klik op een container om direct logs te zien

### 🌙☀️ **Dark/Light Mode**
- **Gruvbox** thema (Dark & Light varianten)
- Thema wordt opgeslagen in browser
- Mooie, warme kleuren die prettig zijn voor de ogen

### 📱 **PWA Support**
- Installeer als app op iPhone, iPad, MacBook
- Voeg toe aan homescreen
- Offline basis functionaliteit

### 🔐 **Beveiliging**
- Session-based authenticatie
- Security headers (X-Frame-Options, CSP, XSS Protection)
- Gunicorn production server

---

## 🎨 Thema

Gebruikt het prachtige **Gruvbox** kleurenpalet:

| Element | Dark Mode | Light Mode |
|---------|-----------|------------|
| Background | `#282828` | `#fbf1c7` |
| Card | `#3c3836` | `#f2e5bc` |
| Text | `#ebdbb2` | `#3c3836` |
| Accent | `#fe8019` 🟠 | `#d65d0e` 🟠 |
| Running | `#b8bb26` 🟢 | `#79740e` 🟢 |
| Stopped | `#fb4934` 🔴 | `#9d0006` 🔴 |

---

## 🚀 Snelle Start

### Optie 1: Docker Compose (Aanbevolen)

```yaml
version: '3.8'
services:
  status-dashboard:
    image: ghcr.io/jphermans/docker-status-dashboard:latest
    container_name: status-dashboard
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - AUTH_USERNAME=admin
      - AUTH_PASSWORD=your-secure-password
      - SECRET_KEY=your-secret-key-here
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /usr/bin/docker:/usr/bin/docker:ro
```

```bash
docker-compose up -d
```

### Optie 2: Docker Run

```bash
docker run -d \
  --name status-dashboard \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker:ro \
  -e AUTH_USERNAME=admin \
  -e AUTH_PASSWORD=your-secure-password \
  -e SECRET_KEY=your-secret-key-here \
  ghcr.io/jphermans/docker-status-dashboard:latest
```

### Optie 3: Lokaal Bouwen

```bash
# Clone de repository
git clone https://github.com/jphermans/docker-status-dashboard.git
cd docker-status-dashboard

# Bouw de image
docker build -t docker-status-dashboard .

# Start de container
docker run -d \
  --name status-dashboard \
  -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /usr/bin/docker:/usr/bin/docker:ro \
  -e AUTH_USERNAME=admin \
  -e AUTH_PASSWORD=your-password \
  -e SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))") \
  docker-status-dashboard
```

---

## ⚙️ Configuratie

### Environment Variabelen

| Variabele | Beschrijving | Standaard |
|-----------|-------------|----------|
| `AUTH_USERNAME` | Login gebruikersnaam | `admin` |
| `AUTH_PASSWORD` | Login wachtwoord | *verplicht* |
| `SECRET_KEY` | Flask session key | *auto-generated* |

### Gebruik

1. Open `http://localhost:5000` in je browser
2. Login met je credentials
3. Bekijk container status, stats en logs
4. Schakel tussen dark/light mode met de 🌙/☀️ knop

---

## 📱 PWA Installatie

### iPhone / iPad (Safari)
1. Open de dashboard URL in Safari
2. Tik op de **Deel** knop
3. Tik op **Zet in beginscherm**
4. De app verschijnt op je homescreen 🎉

### Android (Chrome)
1. Open de dashboard URL in Chrome
2. Tik op de menu knop (⋮)
3. Tik op **App installeren**
4. De app wordt geïnstalleerd 🎉

### Desktop (Chrome/Edge)
1. Open de dashboard URL
2. Klik op het **installatie icoon** in de adresbalk
3. Of gebruik menu → **Installeer app**

---

## 🔒 Beveiliging

### Geïmplementeerd
- ✅ Session-based authenticatie (geen Basic Auth popups)
- ✅ X-Frame-Options: DENY
- ✅ X-Content-Type-Options: nosniff
- ✅ X-XSS-Protection: 1; mode=block
- ✅ Content-Security-Policy
- ✅ Referrer-Policy: strict-origin-when-cross-origin
- ✅ Server header verborgen
- ✅ Gunicorn production server

### Aanbevolen voor Productie
- 🔀 **HTTPS**: Gebruik een reverse proxy (Caddy, Nginx, Traefik)
- 🔑 **Sterk wachtwoord**: Gebruik een lang, uniek wachtwoord
- 🗝️ **SECRET_KEY**: Genereer een veilige random key

---

## 🛠️ Technologie

| Component | Technologie |
|-----------|------------|
| Backend | Python 3.11, Flask 3.0 |
| WSGI | Gunicorn |
| Frontend | Bootstrap 5, Vanilla JS |
| Thema | Gruvbox Color Palette |
| Container | Docker, python:3.11-slim |

---

## 📁 Project Structuur

```
docker-status-dashboard/
├── 📄 app.py              # Flask applicatie
├── 📄 Dockerfile          # Docker image definitie
├── 📄 requirements.txt    # Python dependencies
├── 📄 README.md           # Dit bestand
├── 📂 templates/
│   ├── 📄 index.html      # Dashboard template
│   └── 📄 login.html      # Login template
└── 📂 static/
    ├── 📄 manifest.json   # PWA manifest
    ├── 📄 sw.js           # Service Worker
    ├── 🖼️ icon-192.png    # App icon 192x192
    └── 🖼️ icon-512.png    # App icon 512x512
```

---

## 🤝 Bijdragen

Bijdragen zijn welkom! Voel je vrij om:
- 🐛 Bugs te rapporteren
- 💡 Features voor te stellen
- 🔧 Pull requests in te dienen

---

## 📄 Licentie

Dit project is gelicentieerd onder de MIT Licentie.

---

## 👤 Auteur

**JP Hermans**

- GitHub: [@jphermans](https://github.com/jphermans)

---

<p align="center">
  Gemaakt met ❤️ en ☕
</p>
