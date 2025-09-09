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
bench init --frappe-path https://github.com/karlorz/frappe --frappe-branch version-15-dev --skip-redis-config-generation frappe-bench
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
bench init --frappe-path https://github.com/karlorz/frappe --frappe-branch version-15-dev --skip-redis-config-generation frappe-bench
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

#### Option A: Full Native Installation

**Install Dependencies:**
```bash
# Using Homebrew
brew install python3 git node mariadb redis nginx

# Note: wkhtmltopdf cask is discontinued as of Dec 2024
# For PDF generation, use container-based approach or alternatives

# Start services
brew services start mariadb
brew services start redis

# Install bench (requires breaking system packages on modern macOS)
pip3 install --break-system-packages frappe-bench
```

**Setup Process:** (Same as Linux above)

#### Option B: Hybrid Native Development + Container Services (Recommended for ARM64)

This approach runs the Frappe web server natively on macOS while using containerized database and Redis services. Ideal for development with better native performance.

**Prerequisites:**
```bash
# Install basic dependencies
brew install python3 git node mysql-client

# wkhtmltopdf via Rosetta 2 (Homebrew cask discontinued Dec 2024)
# Download x86_64 binary and create Rosetta 2 wrapper
# Example setup:
# 1. Download wkhtmltopdf x86_64 binary to ~/bin/wkhtmltopdf.bin
# 2. Create wrapper script at ~/bin/wkhtmltopdf:
cat > ~/bin/wkhtmltopdf << 'EOF'
#!/bin/bash
# Rosetta 2 wrapper for wkhtmltopdf on Apple Silicon
arch -x86_64 ~/bin/wkhtmltopdf.bin "$@"
EOF
chmod +x ~/bin/wkhtmltopdf
export PATH="$HOME/bin:$PATH"

# MySQL client tools need to be in PATH
export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"

# Option 1: Use uv for Python management (Recommended)
brew install uv
cd frappe_docker

# If pyproject.toml already exists with frappe-bench:
uv sync
source .venv/bin/activate

# Or to add frappe-bench to new project:
uv add frappe-bench
source .venv/bin/activate

# Option 2: Use pip with system packages
pip3 install --break-system-packages frappe-bench

# Note: Python venv creation may fail with bench init due to ensurepip issues
# Alternative: Use the container bench directly (see workaround below)
```

**Setup Container Backend Services:**
```bash
# 1. Copy devcontainer configuration
cp -R devcontainer-example .devcontainer

# 2. Modify .devcontainer/docker-compose.yml to expose ports (if not already done)
# Add port mappings to mariadb, redis-cache, and redis-queue services:

# mariadb service:
ports:
  - "3306:3306"

# redis-cache service:  
ports:
  - "6379:6379"

# redis-queue service:
ports:
  - "6380:6379"

# 3. Start containers with project name
docker-compose -f .devcontainer/docker-compose-local.yml --project-name 'frappe_docker_devcontainer' up -d
```

**Verify Container Services:**
```bash
# Test port connectivity
nc -z localhost 3306 && echo "MariaDB accessible"
nc -z localhost 6379 && echo "Redis cache accessible" 
nc -z localhost 6380 && echo "Redis queue accessible"
```

**Native Bench Setup:**

**Option 1: Automated Setup (Recommended)**
```bash
# Change to development directory
cd development

# Init frappe framework
bench init --frappe-path https://github.com/karlorz/frappe --frappe-branch version-15-dev --skip-redis-config-generation frappe-bench

# Use automated setup script
source ../.venv/bin/activate && python installer-local.py

# If you need to recreate the site:
source ../.venv/bin/activate && python installer-local.py --recreate-site

# Start web server (as shown in script output):
cd frappe-bench && source env/bin/activate && bench --site development.localhost serve --port 8000

# Access at: http://localhost:8000
# Login: Administrator / admin
```

**Key Features of installer-local.py:**
- ✅ **Environment Validation**: Automatically checks uv environment setup
- ✅ **MariaDB TCP Wrapper**: Creates `~/bin/mariadb` wrapper that forces TCP connections
- ✅ **Container Backend Config**: Configures bench to use localhost ports (3306, 6379, 6380)
- ✅ **ERPNext Installation**: Automatically installs ERPNext from karlorz repositories
- ✅ **Site Management**: Handles site creation and recreation with proper configuration
- ✅ **Error Handling**: Resolves common MySQL socket connection issues on macOS

**Option 2: Manual Setup**
```bash
# Change workplace
cd development

# Using uv environment (recommended):
source ../.venv/bin/activate && bench init --frappe-path https://github.com/karlorz/frappe --frappe-branch version-15-dev --skip-redis-config-generation frappe-bench

# Or using system pip:
bench init --frappe-path https://github.com/karlorz/frappe --frappe-branch version-15-dev --skip-redis-config-generation frappe-bench

cd frappe-bench

# Configure for container services
bench set-config -g db_host localhost
bench set-config -g db_port 3306
bench set-config -g redis_cache redis://localhost:6379
bench set-config -g redis_queue redis://localhost:6380
bench set-config -g redis_socketio redis://localhost:6380

# Create site using containerized MariaDB (ensure MySQL client in PATH)
export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"
bench new-site --mariadb-user-host-login-scope=% --db-root-password 123 --admin-password admin development.localhost

# Install ERPNext from karlorz repository (has demo data fixes)
bench get-app --branch version-15-dev --resolve-deps erpnext https://github.com/karlorz/erpnext
bench --site development.localhost install-app erpnext

# Start native web server (use --noreload, NOT --nothreading to avoid PDF hangs)
source env/bin/activate
bench --site development.localhost serve --port 8000 --noreload
```

**Workaround for Python venv Issues:**
If `bench init` fails due to Python venv creation issues on macOS, use the container bench directly:

```bash
# Ensure containers are running with project name
cp -R devcontainer-example .devcontainer
docker compose -f .devcontainer/docker-compose.yml --project-name 'frappe_docker_devcontainer' up -d

# Use existing container bench with exposed ports
docker exec -it frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && source env/bin/activate && bench --site development.localhost serve --port 8000 --noreload"

# Access at: http://localhost:8000
```

**Known Issues on macOS ARM64:**
- **Python venv creation fails**: Modern macOS has ensurepip issues with some Python versions
- **wkhtmltopdf discontinued**: Cask removed from Homebrew in Dec 2024, use Rosetta 2 wrapper for x86_64 binary
- **System packages protection**: Requires `--break-system-packages` for pip installations  
- **MySQL client required**: MariaDB client tools needed for site creation
- **PDF generation hanging**: Use `--noreload` instead of `--nothreading` to prevent server hangs during PDF generation
- ~~**Database initialization issues**: Site creation may fail with corrupted DB~~ - **FIXED** ✅
- ~~**MariaDB socket connection errors**: MariaDB trying to use socket instead of TCP~~ - **FIXED** ✅

**Tested Working Solutions:**
- ✅ **installer-local.py**: Fully automated hybrid setup with all fixes applied
- ✅ **MariaDB TCP wrapper**: Resolves socket connection issues automatically
- ✅ **Rosetta 2 wkhtmltopdf**: x86_64 binary wrapper for PDF generation on Apple Silicon
- ✅ **Multi-threaded server**: `--noreload` prevents PDF generation hangs
- ✅ **uv environment management**: Better than pip for dependency management
- ✅ **karlorz repositories**: Required for demo data fixes and correct branches
- ✅ **Container backend services**: Database and Redis run in containers with exposed ports

**Alternative: Use Container for Everything:**
If native setup is problematic, use the full container development environment as described in the VSCode Dev Containers section.

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

### GitHub Container Registry (GHCR) Multi-Arch Build & Deployment

**Prerequisites:**
```bash
# Install Docker with Buildx support
curl -fsSL https://get.docker.com | bash

# Install Docker Compose V2
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 \
  -o $DOCKER_CONFIG/cli-plugins/docker-compose
chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

# Setup buildx for multi-arch builds
docker buildx create --name multibuilder --use
docker buildx inspect --bootstrap
```

### Building Production Images

**Local Multi-Arch Build:**
```bash
git clone https://github.com/karlorz/frappe_docker
cd frappe_docker

# Build for both AMD64 and ARM64 platforms
docker buildx bake --platform linux/amd64,linux/arm64

# Build specific platform only
docker buildx bake --platform linux/arm64    # Apple Silicon
docker buildx bake --platform linux/amd64    # Intel/AMD

# Build and push to GitHub Container Registry
docker login ghcr.io -u yourusername -p YOUR_GITHUB_TOKEN
docker buildx bake --push --platform linux/amd64,linux/arm64

# View built images
docker images | grep ghcr.io/karlorz
```

**Available Image Targets:**
- `ghcr.io/karlorz/base:latest` - Base Frappe framework
- `ghcr.io/karlorz/build:latest` - Build tools and dependencies
- `ghcr.io/karlorz/erpnext:latest` - Complete ERPNext application
- `ghcr.io/karlorz/bench:latest` - Development toolchain

### GitHub Actions Automated Build

The repository includes automated CI/CD workflows for GHCR:

**Triggered Builds:**
- **Stable Releases**: `build_stable.yml` - Builds on version tags (v15.x.x)
- **Development**: `build_develop.yml` - Builds on pushes to main branch
- **Bench Tools**: `build_bench.yml` - Builds development tools

**Required GitHub Secrets:**
```bash
# GITHUB_TOKEN is automatically provided by GitHub Actions
# No additional secrets needed for GHCR authentication
```

**Workflow Features:**
- ✅ Multi-architecture builds (linux/amd64, linux/arm64)
- ✅ Automated version tagging from repository tags
- ✅ GitHub Container Registry integration
- ✅ Build caching for faster subsequent builds
- ✅ Automated testing and validation

### Single Server Docker Deployment

**Deploy:**
```bash
git clone https://github.com/karlorz/frappe_docker
cd frappe_docker

# Configure environment
cp example.env .env
nano .env  # Edit with your settings

# Deploy using GHCR images
docker compose -f compose.yaml up -d
```

### Environment Configuration (.env)
```env
# Version Configuration  
ERPNEXT_VERSION=v15.78.1
FRAPPE_VERSION=v15.0.0

# GHCR Image Configuration (uses karlorz repositories)
CUSTOM_IMAGE=ghcr.io/karlorz/erpnext
CUSTOM_TAG=${ERPNEXT_VERSION}
PULL_POLICY=always

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

**Basic Site Operations:**
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

**Site Reset Commands (For 500 Errors & Database Issues):**

When encountering 500 errors related to database metadata (e.g., `frappe/database/database.py:839`), use these commands in order:

```bash
# 1. Clear cache and rebuild assets (fixes most asset-related 500 errors)
docker-compose -f pwd.yml exec backend bench clear-cache
docker-compose -f pwd.yml exec backend bench build

# 2. Run database migration (fixes metadata and schema issues)
docker-compose -f pwd.yml exec backend bench migrate

# 3. If above doesn't work, reinstall the site (preserves data)
docker-compose -f pwd.yml exec backend bench --site localhost reinstall

# 4. Complete site reset (last resort - recreates entire site)
docker-compose -f pwd.yml exec backend bench --site localhost drop-site --force
docker-compose -f pwd.yml exec backend bench new-site --mariadb-user-host-login-scope=% --db-root-password 123 localhost
docker-compose -f pwd.yml exec backend bench --site localhost install-app erpnext

# 5. Restart all services after any major changes
docker-compose -f pwd.yml restart
```

**Recommended Approach:**
1. Start with commands 1 and 2 for most 500 errors
2. Use command 3 if migration doesn't resolve the issue
3. Only use command 4 for complete site recreation (data loss occurs)
4. Always restart services after major changes

**Common Error Patterns:**
- `frappe/database/database.py:839` → Usually fixed by migration (command 2)
- Asset 404 errors → Fixed by cache clearing and building (command 1)
- Corrupted metadata → Fixed by reinstallation or complete reset (commands 3-4)

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

### Docker Desktop Issues (Windows)

**Git Bash Mount Path Errors:**
```bash
# Error: "mkdir /run/desktop/mnt/host/d: file exists"
# This occurs when Docker Desktop's internal VM has mount path conflicts

# Solution 1: Restart Docker Desktop (Most Effective)
# 1. Close Docker Desktop completely
# 2. Restart Docker Desktop
# 3. Retry the docker-compose command

# Solution 2: Use MSYS_NO_PATHCONV for Git Bash
export MSYS_NO_PATHCONV=1
docker-compose -f .devcontainer/docker-compose.yml --project-name 'frappe_docker_devcontainer' up -d

# Solution 3: Use PowerShell Instead of Git Bash
# Git Bash has path conversion issues that PowerShell doesn't have
```

**File Sharing Configuration (Newer Docker Desktop Versions):**

Docker Desktop file sharing settings have moved in newer versions:

**Docker Desktop 4.6+ (Current):**
- Go to **Settings → Resources → File sharing**
- If "File sharing" is missing, it means Docker Desktop now uses on-demand sharing
- You'll be prompted to share folders automatically when first mounting them

**Docker Desktop 4.0-4.5:**
- Go to **Settings → Shared Folders**
- Manually add `D:\local\frappe_docker` to shared folders

**On-Demand File Sharing (Latest Versions):**
```bash
# When you first run a volume mount, Docker Desktop will prompt:
# "Docker Desktop wants to share D:\local\frappe_docker"
# Select "Share it" to automatically add to shared folders

# If no prompt appears but mounts fail:
# 1. Check Docker Desktop → Settings → General → "Use file sharing based on user identity"
# 2. Ensure your Windows user has access to the directory
# 3. Try running Docker Desktop as Administrator (temporarily)
```

**Alternative Mount Formats for Windows:**
```yaml
# Option 1: Windows-style absolute path (Recommended)
volumes:
  - "D:\\local\\frappe_docker:/workspace:cached"

# Option 2: Unix-style path for Docker Desktop
volumes:
  - "/d/local/frappe_docker:/workspace:cached"

# Option 3: PowerShell environment variable
volumes:
  - "${PWD}:/workspace:cached"
```

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

**MariaDB Connection Issues (macOS Hybrid Setup):**
```bash
# Error: "Can't connect to local MySQL server through socket '/tmp/mysql.sock'"
# Solution: The installer-local.py automatically creates a TCP wrapper

# Manual fix if needed:
cat > ~/bin/mariadb << 'EOF'
#!/bin/bash
exec /opt/homebrew/opt/mysql-client/bin/mysql --protocol=TCP "$@"
EOF
chmod +x ~/bin/mariadb

# Add to PATH
export PATH="$HOME/bin:$PATH"

# Test connection
mariadb -h localhost -P 3306 -u root -p123 -e "SELECT VERSION();"
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

*Container Development Setup:*
```bash
# Drop existing site to start fresh
cd frappe-bench && bench drop-site development.localhost --force

# Or clean restart containers
docker compose -f .devcontainer/docker-compose.yml --project-name 'frappe_docker_devcontainer' down
docker volume rm frappe_docker_devcontainer_mariadb-data
docker compose -f .devcontainer/docker-compose.yml --project-name 'frappe_docker_devcontainer' up -d

# Then re-run installer
python development/installer.py
```

*Hybrid macOS Setup:*
```bash
# Use the installer script's recreate option
cd development
source ../.venv/bin/activate && python installer-local.py --recreate-site

# Or manually drop database if needed
export PATH="$HOME/bin:/opt/homebrew/opt/mysql-client/bin:$PATH"
mariadb -h localhost -P 3306 -u root -p123 -e "DROP DATABASE IF EXISTS _randomdatabaseid;"
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