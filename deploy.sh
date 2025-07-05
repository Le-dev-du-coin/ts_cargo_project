#!/bin/bash

# --- Configuration Variables (USER MUST EDIT THESE) ---
# Your Django project name (e.g., ts_cargo)
PROJECT_NAME="ts_cargo"
# Your Git repository URL (e.g., https://github.com/youruser/ts_cargo.git)
GIT_REPO_URL="YOUR_GIT_REPOSITORY_URL"
# Where your project will be cloned on the server
PROJECT_DIR="/var/www/$PROJECT_NAME"
# Your specific Python version, e.g., python3.12
PYTHON_VERSION="python3.12"
# Your domain name, e.g., example.com
DOMAIN_NAME="your_domain.com"
# Your Django settings module (e.g., ts_cargo.settings)
DJANGO_SETTINGS_MODULE="$PROJECT_NAME.settings"
# Port Gunicorn will listen on
GUNICORN_PORT="8000"

# PostgreSQL database name and user (will be same as PROJECT_NAME)
DB_NAME="$PROJECT_NAME"
DB_USER="$PROJECT_NAME"
# IMPORTANT: Set a strong password for your PostgreSQL user
DB_PASSWORD="YOUR_DB_PASSWORD"

# --- System Update and Basic Dependencies ---
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo "Installing Python and essential packages..."
sudo apt install -y $PYTHON_VERSION $PYTHON_VERSION-venv python3-pip nginx curl git postgresql postgresql-contrib libpq-dev

# --- PostgreSQL Setup ---
echo "Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "Installing psycopg2-binary for PostgreSQL connection..."
source venv/bin/activate
pip install psycopg2-binary
deactivate

# --- Create Project Directory and Clone Repository ---
echo "Creating project directory: $PROJECT_DIR"
sudo mkdir -p $PROJECT_DIR
# Give ownership to current user for setup
sudo chown $USER:$USER $PROJECT_DIR
cd $PROJECT_DIR

echo "Cloning Git repository..."
# Clones into the current directory
git clone $GIT_REPO_URL .

# --- Set up Python Virtual Environment ---
echo "Setting up Python virtual environment..."
$PYTHON_VERSION -m venv venv
source venv/bin/activate

echo "Installing Python dependencies from requirements.txt..."
# Assuming requirements.txt is at the root of your cloned repo
pip install -r requirements.txt gunicorn

# --- Django Configuration (USER MUST PERFORM MANUALLY AFTER SCRIPT RUNS) ---
echo ""
echo "--- IMPORTANT: MANUAL DJANGO CONFIGURATION REQUIRED ---"
echo "1. Edit your Django settings file: $PROJECT_DIR/$PROJECT_NAME/settings.py"
echo "   - Set DEBUG = False"
echo "   - Update ALLOWED_HOSTS = ['$DOMAIN_NAME', 'your_server_ip']"
echo "   - Configure your production database settings (e.g., PostgreSQL, MySQL)"
echo "     Example for PostgreSQL:"
echo "     DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql_psycopg2', 'NAME': '$DB_NAME', 'USER': '$DB_USER', 'PASSWORD': '$DB_PASSWORD', 'HOST': 'localhost', 'PORT': ''}}"
echo "   - Set a strong SECRET_KEY"
echo "   - Add SITE_URL = 'http://$DOMAIN_NAME' (or https if you set up SSL)"
echo ""
echo "2. Run Django migrations and collect static files:"
echo "   cd $PROJECT_DIR"
echo "   source venv/bin/activate"
echo "   python manage.py makemigrations"
echo "   python manage.py migrate"
echo "   python manage.py collectstatic --noinput"
echo "   deactivate"
echo ""

# --- Gunicorn Configuration ---
echo "Creating Gunicorn service file..."
GUNICORN_SERVICE_FILE="/etc/systemd/system/gunicorn_$PROJECT_NAME.service"
sudo bash -c "cat > $GUNICORN_SERVICE_FILE" <<EOF
[Unit]
Description=Gunicorn instance to serve $PROJECT_NAME
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind unix:$PROJECT_DIR/$PROJECT_NAME.sock $PROJECT_NAME.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling and starting Gunicorn service..."
sudo systemctl daemon-reload
sudo systemctl enable gunicorn_$PROJECT_NAME
sudo systemctl start gunicorn_$PROJECT_NAME
sudo systemctl status gunicorn_$PROJECT_NAME --no-pager

# --- Nginx Configuration ---
echo "Creating Nginx server block..."
NGINX_CONF_FILE="/etc/nginx/sites-available/$PROJECT_NAME"
sudo bash -c "cat > $NGINX_CONF_FILE" <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $PROJECT_DIR;
    }
    location /media/ {
        root $PROJECT_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/$PROJECT_NAME.sock;
    }
}
EOF

echo "Enabling Nginx server block and restarting Nginx..."
sudo ln -sf $NGINX_CONF_FILE /etc/nginx/sites-enabled/
sudo nginx -t # Test Nginx configuration
sudo systemctl restart nginx
sudo systemctl status nginx --no-pager

# --- Cron Job Setup (for send_whatsapp_notifications) ---
echo ""
echo "--- CRON JOB SETUP ---"
echo "To set up the cron job for WhatsApp notifications, run the following command:"
echo "crontab -e"
echo "Then add a line like this (e.g., to run every 5 minutes):"
echo "*/5 * * * * /usr/bin/$PYTHON_VERSION $PROJECT_DIR/manage.py send_whatsapp_notifications >> $PROJECT_DIR/cron.log 2>&1"
echo "Remember to replace $PYTHON_VERSION with your actual Python executable path if different."
echo ""

echo "Deployment script finished. Please complete the manual Django configuration steps."
echo "Visit your domain: http://$DOMAIN_NAME"