#!/bin/bash
set -e

echo "=========================================="
echo "🚀 UPDATING HEARTMATE ON PYTHONANYWHERE"
echo "=========================================="

# 1. Update remote URL to your new GitHub repository
echo "[1/5] Updating git remote to https://github.com/sonamolcm/heartmate.git..."
git remote set-url origin https://github.com/sonamolcm/heartmate.git

# 2. Fetch and pull latest code from main branch
echo "[2/5] Pulling latest code from main branch..."
git fetch origin main
git checkout main
git pull origin main

# 3. Install/update python packages
echo "[3/5] Installing dependencies..."
pip install -r requirements.txt

# 4. Apply database migrations
echo "[4/5] Running migrations..."
python manage.py migrate

# 5. Collect static files
echo "[5/5] Collecting static files..."
python manage.py collectstatic --noinput

# 6. Touch WSGI to trigger auto-reload
touch /var/www/*_wsgi.py 2>/dev/null || true

echo "=========================================="
echo "✅ DEPLOYMENT SUCCEEDED!"
echo "Visit your Web tab and click 'Reload' if needed."
echo "=========================================="
