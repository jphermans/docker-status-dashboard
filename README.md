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
- **Persistent Storage** - Passwords and 2FA settings persist across container rebuilds via volume mount
- **Automatic Fallback** - Login checks stored password first, falls back to environment variable

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
SECRET_KEY=your-secure-random-key-here
AUTH_USERNAME=admin
AUTH_PASSWORD=your-secure-password
```

### 3. Create Data Directory (for persistence)
```bash
mkdir -p data
```

### 4. Build and Run
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
  -e SECRET_KEY=$(grep SECRET_KEY .env | cut -d'=' -f2) \
  -e AUTH_USERNAME=$(grep AUTH_USERNAME .env | cut -d'=' -f2) \
  -e AUTH_PASSWORD=$(grep AUTH_PASSWORD .env | cut -d'=' -f2) \
  docker-status-dashboard:latest
```

### 5. Access the Dashboard
Open your browser and navigate to: `http://your-server-ip:5000`

## 📁 Project Structure

```
docker-status-dashboard/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker build configuration
├── .gitignore            # Git exclusions
├── .dockerignore         # Docker build exclusions
├── .env.example          # Environment template
├── README.md             # This file
├── data/                 # Persistent data (volume mount)
│   ├── 2fa_config.json   # 2FA settings (auto-generated)
│   └── password.json     # Changed passwords (auto-generated)
├── templates/            # HTML templates
│   ├── index.html        # Dashboard
│   ├── login.html        # Login page
│   ├── verify_2fa.html   # 2FA verification
│   ├── 2fa_setup.html    # 2FA setup wizard
│   ├── 2fa_status.html   # 2FA status
│   └── change_password.html  # Password change
└── static/               # Static assets
    ├── icon-192.png
    ├── icon-512.png
    ├── sw.js
    └── manifest.json
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Flask secret key for session encryption |
| `AUTH_USERNAME` | Yes | Dashboard login username |
| `AUTH_PASSWORD` | Yes | Initial dashboard login password |

### Persistent Data

The `data/` directory stores:
- **2FA Configuration** (`2fa_config.json`) - TOTP secrets and backup codes
- **Changed Passwords** (`password.json`) - Updated passwords

> ⚠️ **Important**: Mount the `data/` directory to persist settings across container rebuilds!

## 📱 2FA Setup

1. Login to the dashboard
2. Click **🔐 2FA** in the navigation bar
3. Scan the QR code with your authenticator app:
   - Google Authenticator
   - Authy
   - Microsoft Authenticator
   - 1Password
   - LastPass Authenticator
4. Enter the 6-digit code to verify
5. **Save your backup codes!** Store them securely (password manager, printed copy)

### 2FA Reset
If you lose access to your authenticator and backup codes:
1. Delete `data/2fa_config.json` on the server
2. Restart the container
3. Login without 2FA and set it up again

## 🔑 Password Management

### Change Password
1. Login to the dashboard
2. Click **🔑 Password** in the navigation bar
3. Enter your current password
4. Enter and confirm your new password (min. 8 characters)
5. The new password is stored in `data/password.json`

### How It Works
- Login checks `data/password.json` first
- Falls back to `AUTH_PASSWORD` environment variable if no stored password
- Changes persist across container rebuilds when volume is mounted

## 🛡️ Security Best Practices

### Production Deployment

1. **Use HTTPS** - Place behind a reverse proxy (nginx, Traefik) with SSL
2. **Change default password** - Update password immediately after first login
3. **Enable 2FA** - Always enable two-factor authentication
4. **Restrict access** - Use firewall rules to limit access
5. **Regular updates** - Keep the container and dependencies updated
6. **Backup data/** - Regularly backup the `data/` directory

### Security Headers
The application sets these security headers:
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard (requires auth) |
| `/login` | GET/POST | Login page |
| `/logout` | GET | Logout |
| `/change-password` | GET/POST | Change password |
| `/2fa-setup` | GET/POST | 2FA setup wizard |
| `/2fa-status` | GET | 2FA status and management |
| `/verify-2fa` | GET/POST | 2FA verification |
| `/api/stats` | GET | System statistics |
| `/api/containers` | GET | List all containers |
| `/api/container/<name>/start` | POST | Start container |
| `/api/container/<name>/stop` | POST | Stop container |
| `/api/container/<name>/restart` | POST | Restart container |
| `/api/container/<name>/logs` | GET | Get container logs |
| `/api/images` | GET | List Docker images |
| `/api/prune/images` | POST | Prune unused images |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Flask framework
- Docker SDK
- pyotp for TOTP authentication
- qrcode for QR code generation
