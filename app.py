from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import subprocess
import os
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'admin':
        return User(user_id)
    return None

# Security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https://cdn.jsdelivr.net;"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Server'] = 'gunicorn'
    return response

# PWA Routes
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == os.getenv('AUTH_USERNAME') and password == os.getenv('AUTH_PASSWORD'):
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Ongeldige gebruikersnaam of wachtwoord')

    return render_template('login.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Main dashboard
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# API: Get system stats
@app.route('/api/stats')
@login_required
def get_stats():
    try:
        # CPU usage
        cpu_result = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=5)
        cpu_line = [l for l in cpu_result.stdout.split('\n') if '%Cpu' in l]
        cpu_usage = 0
        if cpu_line:
            parts = cpu_line[0].split()
            if len(parts) > 1:
                cpu_usage = 100 - float(parts[7].replace(',', '.'))

        # Memory usage
        mem_result = subprocess.run(['free', '-m'], capture_output=True, text=True, timeout=5)
        mem_lines = mem_result.stdout.split('\n')
        mem_parts = mem_lines[1].split()
        mem_total = int(mem_parts[1])
        mem_used = int(mem_parts[2])
        mem_percent = (mem_used / mem_total) * 100

        # Disk usage
        disk_result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
        disk_line = disk_result.stdout.split('\n')[1].split()
        disk_percent = int(disk_line[4].replace('%', ''))

        # Uptime
        uptime_result = subprocess.run(['uptime', '-p'], capture_output=True, text=True, timeout=5)
        uptime = uptime_result.stdout.strip().replace('up ', '')

        return jsonify({
            'cpu': round(cpu_usage, 1),
            'ram': round(mem_percent, 1),
            'ram_used': mem_used,
            'ram_total': mem_total,
            'disk': disk_percent,
            'uptime': uptime
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: Get container list
@app.route('/api/containers')
@login_required
def get_containers():
    try:
        result = subprocess.run(
            ['docker', 'ps', '-a', '--format', '{{.Names}}|{{.Status}}|{{.Image}}'],
            capture_output=True, text=True, timeout=10
        )
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 3:
                    name, status, image = parts[0], parts[1], parts[2]
                    is_running = 'Up' in status
                    containers.append({
                        'name': name,
                        'status': status,
                        'image': image,
                        'running': is_running
                    })
        return jsonify(containers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: Get container stats
@app.route('/api/container/<name>/stats')
@login_required
def get_container_stats(name):
    try:
        result = subprocess.run(
            ['docker', 'stats', '--no-stream', '--format', '{{.CPUPerc}}|{{.MemUsage}}|{{.NetIO}}', name],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip():
            parts = result.stdout.strip().split('|')
            if len(parts) >= 3:
                return jsonify({
                    'cpu': parts[0],
                    'memory': parts[1],
                    'network': parts[2]
                })
        return jsonify({'cpu': 'N/A', 'memory': 'N/A', 'network': 'N/A'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: Get container logs
@app.route('/api/container/<name>/logs')
@login_required
def get_container_logs(name):
    try:
        lines = request.args.get('lines', 100, type=int)
        result = subprocess.run(
            ['docker', 'logs', '--tail', str(lines), name],
            capture_output=True, text=True, timeout=15
        )
        return jsonify({
            'logs': result.stdout + result.stderr,
            'container': name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
