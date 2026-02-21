# 🔐 Docker Status Dashboard

A secure, feature-rich web dashboard for monitoring and managing Docker containers with Two-Factor Authentication (2FA), rate limiting, and comprehensive security features.

![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Security](https://img.shields.io/badge/Security-Hardened-green)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![Flask](https://img.shields.io/badge/Flask-3.0-red)

## ✨ Features

### 📊 Dashboard
- **Real-time Container Monitoring** - View all containers with status, image, and port information
- **System Statistics** - CPU, RAM, disk usage, and system uptime
- **Container Management** - Start, stop, restart containers with one click
- **Log Viewer** - View and export container logs
- **Image Management** - List and prune unused Docker images

### 🔐 Security Features

| Feature | Description |
|---------|-------------|
| **TOTP 2FA** | Time-based One-Time Password authentication (30-second codes) |
| **QR Code Setup** | Easy setup with Google Authenticator, Authy, or compatible apps |
| **Backup Codes** | 10 one-time backup codes for account recovery |
| **CSRF Protection** | Flask-WTF token-based protection against cross-site attacks |
| **Rate Limiting** | 5 login attempts per minute per IP address |
| **Security Headers** | X-Frame-Options, CSP, X-Content-Type-Options, Referrer-Policy |
| **Secure Cookies** | HttpOnly, SameSite=Lax, 2-hour session timeout |
| **Input Validation** | Regex-based container name validation, no shell injection |

### 👤 User Management
- **Password Change** - Secure password updates with strength indicator
- **Persistent Storage** - Passwords and 2FA settings persist across container rebuilds

## 🚀 Quick Start

### Prerequisites
- Docker installed on your host system
- Access to Docker socket (`/var/run/docker.sock`)

### 1. Clone the Repository
```bash
git clone https://github.com/jphermans/docker-status-dashboard.git
cd docker-status-dashboard
```

### 2. Create Environment File
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
AUTH_USERNAME=admin
AUTH_PASSWORD=your-secure-password
```

### 3. Build and Run
```bash
# Build the Docker image
docker build -t docker-status-dashboard:latest .

# Run the container
docker run -d \
  --name status-dashboard \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY="$(grep SECRET_KEY .env | cut -d'=' -f2)" \
  -e AUTH_USERNAME="$(grep AUTH_USERNAME .env | cut -d'=' -f2)" \
  -e AUTH_PASSWORD="$(grep AUTH_PASSWORD .env | cut -d'=' -f2)" \
  docker-status-dashboard:latest
```

### 4. Access the Dashboard
Open your browser and navigate to: `http://localhost:5000`

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret key for session encryption (min 32 chars) |
| `AUTH_USERNAME` | Yes | Dashboard login username |
| `AUTH_PASSWORD` | Yes | Dashboard login password (min 8 chars recommended) |

### Persistent Data
The `data` directory stores:
- `2fa_config.json` - TOTP secrets and backup codes
- `password.json` - Updated password (after password change)

## 📱 2FA Setup

### Enable 2FA
1. Login to the dashboard
2. Click **🔐 2FA** in the navigation bar
3. Scan the QR code with your authenticator app:
   - Google Authenticator
   - Authy
   - Microsoft Authenticator
   - 1Password
   - LastPass Authenticator
4. Enter the 6-digit code to verify
5. **Save your backup codes!**

### After 2FA Setup
- Login requires password + 2FA code
- Codes refresh every 30 seconds
- Use backup codes if you lose access to your authenticator

## 🛡️ Security Best Practices

### For Production
1. **Enable HTTPS** - Use a reverse proxy (nginx, Traefik) with SSL/TLS
2. **Change `SESSION_COOKIE_SECURE`** to `True` in `app.py` when using HTTPS
3. **Use strong secrets** - Generate a cryptographically secure `SECRET_KEY`
4. **Regular updates** - Keep dependencies updated
5. **Network security** - Consider firewall rules or VPN access

### Generate Secure Secret Key
```python
import secrets
print(secrets.token_hex(32))
```

## 📁 Project Structure

```
docker-status-dashboard/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker build configuration
├── .gitignore            # Git exclusions
├── .dockerignore         # Docker build exclusions
├── .env.example          # Environment template
├── README.md             # This file
├── templates/
│   ├── index.html        # Main dashboard
│   ├── login.html        # Login page
│   ├── verify_2fa.html   # 2FA verification
│   ├── 2fa_setup.html    # 2FA setup wizard
│   ├── 2fa_status.html   # 2FA status page
│   └── change_password.html  # Password change form
├── static/
│   ├── icon-192.png      # PWA icon
│   ├── icon-512.png      # PWA icon
│   ├── sw.js             # Service worker
│   └── manifest.json     # PWA manifest
└── data/                  # Persistent data (mounted volume)
    ├── 2fa_config.json   # 2FA settings
    └── password.json     # Updated password
```

## 🔧 Dependencies

- **Flask** - Web framework
- **Flask-Login** - User session management
- **Flask-Limiter** - Rate limiting
- **Flask-WTF** - CSRF protection
- **pyotp** - TOTP 2FA implementation
- **qrcode** - QR code generation
- **psutil** - System statistics
- **gunicorn** - WSGI HTTP Server

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard (requires auth) |
| `/login` | GET/POST | Login page |
| `/logout` | GET | Logout user |
| `/verify-2fa` | GET/POST | 2FA verification |
| `/2fa-setup` | GET/POST | Setup 2FA |
| `/2fa-status` | GET | View 2FA status |
| `/change-password` | GET/POST | Change password |
| `/api/stats` | GET | System statistics |
| `/api/containers` | GET | List all containers |
| `/api/container/<name>/start` | POST | Start container |
| `/api/container/<name>/stop` | POST | Stop container |
| `/api/container/<name>/restart` | POST | Restart container |
| `/api/container/<name>/logs` | GET | Get container logs |
| `/api/images` | GET | List Docker images |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Flask framework and extensions
- Docker SDK
- pyotp for TOTP implementation

---

**Made with ❤️ by [jphermans](https://github.com/jphermans)**
