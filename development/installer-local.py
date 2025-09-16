#!/usr/bin/env python3
"""
Simple setup script for native frappe-bench with container backend services
Usage: cd development && source ../.venv/bin/activate && python installer-local.py
"""
import argparse
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


def check_mysql_client():
    """Check if mysql client is available (system PATH or Homebrew)"""
    # First try to find mysql in system PATH
    try:
        result = subprocess.run(['which', 'mysql'], capture_output=True, text=True)
        if result.returncode == 0:
            mysql_path = result.stdout.strip()
            cprint(f"✓ mysql client found in PATH: {mysql_path}", 2)
            return True
    except:
        pass

    # Fall back to Homebrew locations (macOS)
    homebrew_paths = [
        '/opt/homebrew/opt/mysql-client/bin/mysql',  # Apple Silicon
        '/usr/local/opt/mysql-client/bin/mysql',     # Intel Mac
        '/opt/homebrew/opt/mysql/bin/mysql',         # Full MySQL
        '/usr/local/opt/mysql/bin/mysql'             # Intel MySQL
    ]

    for mysql_binary in homebrew_paths:
        if os.path.exists(mysql_binary):
            cprint(f"✓ mysql client found via Homebrew: {mysql_binary}", 2)
            return True

    # If nothing found, provide platform-appropriate suggestions
    import platform
    system = platform.system()
    if system == "Darwin":  # macOS
        cprint("ERROR: mysql client not found. Try: brew install mysql-client", 1)
    elif system == "Linux":
        cprint("ERROR: mysql client not found. Try: apt install mysql-client or yum install mysql", 1)
    else:
        cprint("ERROR: mysql client not found. Please install MySQL client tools", 1)

    return False


def check_database_service(db_type="mariadb"):
    """Check if database service is available (Docker or local)"""
    if db_type == "mariadb":
        try:
            # Find mysql binary (should be set up by setup_mysql_path)
            mysql_binary = None
            local_bin = os.path.expanduser('~/bin')
            mariadb_script = os.path.join(local_bin, 'mariadb')

            # Use the mariadb wrapper script we created
            if os.path.exists(mariadb_script):
                mysql_binary = mariadb_script
            else:
                # Try to find mysql in PATH
                try:
                    result = subprocess.run(['which', 'mysql'], capture_output=True, text=True)
                    if result.returncode == 0:
                        mysql_binary = result.stdout.strip()
                except:
                    pass

            if not mysql_binary:
                cprint("ERROR: MySQL client not available", 1)
                return False

            env = os.environ.copy()
            env['PATH'] = f"{local_bin}:{env.get('PATH', '')}"

            # Test MariaDB connection
            cmd = [mysql_binary, '--protocol=TCP', '-h', 'localhost', '-P', '3306', '-u', 'root', '-p123', '-e', 'SELECT 1;']
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=5)

            if result.returncode == 0:
                cprint("✓ MariaDB service available", 2)
                return True
            else:
                cprint("ERROR: MariaDB service not available", 1)
                cprint("💡 Ensure MariaDB/MySQL is running on localhost:3306", 3)
                return False
        except subprocess.TimeoutExpired:
            cprint("ERROR: Database connection timeout", 1)
            return False
        except Exception as e:
            cprint(f"ERROR: Could not test MariaDB service: {e}", 1)
            return False
    else:  # postgresql
        try:
            # Test PostgreSQL connection using psql
            result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
            if result.returncode != 0:
                cprint("WARNING: psql not found, skipping PostgreSQL connection test", 3)
                return True  # Don't fail if psql not available

            # Test PostgreSQL connection
            env = os.environ.copy()
            env['PGPASSWORD'] = '123'
            cmd = ['psql', '-h', 'localhost', '-p', '5432', '-U', 'root', '-d', 'postgres', '-c', 'SELECT 1;']
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=5)

            if result.returncode == 0:
                cprint("✓ PostgreSQL service available", 2)
                return True
            else:
                cprint("ERROR: PostgreSQL service not available", 1)
                cprint("💡 Ensure PostgreSQL is running on localhost:5432", 3)
                return False
        except subprocess.TimeoutExpired:
            cprint("ERROR: PostgreSQL connection timeout", 1)
            return False
        except Exception as e:
            cprint(f"ERROR: Could not test PostgreSQL service: {e}", 1)
            return False




def setup_mysql_path():
    """Setup MySQL client path and create TCP wrapper for cross-platform compatibility"""
    import platform

    # Find mysql binary location
    mysql_binary = None
    mysql_dir = None

    # First check system PATH
    try:
        result = subprocess.run(['which', 'mysql'], capture_output=True, text=True)
        if result.returncode == 0:
            mysql_binary = result.stdout.strip()
            mysql_dir = os.path.dirname(mysql_binary)
            cprint(f"✓ Using mysql from PATH: {mysql_binary}", 3)
    except:
        pass

    # Fall back to platform-specific locations
    if not mysql_binary:
        system = platform.system()
        if system == "Darwin":  # macOS
            homebrew_paths = [
                '/opt/homebrew/opt/mysql-client',  # Apple Silicon
                '/usr/local/opt/mysql-client',     # Intel Mac
                '/opt/homebrew/opt/mysql',         # Full MySQL
                '/usr/local/opt/mysql'             # Intel MySQL
            ]
            for path in homebrew_paths:
                mysql_bin = f'{path}/bin/mysql'
                if os.path.exists(mysql_bin):
                    mysql_binary = mysql_bin
                    mysql_dir = f'{path}/bin'
                    # Set up compilation environment for macOS
                    mysql_lib_path = f'{path}/lib'
                    mysql_include_path = f'{path}/include/mysql'
                    if os.path.exists(mysql_lib_path) and os.path.exists(mysql_include_path):
                        os.environ['MYSQLCLIENT_CFLAGS'] = f"-I{mysql_include_path}"
                        os.environ['MYSQLCLIENT_LDFLAGS'] = f"-L{mysql_lib_path} -lmysqlclient"
                        cprint("✓ Set MySQL compilation environment variables", 3)
                    break

    if not mysql_binary:
        cprint("ERROR: Could not locate mysql binary", 1)
        return False

    # Add mysql directory to PATH if needed
    current_path = os.environ.get('PATH', '')
    if mysql_dir and mysql_dir not in current_path:
        os.environ['PATH'] = f"{mysql_dir}:{current_path}"
        cprint(f"✓ Added {mysql_dir} to PATH", 3)

    # Create mariadb TCP wrapper script (cross-platform)
    local_bin = os.path.expanduser('~/bin')
    os.makedirs(local_bin, exist_ok=True)
    mariadb_script = os.path.join(local_bin, 'mariadb')

    wrapper_content = f"""#!/bin/bash
# Wrapper for mariadb to force TCP connection instead of socket
exec {mysql_binary} --protocol=TCP "$@"
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

    return True


def init_bench_if_not_exist(args):
    """Initialize bench if it doesn't exist"""
    if os.path.exists(args.bench_name):
        cprint("Bench already exists. Only site will be created", level=3)
        return True
    
    try:
        cprint(f"Creating new bench '{args.bench_name}'...", 2)
        env = os.environ.copy()
        
        # Fix git safe directory issues for apps
        cprint("Configuring git safe directories...", level=3)
        git_safe_dirs = [
            f"/workspace/development/{args.bench_name}/apps/erpnext",
            f"/workspace/development/{args.bench_name}/apps/frappe",
        ]
        for safe_dir in git_safe_dirs:
            try:
                subprocess.call(
                    ["git", "config", "--global", "--add", "safe.directory", safe_dir],
                    cwd=os.getcwd(),
                )
            except subprocess.CalledProcessError:
                pass  # Continue if git config fails
        
        # Initialize bench (skip apps.json to avoid wrong branch)
        init_command = "bench init --skip-redis-config-generation "
        init_command += f"--frappe-path={args.frappe_repo} "
        init_command += f"--frappe-branch={args.frappe_branch} "
        # Skip apps.json to manually install ERPNext with correct branch
        init_command += args.bench_name

        cprint(f"Running: {init_command}", 3)
        command = ["/bin/bash", "-c", init_command]
        # Show live output during bench initialization
        result = subprocess.run(command, env=env, cwd=os.getcwd())

        if result.returncode != 0:
            cprint("Error initializing bench", 1)
            return False
        
        cprint("✓ Bench initialized successfully", 2)
        return True
        
    except Exception as e:
        cprint(f"Error initializing bench: {e}", 1)
        return False


def configure_bench(args=None):
    """Configure existing bench for container backend"""
    bench_name = args.bench_name if args else 'frappe-bench'
    db_type = args.db_type if args else 'mariadb'

    if not os.path.exists(bench_name):
        cprint(f"ERROR: {bench_name} directory not found", 1)
        return False

    cprint("Configuring frappe-bench for database backend...", 3)

    bench_dir = bench_name
    if db_type == "mariadb":
        config_commands = [
            ['bench', 'set-config', '-g', 'db_host', 'localhost'],
            ['bench', 'set-config', '-g', 'db_port', '3306'],
            ['bench', 'set-config', '-g', 'db_socket', ''],
            ['bench', 'set-config', '-g', 'db_type', 'mariadb'],
            ['bench', 'set-config', '-g', 'redis_cache', 'redis://localhost:6379'],
            ['bench', 'set-config', '-g', 'redis_queue', 'redis://localhost:6380'],
            ['bench', 'set-config', '-g', 'redis_socketio', 'redis://localhost:6380'],
            ['bench', 'set-config', '-g', 'developer_mode', '1'],
        ]
    else:  # postgresql
        config_commands = [
            ['bench', 'set-config', '-g', 'db_host', 'localhost'],
            ['bench', 'set-config', '-g', 'db_port', '5432'],
            ['bench', 'set-config', '-g', 'db_type', 'postgres'],
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
    site_config_path = f'{bench_name}/sites/development.localhost/site_config.json'
    if os.path.exists(site_config_path):
        cprint("Fixing site-specific database configuration...", 3)
        try:
            import json
            with open(site_config_path, 'r') as f:
                site_config = json.load(f)

            # Fix both mariadb container and localhost socket issues
            if site_config.get('db_host') in ['mariadb', 'localhost']:
                site_config['db_host'] = '127.0.0.1'
                site_config['db_port'] = 3306
                site_config['db_socket'] = ''
                with open(site_config_path, 'w') as f:
                    json.dump(site_config, f, indent=1)
                cprint("✓ Updated site config db_host to 127.0.0.1", 3)
        except Exception as e:
            cprint(f"Warning: Could not update site config: {e}", 3)
    
    return True


def check_apps(args=None):
    """Check what apps are installed"""
    bench_name = args.bench_name if args else 'frappe-bench'
    if not os.path.exists(f'{bench_name}/apps'):
        return []
    
    apps = []
    for item in os.listdir(f'{bench_name}/apps'):
        if os.path.isdir(f'{bench_name}/apps/{item}'):
            apps.append(item)
    
    cprint(f"Apps found: {', '.join(apps)}", 3)
    return apps


def install_erpnext_if_missing(args=None):
    """Install ERPNext if not present"""
    bench_name = args.bench_name if args else 'frappe-bench'
    apps = check_apps(args)

    if 'erpnext' not in apps:
        cprint("Installing ERPNext...", 3)
        try:
            cmd = ['bench', 'get-app', '--branch', 'develop-next', 'erpnext', 'https://github.com/karlorz/erpnext']
            cprint(f"Running: {' '.join(cmd)}", 3)
            # Show live output during installation
            result = subprocess.run(cmd, cwd=bench_name)
            if result.returncode == 0:
                cprint("✓ ERPNext installed successfully", 2)
                return True
            else:
                cprint("Error installing ERPNext", 1)
                return False
        except Exception as e:
            cprint(f"Error installing ERPNext: {e}", 1)
            return False
    else:
        cprint("✓ ERPNext already installed", 2)
        return True


def create_site_config_manually(bench_name, site_name, db_type="mariadb"):
    """Create site config manually to ensure TCP connection"""
    sites_dir = f"{bench_name}/sites"
    site_dir = f"{sites_dir}/{site_name}"

    os.makedirs(site_dir, exist_ok=True)

    if db_type == "mariadb":
        site_config = {
            "db_host": "127.0.0.1",
            "db_port": 3306,
            "db_socket": "",
            "db_type": "mariadb",
            "db_name": f"_{site_name.replace('.', '_').replace('-', '_')}"
        }
    else:  # postgresql
        site_config = {
            "db_host": "127.0.0.1",
            "db_port": 5432,
            "db_type": "postgres",
            "db_name": f"_{site_name.replace('.', '_').replace('-', '_')}"
        }

    config_path = f"{site_dir}/site_config.json"
    try:
        import json
        with open(config_path, 'w') as f:
            json.dump(site_config, f, indent=1)
        cprint(f"✓ Created site config for TCP connection: {config_path}", 3)
        return True
    except Exception as e:
        cprint(f"Warning: Could not create site config: {e}", 3)
        return False


def create_site(args=None, recreate=False):
    """Create or recreate the development site"""
    bench_name = args.bench_name if args else 'frappe-bench'
    site_name = args.site_name if args else "development.localhost"
    admin_password = args.admin_password if args else "admin"
    db_type = args.db_type if args else "mariadb"

    # Check if site exists
    site_path = f"{bench_name}/sites/{site_name}"
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
            subprocess.run(cmd, cwd=bench_name, env=env, check=False)  # Don't fail if drop fails
        except:
            pass

    # Let bench create the site first, then fix config afterward
    
    # Create new site
    cprint(f"Creating site {site_name}...", 3)
    try:
        env = os.environ.copy()
        env['PATH'] = f"{os.path.expanduser('~/bin')}:/opt/homebrew/opt/mysql-client/bin:{env.get('PATH', '')}"
        
        if db_type == "mariadb":
            cmd = [
                'bench', 'new-site',
                '--db-root-username=root',
                '--db-host=127.0.0.1',
                '--db-port=3306',
                f'--db-type={db_type}',
                '--mariadb-user-host-login-scope=%',
                '--db-root-password=123',
                f'--admin-password={admin_password}',
                '--force',
                site_name
            ]
        else:  # postgresql
            cmd = [
                'bench', 'new-site',
                '--db-root-username=root',
                '--db-host=127.0.0.1',
                '--db-port=5432',
                f'--db-type={db_type}',
                '--db-root-password=123',
                f'--admin-password={admin_password}',
                '--force',
                site_name
            ]

        cprint(f"Running: {' '.join(cmd)}", 3)
        # Show live output during site creation
        result = subprocess.run(cmd, cwd=bench_name, env=env)
        if result.returncode == 0:
            cprint(f"✓ Site {site_name} created successfully!", 2)

            # Install ERPNext separately
            cprint("Installing ERPNext app to site...", 3)
            cmd = ['bench', '--site', site_name, 'install-app', 'erpnext']
            cprint(f"Running: {' '.join(cmd)}", 3)
            # Show live output during app installation
            result = subprocess.run(cmd, cwd=bench_name, env=env)
            if result.returncode == 0:
                cprint("✓ ERPNext installed successfully!", 2)
                cprint("✓ Login: Administrator / admin", 2)
                return True
            else:
                cprint("Warning: ERPNext installation failed", 3)
                cprint("✓ Login: Administrator / admin (Frappe only)", 2)
                return True
        else:
            cprint("Error creating site", 1)
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


def get_args_parser():
    """Get argument parser with all options from original installer.py"""
    parser = argparse.ArgumentParser(description="Setup native Frappe development environment")
    parser.add_argument(
        "-j",
        "--apps-json",
        action="store",
        type=str,
        help="Path to apps.json, default: apps-example.json",
        default="apps-example.json",
    )
    parser.add_argument(
        "-b",
        "--bench-name",
        action="store",
        type=str,
        help="Bench directory name, default: frappe-bench",
        default="frappe-bench",
    )
    parser.add_argument(
        "-s",
        "--site-name",
        action="store",
        type=str,
        help="Site name, should end with .localhost, default: development.localhost",
        default="development.localhost",
    )
    parser.add_argument(
        "-r",
        "--frappe-repo",
        action="store",
        type=str,
        help="frappe repo to use, default: https://github.com/karlorz/frappe",
        default="https://github.com/karlorz/frappe",
    )
    parser.add_argument(
        "-t",
        "--frappe-branch",
        action="store",
        type=str,
        help="frappe repo to use, default: develop-next",
        default="develop-next",
    )
    parser.add_argument(
        "-a",
        "--admin-password",
        action="store",
        type=str,
        help="admin password for site, default: admin",
        default="admin",
    )
    parser.add_argument(
        "-d",
        "--db-type",
        action="store",
        type=str,
        help="Database type to use (e.g., mariadb or postgres)",
        default="mariadb",
    )
    parser.add_argument(
        "--recreate-site",
        action="store_true",
        help="Drop existing site and recreate it",
    )
    return parser


def main():
    """Main setup function"""
    parser = get_args_parser()
    args = parser.parse_args()

    cprint("=== Native Frappe Development Setup ===", 2)

    # Check prerequisites
    if not check_uv_environment():
        sys.exit(1)

    # MySQL client tools only needed for MariaDB
    if args.db_type == "mariadb":
        if not check_mysql_client():
            sys.exit(1)

        if not setup_mysql_path():
            sys.exit(1)

        if not check_database_service(args.db_type):
            sys.exit(1)
    else:
        cprint(f"Using {args.db_type} database - skipping MySQL client setup", 3)
    
    # Initialize bench if it doesn't exist
    if not init_bench_if_not_exist(args):
        sys.exit(1)
    
    # Configure bench
    if not configure_bench(args):
        sys.exit(1)
    
    # Install ERPNext if missing
    if not install_erpnext_if_missing(args):
        cprint("Failed to install ERPNext, continuing anyway...", 3)
    
    # Create site
    if create_site(args, recreate=args.recreate_site):
        show_usage()
    else:
        cprint("Site creation failed. Check container services are running.", 1)
        sys.exit(1)


if __name__ == "__main__":
    main()