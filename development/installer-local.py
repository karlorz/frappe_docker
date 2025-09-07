#!/usr/bin/env python3
"""
Simple setup script for native frappe-bench with container backend services
Usage: cd development && source ../.venv/bin/activate && python installer-local.py
"""
import os
import subprocess
import sys


def cprint(message, level=1):
    """Print colored messages"""
    colors = {1: "\033[31m", 2: "\33[92m", 3: "\33[93m"}  # red, green, yellow
    reset = "\033[0m"
    color = colors.get(level, colors[1])
    print(f"{color} {message} {reset}")


def check_uv_environment():
    """Check if we're in the correct uv environment"""
    if not os.environ.get('VIRTUAL_ENV'):
        cprint("ERROR: Not in virtual environment. Run: source ../.venv/bin/activate", 1)
        return False
    
    venv_path = os.environ.get('VIRTUAL_ENV')
    if 'frappe_docker/.venv' not in venv_path:
        cprint(f"WARNING: Unexpected venv path: {venv_path}", 3)
    
    try:
        result = subprocess.run(['which', 'bench'], capture_output=True, text=True)
        if result.returncode == 0:
            cprint("✓ frappe-bench available", 2)
            return True
        else:
            cprint("ERROR: bench not found. Run: uv add frappe-bench", 1)
            return False
    except:
        cprint("ERROR: Could not check bench availability", 1)
        return False


def setup_mysql_path():
    """Add MySQL client to PATH and create mariadb TCP wrapper"""
    mysql_path = '/opt/homebrew/opt/mysql-client/bin'
    current_path = os.environ.get('PATH', '')
    
    if mysql_path not in current_path:
        os.environ['PATH'] = f"{mysql_path}:{current_path}"
        cprint("✓ Added mysql-client to PATH", 3)
    
    # Test mysql availability
    try:
        subprocess.run(['which', 'mysql'], capture_output=True, check=True)
        cprint("✓ mysql client available", 2)
    except:
        cprint("WARNING: mysql client not found", 3)
        return False
    
    # Create mariadb TCP wrapper script if it doesn't exist
    local_bin = os.path.expanduser('~/bin')
    os.makedirs(local_bin, exist_ok=True)
    mariadb_script = os.path.join(local_bin, 'mariadb')
    
    # Always recreate the wrapper to ensure it has correct content
    wrapper_content = f"""#!/bin/bash
# Wrapper for mariadb to force TCP connection instead of socket
exec {mysql_path}/mysql --protocol=TCP "$@"
"""
    
    try:
        with open(mariadb_script, 'w') as f:
            f.write(wrapper_content)
        os.chmod(mariadb_script, 0o755)
        cprint("✓ Created mariadb TCP wrapper", 3)
    except Exception as e:
        cprint(f"Warning: Could not create mariadb wrapper: {e}", 3)
    
    # Add ~/bin to PATH
    if local_bin not in os.environ.get('PATH', ''):
        os.environ['PATH'] = f"{local_bin}:{os.environ.get('PATH', '')}"
        cprint("✓ Added ~/bin to PATH", 3)
    
    # Test mariadb wrapper
    try:
        result = subprocess.run([mariadb_script, '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            cprint("✓ mariadb TCP wrapper working", 2)
        else:
            cprint("WARNING: mariadb wrapper test failed", 3)
    except:
        cprint("WARNING: mariadb wrapper test failed", 3)
    
    return True


def configure_bench():
    """Configure existing bench for container backend"""
    if not os.path.exists('frappe-bench'):
        cprint("ERROR: frappe-bench directory not found", 1)
        return False
    
    cprint("Configuring frappe-bench for container backend...", 3)
    
    bench_dir = 'frappe-bench'
    config_commands = [
        ['bench', 'set-config', '-g', 'db_host', 'localhost'],
        ['bench', 'set-config', '-g', 'db_port', '3306'],
        ['bench', 'set-config', '-g', 'db_socket', ''],
        ['bench', 'set-config', '-g', 'redis_cache', 'redis://localhost:6379'],
        ['bench', 'set-config', '-g', 'redis_queue', 'redis://localhost:6380'],
        ['bench', 'set-config', '-g', 'redis_socketio', 'redis://localhost:6380'],
        ['bench', 'set-config', '-g', 'developer_mode', '1'],
    ]
    
    for cmd in config_commands:
        try:
            result = subprocess.run(cmd, cwd=bench_dir, capture_output=True, text=True)
            if result.returncode == 0:
                cprint(f"✓ {' '.join(cmd[2:])}", 3)
            else:
                cprint(f"Warning: {' '.join(cmd)} failed: {result.stderr.strip()}", 3)
        except Exception as e:
            cprint(f"Error running {' '.join(cmd)}: {e}", 1)
    
    # Also fix site-specific config if development.localhost exists
    site_config_path = 'frappe-bench/sites/development.localhost/site_config.json'
    if os.path.exists(site_config_path):
        cprint("Fixing site-specific database configuration...", 3)
        try:
            import json
            with open(site_config_path, 'r') as f:
                site_config = json.load(f)
            
            if site_config.get('db_host') == 'mariadb':
                site_config['db_host'] = 'localhost'
                with open(site_config_path, 'w') as f:
                    json.dump(site_config, f, indent=1)
                cprint("✓ Updated site config db_host to localhost", 3)
        except Exception as e:
            cprint(f"Warning: Could not update site config: {e}", 3)
    
    return True


def check_apps():
    """Check what apps are installed"""
    if not os.path.exists('frappe-bench/apps'):
        return []
    
    apps = []
    for item in os.listdir('frappe-bench/apps'):
        if os.path.isdir(f'frappe-bench/apps/{item}'):
            apps.append(item)
    
    cprint(f"Apps found: {', '.join(apps)}", 3)
    return apps


def install_erpnext_if_missing():
    """Install ERPNext if not present"""
    apps = check_apps()
    
    if 'erpnext' not in apps:
        cprint("Installing ERPNext...", 3)
        try:
            cmd = ['bench', 'get-app', '--branch', 'version-15-dev', 'erpnext', 'https://github.com/karlorz/erpnext']
            result = subprocess.run(cmd, cwd='frappe-bench', capture_output=True, text=True)
            if result.returncode == 0:
                cprint("✓ ERPNext installed successfully", 2)
                return True
            else:
                cprint(f"Error installing ERPNext: {result.stderr}", 1)
                return False
        except Exception as e:
            cprint(f"Error installing ERPNext: {e}", 1)
            return False
    else:
        cprint("✓ ERPNext already installed", 2)
        return True


def create_site(recreate=False):
    """Create or recreate the development site"""
    site_name = "development.localhost"
    
    # Check if site exists
    site_path = f"frappe-bench/sites/{site_name}"
    if os.path.exists(site_path):
        if not recreate:
            cprint(f"✓ Site {site_name} already exists", 2)
            cprint("✓ Login: Administrator / admin", 2)
            return True
        else:
            cprint(f"Site {site_name} exists, recreating...", 3)
        
        # Drop existing site
        cprint(f"Dropping existing site {site_name}...", 3)
        try:
            env = os.environ.copy()
            env['PATH'] = f"{os.path.expanduser('~/bin')}:/opt/homebrew/opt/mysql-client/bin:{env.get('PATH', '')}"
            cmd = ['bench', 'drop-site', site_name, '--force', '--db-root-password=123']
            subprocess.run(cmd, cwd='frappe-bench', env=env, check=False)  # Don't fail if drop fails
        except:
            pass
    
    # Create new site
    cprint(f"Creating site {site_name}...", 3)
    try:
        env = os.environ.copy()
        env['PATH'] = f"{os.path.expanduser('~/bin')}:/opt/homebrew/opt/mysql-client/bin:{env.get('PATH', '')}"
        
        cmd = [
            'bench', 'new-site', 
            '--mariadb-user-host-login-scope=%',
            '--db-root-password=123',
            '--admin-password=admin',
            site_name
        ]
        
        result = subprocess.run(cmd, cwd='frappe-bench', env=env, capture_output=True, text=True)
        if result.returncode == 0:
            cprint(f"✓ Site {site_name} created successfully!", 2)
            
            # Install ERPNext separately 
            cprint("Installing ERPNext...", 3)
            cmd = ['bench', '--site', site_name, 'install-app', 'erpnext']
            result = subprocess.run(cmd, cwd='frappe-bench', env=env, capture_output=True, text=True)
            if result.returncode == 0:
                cprint("✓ ERPNext installed successfully!", 2)
                cprint("✓ Login: Administrator / admin", 2)
                return True
            else:
                cprint(f"Warning: ERPNext installation failed: {result.stderr}", 3)
                cprint("✓ Login: Administrator / admin (Frappe only)", 2)
                return True
        else:
            cprint(f"Error creating site: {result.stderr}", 1)
            return False
    except Exception as e:
        cprint(f"Error creating site: {e}", 1)
        return False


def show_usage():
    """Show usage instructions"""
    cprint("Setup complete! Usage instructions:", 2)
    cprint("", 2)
    cprint("1. Start web server:", 3)
    cprint("   cd frappe-bench && source env/bin/activate && bench --site development.localhost serve --port 8000", 3)
    cprint("", 2)
    cprint("2. Access your site:", 3)
    cprint("   http://localhost:8000", 3)
    cprint("   Login: Administrator / admin", 3)
    cprint("", 2)
    cprint("3. Background workers (optional, for demo data):", 3)
    cprint("   cd frappe-bench && source env/bin/activate && bench --site development.localhost worker", 3)


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup native Frappe development environment")
    parser.add_argument("--recreate-site", action="store_true", help="Drop and recreate the site")
    args = parser.parse_args()
    
    cprint("=== Native Frappe Development Setup ===", 2)
    
    # Check environment
    if not check_uv_environment():
        sys.exit(1)
    
    setup_mysql_path()
    
    # Configure bench
    if not configure_bench():
        sys.exit(1)
    
    # Install ERPNext if missing
    if not install_erpnext_if_missing():
        cprint("Failed to install ERPNext, continuing anyway...", 3)
    
    # Create site
    if create_site(recreate=args.recreate_site):
        show_usage()
    else:
        cprint("Site creation failed. Check container services are running.", 1)
        sys.exit(1)


if __name__ == "__main__":
    main()