# Web Application Deployment Guide

## Overview

This application has been successfully converted from an Electron desktop app to a web-based application. The frontend now runs in any modern browser, while the Python backend continues to serve APIs and static files.

---

## Architecture

### Before (Electron):
```
┌─────────────────────────────────────┐
│  Electron Wrapper (main.js)         │
│  ├─ Window Management                │
│  ├─ IPC Communication                │
│  ├─ Backend Launcher (Python)       │
│  └─ OS Integration (WhatsApp, etc)  │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Frontend (HTML/CSS/JS)              │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Backend (Flask Python API)          │
└─────────────────────────────────────┘
```

### After (Web):
```
┌─────────────────────────────────────┐
│  Browser (Chrome, Firefox, etc)     │
│  └─ Frontend (HTML/CSS/JS)           │
└─────────────────────────────────────┘
         ↓ HTTP
┌─────────────────────────────────────┐
│  Backend (Flask Python API)          │
│  ├─ Serves Static Files              │
│  ├─ REST API Endpoints               │
│  └─ Automated Backup Service         │
└─────────────────────────────────────┘
```

---

## Changes Made

### 1. **Removed Electron Components**
- ❌ `desktop/main.js` - No longer needed
- ❌ `desktop/package.json` - Electron config removed
- ❌ `desktop/backup.js` - Replaced with Python scheduler
- ❌ `desktop/splash.html` - Removed (direct login)

### 2. **Frontend Updates**

#### `login.html`:
- ✅ Removed `require('electron')`
- ✅ Changed `ipcRenderer.send('login-success')` → `window.location.href = '/app'`
- ✅ Changed API URL from `http://localhost:5000/api/login` → `/api/login` (relative)

#### `app.html`:
- ✅ Removed `require('electron')`
- ✅ Changed `ipcRenderer.send('logout')` → `window.location.href = '/'`
- ✅ Replaced Electron print dialog with browser-native print preview window
- ✅ WhatsApp sharing now uses WhatsApp Web API (browser-compatible)
- ✅ Changed CSS reference from `http://localhost:5000/static/css/style.css` → `/static/css/style.css`

### 3. **Backend Updates**

#### `backend/app.py`:
- ✅ Added route: `@app.route('/')` → serves `login.html`
- ✅ Added route: `@app.route('/app')` → serves `app.html`
- ✅ Added route: `@app.route('/assets/<path:filename>')` → serves static assets
- ✅ Integrated automated backup service on startup

#### `backend/scheduled_backup.py` (NEW):
- ✅ Runs automatic MySQL backups every 24 hours
- ✅ Saves backups to `~/Documents/smart_purchase_slip_backup/`
- ✅ Optional Google Drive upload (requires OAuth tokens)
- ✅ Runs as background daemon thread

### 4. **Feature Parity**

| Feature | Electron | Web | Status |
|---------|----------|-----|--------|
| Login/Logout | ✅ | ✅ | **Identical** |
| Dashboard | ✅ | ✅ | **Identical** |
| Create Slips | ✅ | ✅ | **Identical** |
| View/Edit/Delete | ✅ | ✅ | **Identical** |
| Print (PDF) | ✅ | ✅ | **Browser native** |
| WhatsApp Share | ✅ | ✅ | **WhatsApp Web** |
| Auto Backup | ✅ | ✅ | **Server-side** |
| User Management | ✅ | ✅ | **Identical** |

---

## Installation & Setup

### Prerequisites

1. **Python 3.8+** installed
2. **MySQL Server** running and accessible
3. **Python packages** from `requirements.txt`

### Step 1: Install Dependencies

```bash
cd /path/to/project
pip install -r requirements.txt
```

### Step 2: Configure Database

Edit `config.json`:
```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "purchase_slips_db"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

### Step 3: Run Database Migrations

```bash
# Ensure your database exists and is accessible
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS purchase_slips_db;"

# Run migrations if needed
python backend/database.py
```

### Step 4: Start the Backend

```bash
cd /path/to/project
python backend/app.py
```

You should see:
```
============================================================
RICE MILL PURCHASE SLIP MANAGER
============================================================

[OK] Server starting...
[INFO] Backend running on: http://127.0.0.1:5000
[INFO] Starting automated backup service...
[OK] Automated backup service started

 * Running on http://127.0.0.1:5000
```

### Step 5: Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

You'll see the login page. Use your existing credentials to log in.

---

## Running on LAN (Network Access)

To allow other devices on your network to access the app:

1. Update `config.json`:
```json
{
  "server": {
    "host": "0.0.0.0",  // Listen on all interfaces
    "port": 5000
  }
}
```

2. Find your server's IP address:
```bash
# Windows
ipconfig

# Linux/Mac
ifconfig
```

3. Access from other devices:
```
http://<your-server-ip>:5000
```

Example: `http://192.168.1.100:5000`

---

## Automated Backup Service

### How It Works

The backup service runs automatically in the background when the backend starts:

- **Frequency**: Every 24 hours
- **Location**: `~/Documents/smart_purchase_slip_backup/`
- **Format**: `purchase_slips_backup_YYYY-MM-DD_HH-MM-SS.sql`
- **Method**: MySQL `mysqldump` command

### Google Drive Integration (Optional)

To enable Google Drive uploads:

1. Ensure `tokens.json` exists in the `desktop/` folder with valid OAuth credentials
2. Install Google API libraries:
```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

3. The backup service will automatically upload to Drive after creating local backups

**Note**: If Google Drive is not configured, backups will still be saved locally.

### Manual Backup

To run a backup manually:
```bash
python backend/scheduled_backup.py
```

---

## Production Deployment

### Using Gunicorn (Recommended)

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### Using systemd (Linux)

Create `/etc/systemd/system/purchase-slips.service`:

```ini
[Unit]
Description=Purchase Slips Manager
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/project
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable purchase-slips
sudo systemctl start purchase-slips
```

### Using Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Browser Compatibility

### Tested Browsers:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Edge 90+
- ✅ Safari 14+

### Required Features:
- JavaScript ES6+ support
- LocalStorage API
- Fetch API
- CSS Grid & Flexbox

---

## Troubleshooting

### Issue: "Cannot connect to backend"

**Solution**: Ensure the Python backend is running:
```bash
python backend/app.py
```

### Issue: "Database connection failed"

**Solution**: Check your `config.json` and MySQL service:
```bash
# Test MySQL connection
mysql -h localhost -u root -p -e "SHOW DATABASES;"
```

### Issue: "Backup not working"

**Solution**: Ensure `mysqldump` is in your PATH:
```bash
# Test mysqldump
mysqldump --version
```

### Issue: "Print not working"

**Solution**:
1. Ensure pop-ups are allowed in your browser
2. Check browser console for errors (F12)
3. Try Ctrl+P after the print window opens

### Issue: "WhatsApp share not working"

**Solution**:
1. Ensure mobile number is saved in the slip
2. WhatsApp Web must be accessible
3. Mobile number format: `+91XXXXXXXXXX` or `XXXXXXXXXX`

---

## Security Considerations

### 1. **Change Default Credentials**
- Update default database passwords
- Change admin login credentials

### 2. **Enable HTTPS**
- Use Nginx with SSL certificate (Let's Encrypt)
- Force HTTPS redirects

### 3. **Firewall Rules**
```bash
# Allow only specific IPs (example)
sudo ufw allow from 192.168.1.0/24 to any port 5000
```

### 4. **Backup Security**
- Protect backup directory permissions:
```bash
chmod 700 ~/Documents/smart_purchase_slip_backup/
```

---

## Folder Structure (After Conversion)

```
project/
├── backend/
│   ├── __init__.py
│   ├── app.py                  # Main Flask app
│   ├── database.py             # Database connection
│   ├── scheduled_backup.py     # NEW: Automated backups
│   ├── routes/
│   │   ├── auth.py             # Authentication API
│   │   └── slips.py            # Slips CRUD API
│   └── templates/
│       └── print_template_new.html
├── desktop/                     # Frontend files
│   ├── login.html              # UPDATED: No Electron
│   ├── app.html                # UPDATED: No Electron
│   ├── assets/
│   │   └── spslogo.png
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── script.js
├── config.json                  # Configuration
├── requirements.txt             # Python dependencies
└── WEB_DEPLOYMENT_GUIDE.md     # This file
```

---

## Migration Checklist

- [x] Remove Electron dependencies
- [x] Update frontend navigation (IPC → window.location)
- [x] Implement browser-native printing
- [x] Add WhatsApp Web integration
- [x] Create server-side backup scheduler
- [x] Update backend routes for static file serving
- [x] Test all features in browser
- [x] Create deployment documentation

---

## Support

For issues or questions:
1. Check backend logs: `backend/app.py` console output
2. Check browser console: F12 → Console tab
3. Check backup logs: Output from `scheduled_backup.py`

---

## Summary

The application is now fully web-based and ready for deployment. All Electron-specific code has been removed, and the user experience remains identical. The backend automatically handles backups, and the frontend works seamlessly in any modern browser.

**No desktop wrapper needed. Just run the Python backend and access via browser!**
