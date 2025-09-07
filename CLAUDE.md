# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains Docker containerization for Frappe Framework and ERPNext - a complete enterprise resource planning (ERP) system. The architecture follows a microservices pattern with separate containers for different components of the Frappe/ERPNext stack.

## Source Code Repositories

**IMPORTANT**: For git history analysis and framework investigation, use these source repositories instead of the Docker development copies:

### **Primary Source Repositories**
- **Frappe Framework**: `/Users/karlchow/Desktop/code/frappe` 
  - Branch: `version-15-dev`
  - Full git history available  
  - Use for framework-level investigations
  - **Note**: Contains fixes for demo data setup wizard issue (sanitize_input removal)

- **ERPNext**: `/Users/karlchow/Desktop/code/karlorz/erpnext`
  - Branch: `version-15-dev` 
  - Full git history available
  - Use for ERPNext-specific investigations

### **Docker Development Environment** 
- **Path**: `/Users/karlchow/Desktop/code/frappe_docker/development/frappe-bench/apps/`
- **Purpose**: Development and testing only
- **Limitation**: Does NOT contain complete git history
- **Usage**: Code editing, testing, debugging only

## Key Architecture Components

### Container Structure
- **Backend**: Frappe/ERPNext application server (Gunicorn)
- **Frontend**: Nginx reverse proxy serving static assets
- **Database**: MariaDB (default) or PostgreSQL for data persistence
- **Redis**: Two instances - one for caching, one for job queuing
- **Queue Workers**: Background job processing (short/long queues)
- **Scheduler**: Cron-like job scheduler
- **WebSocket**: Real-time communication via Socket.IO

### Image Types
- **Production Images** (`images/production/`): Multi-stage builds for production deployment
- **Custom Images** (`images/custom/`): For adding custom Frappe apps
- **Bench Images** (`images/bench/`): Development tooling container
- **Layered Images** (`images/layered/`): Alternative build approach

## Tool Usage Guidelines

### File System Exploration Best Practices

**IMPORTANT: Glob tool limitations with development directory**
The Glob tool may not properly detect files in `development/frappe-bench/apps/*` even after .gitignore modifications. Always use Bash commands first for file system exploration in development directories:

```bash
# Use these commands instead of Glob for development directory
ls -la development/frappe-bench/apps/
find development/frappe-bench/apps -name "*.py" -type f | head -10
ls -la development/frappe-bench/sites/
```

**Recommended approach:**
1. Use Bash commands to explore file structure first
2. Use Read tool once file paths are confirmed via Bash
3. Use Glob tool for other project areas where it works reliably

This ensures accurate file system awareness for ERPNext/Frappe development work.

### Docker Container Operations

**Container Management:**
```bash
# List running containers
docker ps -a | grep frappe

# Current container names (as of this session):
# - frappe_docker_devcontainer-frappe-1 (main development container)
# - frappe_docker_devcontainer-mariadb-1 (database)
# - frappe_docker_devcontainer-redis-cache-1 (cache)
# - frappe_docker_devcontainer-redis-queue-1 (queue)
```

**Executing Commands in Container:**
```bash
# Basic command execution (no TTY needed for simple commands)
docker exec frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && [command]"

# Examples:
docker exec frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench build"
docker exec frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench --version"

# Interactive session (when TTY is available)
docker exec -it frappe_docker_devcontainer-frappe-1 bash
```

**Asset Building:**
```bash
# Build static assets (required after code changes or 404 asset errors)
docker exec frappe_docker_devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench build"
```

**Common Troubleshooting:**
- If you see 404 errors for assets like `*.bundle.*.css` or `*.bundle.*.js`, run `bench build`
- Container names may vary between sessions - always check with `docker ps -a | grep frappe`
- Commands executed inside container should use `/workspace/development/frappe-bench` as working directory

## Common Development Commands

### Site Access URLs
**IMPORTANT: Correct development site URLs**
- **Development Environment**: `http://development.localhost:8000` or `http://localhost:8000`
- **Production/PWD Environment**: `http://localhost:8080` (configured in pwd.yml)

**Note**: Previous documentation incorrectly listed localhost:8080 for development - this is wrong!

### Quick Start Commands
```bash
# Clone and setup
git clone https://github.com/frappe/frappe_docker
cd frappe_docker

# Start with Play with Docker configuration
docker compose -f pwd.yml up -d

# For ARM64 (Apple Silicon)
docker buildx bake --no-cache --set "*.platform=linux/arm64"
# Then edit pwd.yml to add platform: linux/arm64 to all services

# Development with VSCode Dev Containers
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode
```

### Build Commands
```bash
# Build images using Docker Buildx Bake
docker buildx bake

# Build specific targets
docker buildx bake erpnext
docker buildx bake base
docker buildx bake build

# Build with specific versions
FRAPPE_VERSION=v15.0.0 ERPNEXT_VERSION=v15.0.0 docker buildx bake

# Build for custom apps
APPS_JSON_BASE64=$(base64 -w 0 apps.json) docker buildx bake --set "*.args.APPS_JSON_BASE64=$APPS_JSON_BASE64"
```

### Development Commands

#### For VSCode Dev Containers (Recommended)
```bash
# Access dev container from VSCode
# Use Command Palette → "Dev Containers: Reopen in Container"
# Or use Remote-Containers extension

# Inside dev container terminal
cd /workspace/development/frappe-bench
bench --help
bench migrate
bench clear-cache
```

#### Python Environment Activation
**CRITICAL**: When running Python commands inside Docker containers under frappe-bench, you must activate the virtual environment first:

```bash
# Inside Docker container - ALWAYS activate venv before Python commands
source /workspace/development/frappe-bench/env/bin/activate

# Then run Python/bench commands
python -c "import frappe; frappe.init_site('development.localhost')"
bench --site development.localhost console
```

#### For Docker CLI Access (Alternative)
```bash
# Find the running dev container name
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# Access dev container shell (replace container name as needed)
docker exec -it devcontainer-frappe-1 bash
docker exec -it frappe_docker-devcontainer-frappe-1 bash

# Or access with working directory set
docker exec -it -w /workspace/development/frappe-bench devcontainer-frappe-1 bash

# Run specific bench commands without entering container
docker exec -it devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench migrate"
docker exec -it devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench clear-cache"

# Site management commands
docker exec -it devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench drop-site development.localhost --force"
docker exec -it devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench new-site --mariadb-user-host-login-scope=% --db-root-password 123 development.localhost"
docker exec -it devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench --site development.localhost install-app erpnext"
```

#### For Production/PWD Setup
```bash
# Monitor container logs
docker compose -f pwd.yml logs -f create-site
docker compose -f pwd.yml logs -f backend

# Access running containers
docker compose -f pwd.yml exec backend bash
docker compose -f pwd.yml exec frontend bash

# Run bench commands inside container
docker compose -f pwd.yml exec backend bench --help
docker compose -f pwd.yml exec backend bench migrate
docker compose -f pwd.yml exec backend bench clear-cache
```

### Testing and Linting
```bash
# Install and setup pre-commit hooks
pip install pre-commit
pre-commit install

# Run pre-commit on all files
pre-commit run --all-files

# Python testing
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-test.txt
pytest
```

## Environment Configuration

### Key Environment Files
- `example.env`: Template for production environment variables
- `pwd.yml`: Play with Docker configuration for quick testing
- `compose.yaml`: Base compose file for production setups

### Important Environment Variables
- `ERPNEXT_VERSION`: Version of ERPNext to deploy (default: v15.78.1)
- `FRAPPE_VERSION`: Version of Frappe Framework 
- `DB_PASSWORD`: Database password
- `FRAPPE_SITE_NAME_HEADER`: Site routing configuration
- `HTTP_PUBLISH_PORT`: Port for web interface (default: 8080)

## Site Operations

### Creating Sites
Sites are created automatically on first startup via the `create-site` container. Default credentials:
- Username: `Administrator`
- Password: `admin`

### Custom Apps Integration
To add custom Frappe apps, create an `apps.json` file listing the repositories and use it during the build process. Apps are installed in dependency order during container startup.

## Build System Details

### Docker Buildx Bake Configuration
The `docker-bake.hcl` file defines:
- Multi-platform build targets
- Version tagging strategies
- Build arguments for Python/Node versions
- Repository URLs for Frappe components

### GitHub Actions Workflows
- `build_stable.yml`: Builds production images for stable releases  
- `build_develop.yml`: Builds development images from main branches
- `build_bench.yml`: Builds bench development tools
- `lint.yml`: Runs pre-commit hooks on pull requests

## Development Workflow

### VSCode Dev Containers Setup (Recommended)
1. Copy example devcontainer configuration
2. Choose database (MariaDB default, PostgreSQL optional)
3. Open folder in VSCode with Remote-Containers extension
4. Container automatically installs Frappe apps in development mode

**Detailed Steps:**
```bash
# Setup dev container
cp -R devcontainer-example .devcontainer
cp -R development/vscode-example development/.vscode

# Open in VSCode with Remote-Containers extension
code .
# Command Palette → "Dev Containers: Reopen in Container"

# Inside container - create bench
bench init --skip-redis-config-generation frappe-bench
cd frappe-bench

# Configure for containerized services
bench set-config -g db_host mariadb
bench set-config -g redis_cache redis://redis-cache:6379
bench set-config -g redis_queue redis://redis-queue:6379

# Create site and install ERPNext
bench new-site --mariadb-user-host-login-scope=% --db-root-password 123 development.localhost
bench get-app --branch version-15-dev --resolve-deps erpnext https://github.com/karlorz/erpnext
bench --site development.localhost install-app erpnext

# Start development server
bench start
```

### Automated Development Setup
```bash
# Use installer script for quick setup
python development/installer.py

# Custom apps
python development/installer.py --apps-json apps-example.json --site-name mysite.localhost

# Recreate site with demo data (useful for development)
python development/installer.py --recreate-site

# Advanced options
python development/installer.py \
  --apps-json apps-example.json \
  --site-name custom.localhost \
  --admin-password custompass \
  --recreate-site \
  --frappe-branch version-15-dev
```

### Site Management Commands (Docker CLI)
```bash
# Recreate site with demo data using Docker CLI
docker exec -it devcontainer-frappe-1 bash -c "cd /workspace/development && python installer.py --recreate-site"

# Individual bench commands
docker exec -it devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench drop-site development.localhost --force"
docker exec -it devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench new-site --mariadb-user-host-login-scope=% --db-root-password 123 development.localhost"
docker exec -it devcontainer-frappe-1 bash -c "cd /workspace/development/frappe-bench && bench --site development.localhost install-app erpnext"
```

### Manual Container Development
```bash
# Start containers manually
docker-compose -f .devcontainer/docker-compose.yml up -d

# Enter development container
docker exec -e "TERM=xterm-256color" -w /workspace/development -it devcontainer-frappe-1 bash
```

### Debugging Configuration
```bash
# Start services without web process for debugging
honcho start socketio watch schedule worker_short worker_long

# Use VSCode debugger launch configuration: "Start Frappe Web Server"
```

### Local Development Features
- All source code mounted as volumes for live editing
- Bench commands available inside containers
- Debugger support configured via `.vscode` settings
- Hot reloading enabled for development
- Multiple Python/Node versions available via pyenv/nvm

## Bare Metal Installation (Alternative)

### Prerequisites
**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3-dev python3-pip python3-venv git build-essential
sudo apt install -y libssl-dev libffi-dev mariadb-server redis-server nginx
sudo apt install -y nodejs npm wkhtmltopdf
pip3 install frappe-bench
```

**macOS:**
```bash
brew install python3 git node mariadb redis nginx
brew install --cask wkhtmltopdf
pip3 install frappe-bench
```

### Native Installation Process
```bash
# Initialize bench
bench init --frappe-branch version-15-dev frappe-bench
cd frappe-bench

# Create site
bench new-site mysite.local

# Install ERPNext
bench get-app --branch version-15-dev erpnext https://github.com/karlorz/erpnext
bench --site mysite.local install-app erpnext

# Setup production (optional)
sudo bench setup production ubuntu --yes
```

## Production Deployment Patterns

### Single Server Setup
Use `compose.yaml` with environment variables for simple single-server deployments.

### Multi-tenant Setup
Configure multiple sites using environment variables and volume mappings.

### Load Balancing
Frontend container (Nginx) handles SSL termination and load balancing to backend containers.

## Troubleshooting

### Common Issues
- Site creation timing: Wait ~5 minutes for initial site creation
- Memory allocation: Ensure Docker has at least 4GB RAM allocated
- ARM64 builds: Must explicitly set platform for Apple Silicon
- **Demo Data Not Loading**: See `DEMO_DATA_TROUBLESHOOTING.md` for comprehensive guide

### Version Issues
**CRITICAL**: Even branches labeled "version-15" may contain recent breaking changes!
- Development branches get updates from main branches
- Always check actual commit dates: `git log --oneline -1`
- Use tagged releases for stability, not branch names

### Log Access
- Container logs via: `docker compose logs -f <service>`
- Application logs mounted at `/home/frappe/frappe-bench/logs`
- Site-specific logs in mounted volumes

### Known Fixed Issues
1. **Setup Wizard Demo Data (Sept 2025)**: Breaking change in `sanitize_input()` - **FIXED** in karlorz/frappe fork
   - Lines 59, 77, 88 in `/frappe/desk/page/setup_wizard/setup_wizard.py` 
   - Reverted `sanitize_input()` calls to restore demo data functionality
2. **Navigation Differences**: ERPNext Integrations workspace removed in develop-next (intentional)
3. **Site URL Confusion**: Development uses port 8000, not 8080

## File Structure Notes

### Key Files
- `docker-bake.hcl`: Build configuration and targets
- `pwd.yml`: Quick start configuration  
- `compose.yaml`: Production base configuration
- `images/production/Containerfile`: Multi-stage production build
- `docs/`: Comprehensive documentation for various scenarios

### Build Context
The root directory serves as build context, with Dockerfiles referencing relative paths to source installations and configurations.