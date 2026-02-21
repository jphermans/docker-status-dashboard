from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_from_directory, Response, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import subprocess
import psutil
import os
import re
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

# Lazy imports for heavy libraries (only loaded when needed)
# pyotp, qrcode, BytesIO, base64 are imported inside functions

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security Configuration
app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required!")

if len(app.secret_key) < 32:
    raise RuntimeError("SECRET_KEY must be at least 32 characters!")

# Secure cookie configuration
app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
    WTF_CSRF_ENABLED=True,
    WTF_CSRF_TIME_LIMIT=None,
)

# CSRF Protection
csrf = CSRFProtect(app)

# Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = "strong"

# 2FA Configuration File
TWO_FA_FILE = os.path.join(os.path.dirname(__file__), '2fa_config.json')

def load_2fa_config():
    """Load 2FA configuration from JSON file"""
    if os.path.exists(TWO_FA_FILE):
        try:
            with open(TWO_FA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_2fa_config(config):
    """Save 2FA configuration to JSON file"""
    with open(TWO_FA_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def is_2fa_enabled(username):
    """Check if 2FA is enabled for user"""
    config = load_2fa_config()
    user_config = config.get(username, {})
    return user_config.get('enabled', False)

def get_2fa_secret(username):
    """Get TOTP secret for user"""
    config = load_2fa_config()
    user_config = config.get(username, {})
    return user_config.get('secret')

def verify_2fa_code(username, code):
    """Verify TOTP code for user"""
    import pyotp  # Lazy import
    secret = get_2fa_secret(username)
    if not secret:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)

def generate_backup_codes(count=10):
    """Generate backup recovery codes"""
    codes = [secrets.token_hex(4).upper() for _ in range(count)]
    hashed = [hashlib.sha256(code.encode()).hexdigest() for code in codes]
    return codes, hashed

def verify_backup_code(username, code):
    """Verify backup code and remove it if valid"""
    config = load_2fa_config()
    user_config = config.get(username, {})
    hashed_codes = user_config.get('backup_codes', [])
    code_hash = hashlib.sha256(code.upper().encode()).hexdigest()
    
    if code_hash in hashed_codes:
        hashed_codes.remove(code_hash)
        user_config['backup_codes'] = hashed_codes
        config[username] = user_config
        save_2fa_config(config)
        return True
    return False

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == os.getenv('AUTH_USERNAME', 'admin'):
        return User(user_id)
    return None

# Input validation
CONTAINER_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,62}$')

def validate_container_name(name):
    if not name or len(name) > 63:
        return False
    return bool(CONTAINER_NAME_PATTERN.match(name))

# Security Headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Server'] = 'SecureServer'
    return response

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f"Rate limit exceeded from IP: {get_remote_address()}")
    return render_template('login.html', error='Te veel pogingen. Wacht 1 minuut en probeer opnieuw.'), 429

# Static routes
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

# Login - Step 1: Password
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        valid_username = os.getenv('AUTH_USERNAME')
        valid_password = os.getenv('AUTH_PASSWORD')

        if username == valid_username and password == valid_password:
            if is_2fa_enabled(username):
                session['pending_user'] = username
                session['pending_2fa'] = True
                logger.info(f"Password OK for {username}, 2FA required")
                return redirect(url_for('verify_2fa'))
            else:
                user = User(username)
                login_user(user)
                logger.info(f"Successful login for user: {username}")
                return redirect(url_for('index'))
        else:
            logger.warning(f"Failed login attempt from IP: {get_remote_address()}")
            return render_template('login.html', error='Ongeldige gebruikersnaam of wachtwoord')

    return render_template('login.html')

# Login - Step 2: 2FA Verification
@app.route('/verify-2fa', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def verify_2fa():
    if 'pending_user' not in session or not session.get('pending_2fa'):
        return redirect(url_for('login'))
    
    username = session['pending_user']
    error = None
    
    if request.method == 'POST':
        code = request.form.get('totp_code', '').strip()
        
        if verify_2fa_code(username, code):
            session.pop('pending_user', None)
            session.pop('pending_2fa', None)
            user = User(username)
            login_user(user)
            logger.info(f"Successful 2FA login for user: {username}")
            return redirect(url_for('index'))
        
        if verify_backup_code(username, code):
            session.pop('pending_user', None)
            session.pop('pending_2fa', None)
            user = User(username)
            login_user(user)
            logger.info(f"Successful backup code login for user: {username}")
            return redirect(url_for('index'))
        
        error = 'Ongeldige code. Probeer opnieuw.'
        logger.warning(f"Failed 2FA attempt for {username}")
    
    return render_template('verify_2fa.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', two_fa_enabled=is_2fa_enabled(current_user.id))

# 2FA Setup Page
@app.route('/2fa-setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    # Lazy imports for heavy libraries (only loaded for 2FA setup)
    import pyotp
    import qrcode
    from io import BytesIO
    import base64
    
    username = current_user.id
    config = load_2fa_config()
    user_config = config.get(username, {})
    
    if user_config.get('enabled', False):
        return render_template('2fa_status.html', enabled=True)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'generate':
            secret = pyotp.random_base32()
            session['temp_2fa_secret'] = secret
            
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(name=username, issuer_name="Docker Dashboard")
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(uri)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return render_template('2fa_setup.html', secret=secret, qr_code=qr_base64, step='verify')
        
        elif action == 'verify':
            code = request.form.get('verify_code', '').strip()
            secret = session.get('temp_2fa_secret')
            
            if secret and pyotp.TOTP(secret).verify(code, valid_window=1):
                backup_codes, hashed_codes = generate_backup_codes(10)
                
                config[username] = {
                    'enabled': True,
                    'secret': secret,
                    'backup_codes': hashed_codes,
                    'created_at': datetime.now().isoformat()
                }
                save_2fa_config(config)
                session.pop('temp_2fa_secret', None)
                
                logger.info(f"2FA enabled for user: {username}")
                return render_template('2fa_setup.html', step='complete', backup_codes=backup_codes)
            else:
                return render_template('2fa_setup.html', secret=secret, qr_code=None, error='Ongeldige code. Probeer opnieuw.', step='verify')
    
    return render_template('2fa_setup.html', step='start')

# Disable 2FA
@app.route('/2fa-disable', methods=['POST'])
@limiter.limit("3 per minute")
@login_required
def disable_2fa():
    username = current_user.id
    password = request.form.get('password', '')
    code = request.form.get('totp_code', '')
    
    if password != os.getenv('AUTH_PASSWORD'):
        flash('Ongeldig wachtwoord', 'error')
        return redirect(url_for('setup_2fa'))
    
    if not verify_2fa_code(username, code):
        flash('Ongeldige 2FA code', 'error')
        return redirect(url_for('setup_2fa'))
    
    config = load_2fa_config()
    if username in config:
        config[username]['enabled'] = False
        config[username]['disabled_at'] = datetime.now().isoformat()
        save_2fa_config(config)
        logger.info(f"2FA disabled for user: {username}")
    
    flash('2FA is uitgeschakeld', 'success')
    return redirect(url_for('setup_2fa'))

# API: Stats
@app.route('/api/stats')
@login_required
def get_stats():
    try:
        import time
        cpu_usage = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        uptime = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"
        return jsonify({
            'cpu': round(cpu_usage, 1),
            'ram': round(mem.percent, 1),
            'ram_used': round(mem.used / (1024 * 1024)),
            'ram_total': round(mem.total / (1024 * 1024)),
            'disk': round(disk.percent, 1),
            'uptime': uptime,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: Containers
@app.route('/api/containers')
@login_required
def get_containers():
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}|{{.Status}}|{{.Image}}|{{.ID}}|{{.Ports}}'],
            capture_output=True, text=True, timeout=10
        )
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 5:
                    containers.append({
                        'name': parts[0],
                        'status': parts[1],
                        'image': parts[2],
                        'id': parts[3][:12],
                        'ports': parts[4],
                        'running': 'Up' in parts[1]
                    })
        return jsonify(containers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: Container Actions
@app.route('/api/container/<name>/stats')
@login_required
def get_container_stats(name):
    if not validate_container_name(name):
        return jsonify({'error': 'Invalid name'}), 400
    try:
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', '{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}|{{.BlockIO}}', name],
            capture_output=True, text=True, timeout=10
        )
        parts = result.stdout.strip().split('|')
        if len(parts) >= 4:
            return jsonify({'cpu': parts[0], 'memory': parts[1], 'network': parts[2], 'disk': parts[3]})
        return jsonify({'cpu': 'N/A', 'memory': 'N/A', 'network': 'N/A', 'disk': 'N/A'})
    except:
        return jsonify({'cpu': 'N/A', 'memory': 'N/A', 'network': 'N/A', 'disk': 'N/A'})

@app.route('/api/container/<name>/details')
@login_required
def get_container_details(name):
    if not validate_container_name(name):
        return jsonify({'error': 'Invalid name'}), 400
    try:
        result = subprocess.run(['docker', 'inspect', '--format', '{{json .}}', name], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return jsonify({'error': 'Container not found'}), 404
        import json
        data = json.loads(result.stdout)
        return jsonify({
            'name': data.get('Name', '').lstrip('/'),
            'id': data.get('Id', '')[:12],
            'image': data.get('Config', {}).get('Image', 'N/A'),
            'status': data.get('State', {}).get('Status', 'N/A'),
            'running': data.get('State', {}).get('Running', False),
            'ip': data.get('NetworkSettings', {}).get('IPAddress', 'N/A'),
            'ports': [], 'volumes': [], 'env': [],
            'networks': list(data.get('NetworkSettings', {}).get('Networks', {}).keys())
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/container/<name>/start', methods=['POST'])
@login_required
def start_container(name):
    if not validate_container_name(name):
        return jsonify({'success': False, 'error': 'Invalid name'}), 400
    result = subprocess.run(['docker', 'start', name], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        return jsonify({'success': True, 'message': f'Container {name} gestart'})
    return jsonify({'success': False, 'error': result.stderr}), 500

@app.route('/api/container/<name>/stop', methods=['POST'])
@login_required
def stop_container(name):
    if not validate_container_name(name):
        return jsonify({'success': False, 'error': 'Invalid name'}), 400
    result = subprocess.run(['docker', 'stop', name], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        return jsonify({'success': True, 'message': f'Container {name} gestopt'})
    return jsonify({'success': False, 'error': result.stderr}), 500

@app.route('/api/container/<name>/restart', methods=['POST'])
@login_required
def restart_container(name):
    if not validate_container_name(name):
        return jsonify({'success': False, 'error': 'Invalid name'}), 400
    result = subprocess.run(['docker', 'restart', name], capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        return jsonify({'success': True, 'message': f'Container {name} herstart'})
    return jsonify({'success': False, 'error': result.stderr}), 500

@app.route('/api/container/<name>/logs')
@login_required
def get_container_logs(name):
    if not validate_container_name(name):
        return jsonify({'error': 'Invalid name'}), 400
    try:
        lines = min(request.args.get('lines', 200, type=int), 5000)
        result = subprocess.run(['docker', 'logs', '--tail', str(lines), name], capture_output=True, text=True, timeout=30)
        logs = result.stdout + result.stderr
        return jsonify({'logs': logs, 'container': name, 'timestamp': datetime.now().isoformat()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/container/<name>/logs/export')
@login_required
def export_container_logs(name):
    if not validate_container_name(name):
        return jsonify({'error': 'Invalid name'}), 400
    lines = min(request.args.get('lines', 1000, type=int), 10000)
    result = subprocess.run(['docker', 'logs', '--tail', str(lines), name], capture_output=True, text=True, timeout=60)
    logs = result.stdout + result.stderr
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return Response(logs, mimetype='text/plain', headers={'Content-Disposition': f'attachment;filename={safe_name}_logs_{timestamp}.txt'})

@app.route('/api/images')
@login_required
def get_images():
    try:
        result = subprocess.run(['docker', 'images', '--format', '{{.Repository}}:{{.Tag}}|{{.ID}}|{{.Size}}|{{.CreatedSince}}'], capture_output=True, text=True, timeout=10)
        images = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 4:
                    images.append({'name': parts[0], 'id': parts[1], 'size': parts[2], 'created': parts[3]})
        return jsonify(images)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/prune/images', methods=['POST'])
@login_required
def prune_images():
    result = subprocess.run(['docker', 'image', 'prune', '-f'], capture_output=True, text=True, timeout=60)
    return jsonify({'success': True, 'message': 'Ongebruikte images verwijderd'})

@app.route('/api/system')
@login_required
def get_system_info():
    result = subprocess.run(['docker', 'system', 'df'], capture_output=True, text=True, timeout=10)
    return jsonify({'df': result.stdout})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

# Password Change
@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    username = current_user.id
    
    if request.method == 'POST':
        current_pwd = request.form.get('current_password', '')
        new_pwd = request.form.get('new_password', '')
        confirm_pwd = request.form.get('confirm_password', '')
        
        # Validate current password
        if current_pwd != os.getenv('AUTH_PASSWORD'):
            flash('Huidig wachtwoord is onjuist', 'danger')
            return redirect(url_for('change_password'))
        
        # Validate new password
        if len(new_pwd) < 8:
            flash('Nieuw wachtwoord moet minimaal 8 tekens zijn', 'danger')
            return redirect(url_for('change_password'))
        
        if new_pwd != confirm_pwd:
            flash('Nieuwe wachtwoorden komen niet overeen', 'danger')
            return redirect(url_for('change_password'))
        
        # Update password in .env file
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        with open(env_file, 'w') as f:
            for line in lines:
                if line.startswith('AUTH_PASSWORD='):
                    f.write(f'AUTH_PASSWORD={new_pwd}\n')
                else:
                    f.write(line)
        
        logger.info(f"Password changed for user: {username}")
        flash('Wachtwoord succesvol gewijzigd!', 'success')
        return redirect(url_for('index'))
    
    return render_template('change_password.html')
