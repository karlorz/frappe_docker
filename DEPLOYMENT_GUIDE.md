# Frappe/ERPNext Development & Deployment Guide

A comprehensive guide for setting up Frappe/ERPNext development environments and production deployments on Linux and macOS.

## 🚀 Quick Start Options

### Option 1: Play with Docker (Fastest)
```bash
git clone https://github.com/karlorz/frappe_docker
cd frappe_docker
docker compose -f pwd.yml up -d

# Wait 5 minutes, then visit: http://localhost:8080
# Login: Administrator / admin
```

## 🌐 Site Access URLs

### Development Environment
- **URL**: `http://development.localhost:8000`
- **Port**: 8000 (development server)
- **Setup**: VSCode Dev Containers or manual development setup

### Production/PWD Environment  
- **URL**: `http://localhost:8080`
- **Port**: 8080 (configured in pwd.yml)
- **Setup**: Play with Docker configuration

**Important**: Development and production use different ports! Don't confuse the URLs.

### Option 2: ARM64 (Apple Silicon)
```bash
git clone https://github.com/karlorz/frappe_docker
cd frappe_docker

# Build ARM64 images
docker buildx bake --no-cache --set "*.platform=linux/arm64"

# Edit pwd.yml to add "platform: linux/arm64" to all services
# Then start
docker compose -f pwd.yml up -d
```

## 🛠️ Development Environment Setup

### VSCode Dev Containers (Recommended)

**Prerequisites:**
- Docker Desktop with 4GB+ RAM allocation
- Visual Studio Code

## 🚀 Development Server Start Options

### Option 1: Fast Command-Line (Recommended for Speed)

**Single Command - Complete Stack:**
```bash
# Starts web server + background workers + file watcher + scheduler
docker exec -it frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && source env/bin/activate && honcho start socketio watch schedule worker web"
```

**Separate Commands - More Control:**
```bash
# Terminal 1: Web Server (Essential)
docker exec -it frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && source env/bin/activate && bench --site development.localhost serve --port 8000 --noreload"

# Terminal 2: Background Worker (Required for Demo Data & Background Jobs)
docker exec -it frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && source env/bin/activate && bench --site development.localhost worker --queue default"

# Terminal 3: File Watcher (Optional - for hot-reload)
docker exec -it frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && source env/bin/activate && bench watch"
```

**Access Development Site**: `http://localhost:8000`

### Option 2: VSCode Debugger (Slower but with Debugging)

Use the **"Honcho + Web debug"** launch profile from `.vscode/launch.json`:
- Includes web server + all background services
- Slower startup but provides debugging capabilities
- **Never use "Bench Web" alone** - it lacks background workers needed for demo data

**Critical**: Always ensure background workers are running when testing demo data functionality!
- Dev Containers extension

**Setup Steps:**
```bash
# Clone and setup
git clone https://github.com/karlorz/frappe_docker
cd frappe_docker

# Copy configurations
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode

# Open in VSCode
code .
# Command Palette (Ctrl/Cmd+Shift+P) → "Dev Containers: Reopen in Container"
```

**Inside Container Setup:**
```bash
# Create bench
bench init --skip-redis-config-generation frappe-bench
cd frappe-bench

# Configure for containers
bench set-config -g db_host mariadb
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379
bench set-config -g redis_socketio redis://redis-queue:6379

# Create site with MariaDB
bench new-site --mariadb-user-host-login-scope=% --db-root-password 123 --admin-password admin development.localhost

# Install ERPNext
bench get-app --branch version-15-dev --resolve-deps erpnext https://github.com/karlorz/erpnext
bench --site development.localhost install-app erpnext

# Enable developer mode
bench --site development.localhost set-config developer_mode 1
bench --site development.localhost clear-cache

# Start development server
bench start
```

**Access your site:** http://development.localhost:8000

### Automated Development Setup
```bash
# Quick setup with installer script
python development/installer.py

# Custom setup
python development/installer.py --help

# Example with custom apps
python development/installer.py \
  --apps-json custom-apps.json \
  --site-name myproject.localhost \
  --admin-password mypassword
```

### Custom Apps Development

**Using Custom ERPNext Fork:**
```bash
# Modify development/apps-example.json for your fork
{
  "url": "https://github.com/yourusername/erpnext.git",
  "branch": "your-custom-branch"
}

# Run installer with your custom apps
python development/installer.py --apps-json development/apps-example.json
```

**Adding Additional Custom Apps:**
```bash
# Inside your bench directory
cd frappe-bench

# Add custom app
bench get-app --branch main https://github.com/yourorg/yourapp
bench --site development.localhost install-app yourapp

# For private repositories
bench get-app --branch main https://TOKEN@github.com/yourorg/private-app
```

**Custom ERPNext Development Workflow:**
```bash
# Set up upstream tracking for your fork
cd frappe-bench/apps/erpnext
git remote add upstream https://github.com/frappe/erpnext.git
git fetch upstream

# Create feature branches
git checkout -b feature/custom-module version-15-dev

# Sync with upstream periodically
git fetch upstream
git checkout version-15-dev
git merge upstream/version-15  # or rebase if preferred
```

### Database Options

**PostgreSQL Setup:**
```bash
# Edit .devcontainer/docker-compose.yml - uncomment postgresql service
# Create site with PostgreSQL
bench new-site --db-type postgres --db-host postgresql mysite.localhost

# Configure PostgreSQL credentials in common_site_config.json
bench config set-common-config -c root_login postgres
bench config set-common-config -c root_password '"123"'
```

### Debugging with VSCode

**Method 1: Launch Configuration**
```bash
# Start all services except web
honcho start socketio watch schedule worker_short worker_long

# Then use VSCode debugger: "Start Frappe Web Server"
```

**Method 2: Launch Configuration Available:**
- "Honcho SocketIO Watch Schedule Worker"
- "Start Frappe Web Server"
- Various worker debugging configs

### Version-Specific Setup

**Frappe v14:**
```bash
nvm use v16
PYENV_VERSION=3.10.13 bench init --frappe-branch version-14 frappe-bench
```

**Frappe v13:**
```bash
nvm use v14
PYENV_VERSION=3.9.17 bench init --frappe-branch version-13 frappe-bench
```

## 🖥️ Bare Metal Installation

### Linux (Ubuntu/Debian)

**Install Dependencies:**
```bash
# System packages
sudo apt update && sudo apt install -y \
  python3-dev python3-pip python3-venv git build-essential \
  libssl-dev libffi-dev libmysqlclient-dev libpq-dev \
  redis-server mariadb-server nginx nodejs npm \
  wkhtmltopdf xvfb libfontconfig

# Install bench
pip3 install frappe-bench

# Configure MariaDB
sudo mysql_secure_installation
sudo mysql -u root -p -e "UPDATE mysql.user SET Password=PASSWORD('yourpassword') WHERE User='root'"
```

**Setup Frappe:**
```bash
# Initialize bench
bench init --frappe-branch version-15-dev frappe-bench
cd frappe-bench

# Create new site
bench new-site mysite.local

# Install ERPNext
bench get-app --branch version-15-dev erpnext https://github.com/karlorz/erpnext
bench --site mysite.local install-app erpnext

# Start development
bench start
```

### macOS Setup

**Install Dependencies:**
```bash
# Using Homebrew
brew install python3 git node mariadb redis nginx
brew install --cask wkhtmltopdf

# Start services
brew services start mariadb
brew services start redis

# Install bench
pip3 install frappe-bench
```

**Setup Process:** (Same as Linux above)

### Production Setup (Linux)
```bash
# Setup production environment
sudo bench setup production ubuntu --yes

# Enable site
bench --site mysite.local enable-scheduler
bench --site mysite.local set-maintenance-mode off

# Setup SSL (optional)
sudo bench setup lets-encrypt mysite.local
```

## 🚢 Production Deployment

### Single Server Docker Deployment

**Prerequisites:**
```bash
# Install Docker
curl -fsSL https://get.docker.com | bash

# Install Docker Compose V2
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 \
  -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose
```

**Deploy:**
```bash
git clone https://github.com/karlorz/frappe_docker
cd frappe_docker

# Configure environment
cp example.env .env
nano .env  # Edit with your settings

# Deploy
docker compose -f compose.yaml up -d
```

### Environment Configuration (.env)
```env
# Version Configuration
ERPNEXT_VERSION=v15.78.1
FRAPPE_VERSION=v15.0.0

# Database Configuration
DB_PASSWORD=your_secure_password_here

# Site Configuration
FRAPPE_SITE_NAME_HEADER=yourdomain.com
HTTP_PUBLISH_PORT=8080

# SSL Configuration
LETSENCRYPT_EMAIL=admin@yourdomain.com
SITES=`yourdomain.com`

# Optional: External Services
# DB_HOST=external-db-host
# REDIS_CACHE=redis://external-redis:6379
```

### Multi-Site Setup
```env
# Multiple sites example
SITES=`site1.com`,`site2.com`,`site3.com`
```

### Custom Apps in Production
```bash
# Create apps.json
cat > apps.json << EOF
[
  {
    "url": "https://github.com/karlorz/erpnext",
    "branch": "version-15-dev"
  },
  {
    "url": "https://github.com/yourorg/custom-app",
    "branch": "main"
  }
]
EOF

# Build with custom apps
APPS_JSON_BASE64=$(base64 -w 0 apps.json) docker buildx bake \
  --set "*.args.APPS_JSON_BASE64=$APPS_JSON_BASE64"
```

## 🔧 Common Operations

### Site Management
```bash
# Create new site
docker compose exec backend bench new-site newsite.local

# Install app on site
docker compose exec backend bench --site newsite.local install-app erpnext

# Backup site
docker compose exec backend bench --site mysite.local backup

# Restore site
docker compose exec backend bench --site mysite.local restore backup_file.sql
```

### Updates and Maintenance
```bash
# Update to new version
# Edit .env with new ERPNEXT_VERSION
docker compose pull
docker compose up -d

# Update apps in development
cd frappe-bench
bench update

# Migrate after updates
bench --site mysite.local migrate
```

### Updating Apps from karlorz Repositories

**For Development Environment:**
```bash
# Update Frappe Framework from karlorz/frappe
docker exec frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench/apps/frappe && git pull upstream version-15-dev"

# Update ERPNext from karlorz/erpnext
docker exec frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench/apps/erpnext && git pull upstream version-15-dev"

# Rebuild assets after updates
docker exec frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench build"
```

**Alternative Methods:**
```bash
# Method 1: Using bench update (comprehensive)
docker exec frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench update"

# Method 2: Clean reinstall with latest
docker exec frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development && python installer.py --recreate-site --apps-json apps-example.json"
```

**Note**: The development container is already configured to use karlorz repositories:
- Frappe: `https://github.com/karlorz/frappe` (branch: version-15-dev)
- ERPNext: `https://github.com/karlorz/erpnext` (branch: version-15-dev)

### Monitoring and Logs
```bash
# View service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f queue-long

# View application logs
docker compose exec backend tail -f /home/frappe/frappe-bench/logs/web.log

# Monitor resource usage
docker stats
```

## 🔍 Troubleshooting

### Common Issues

**Site Creation Timeout:**
```bash
# Wait 5+ minutes for initial site creation
docker compose logs -f create-site

# Check container health
docker compose ps
```

**Permission Issues:**
```bash
# Fix ownership (development)
docker compose exec backend chown -R frappe:frappe /workspace/development

# Check file permissions
ls -la sites/
```

**Database Connection Issues:**
```bash
# Check database service
docker compose exec mariadb mysql -u root -ppassword

# Verify site configuration
cat sites/common_site_config.json
```

**Memory Issues:**
```bash
# Increase Docker Desktop memory allocation to 4GB+
# Or reduce workers in production

# Check memory usage
docker stats
free -h
```

### Development Issues

**Database Already Exists Error:**
```bash
# Drop existing site to start fresh
cd frappe-bench && bench drop-site development.localhost --force

# Or clean restart containers
docker-compose -f .devcontainer/docker-compose.yml --project-name 'frappe_docker_devcontainer' down
docker volume rm frappe_docker_devcontainer_mariadb-data
docker-compose -f .devcontainer/docker-compose.yml --project-name 'frappe_docker_devcontainer' up -d

# Then re-run installer
python development/installer.py
```

**Git Dubious Ownership Errors:**
```bash
# Fix git safe directory issues (automatically handled by installer.py)
git config --global --add safe.directory /workspace/development/frappe-bench/apps/erpnext
git config --global --add safe.directory /workspace/development/frappe-bench/apps/frappe
```

**VSCode Extension Problems:**
```bash
# Reinstall Python extension in container
# Command Palette → "Developer: Reload Window"
```

**Node/Python Version Issues:**
```bash
# Check available versions
nvm ls
pyenv versions

# Switch versions
nvm use v16
PYENV_VERSION=3.10.13 bench init ...
```

**Memory Allocation Issues:**
```bash
# Increase Docker Desktop memory to 4GB+ minimum
# Recommended: 6-8GB for smooth development

# Monitor memory usage
docker stats
```

## 📚 Additional Resources

- **Official Documentation:** https://frappeframework.com/docs
- **ERPNext Documentation:** https://docs.erpnext.com
- **Community Forum:** https://discuss.frappe.io
- **GitHub Issues:** https://github.com/frappe/frappe_docker/issues
- **Docker Documentation:** https://docs.docker.com

## 🔐 Security Notes

### Production Security Best Practices
- Change default passwords in production environments
- Use environment variables for secrets management
- Enable SSL/TLS for production sites
- Regular backups and security updates
- Network isolation for production deployments
- Use secrets management for sensitive data

### Security Improvements Implemented
**Critical Security Vulnerabilities Fixed** (September 2025):
- **Issue**: `ignore_permissions=True` bypassed Frappe's Role-Based Access Control (RBAC) system
- **Files Affected**: `setup_wizard.py`, `demo.py`
- **Solution**: Replaced with context-aware permission flags
- **Impact**: Prevents unauthorized permission bypass in production

```python
# Before (Vulnerable):
doc.insert(ignore_permissions=True)

# After (Secure):
doc.insert(ignore_permissions=frappe.flags.in_setup_wizard or frappe.flags.in_install)
```

### Development Security Considerations
- **Context-Aware Permissions**: Permission bypass only allowed during setup/installation
- **Atomic Operations**: Department creation uses race-condition-safe operations
- **Input Validation**: Proper validation and sanitization of user inputs
- **Error Handling**: Secure error logging without exposing sensitive information

### Code Security Features
- **Shared Utilities**: Centralized, audited functions for common operations
- **Caching Strategy**: Performance optimizations without compromising security
- **Transaction Safety**: Proper database transaction handling with savepoints
- **Exception Handling**: Graceful error recovery that maintains system integrity

---

**Note:** This guide covers Docker-based deployments primarily. For traditional bare-metal installations, refer to the official Frappe/ERPNext installation guides.