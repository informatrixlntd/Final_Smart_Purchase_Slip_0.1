# Quick Start Guide - Web Application

## Start the Application (3 Steps)

### Step 1: Install Dependencies
```bash
pip install flask flask-cors mysql-connector-python pytz
```

### Step 2: Configure Database
Edit `config.json` with your MySQL credentials:
```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_password",
    "database": "purchase_slips_db"
  }
}
```

### Step 3: Run the Server
```bash
python backend/app.py
```

### Step 4: Open Browser
Navigate to:
```
http://localhost:5000
```

**That's it!** 🎉

---

## Access from Other Devices (LAN)

1. Find your computer's IP address:
   - **Windows**: Open CMD → `ipconfig`
   - **Mac/Linux**: Open Terminal → `ifconfig`

2. Look for IPv4 address (example: `192.168.1.100`)

3. On other devices, open browser and navigate to:
   ```
   http://192.168.1.100:5000
   ```

---

## Default Login

Use your existing database credentials. If this is a fresh install:
- Username: `admin`
- Password: Check your database or contact your administrator

---

## Troubleshooting

### "Cannot connect to backend"
→ Make sure Python backend is running (`python backend/app.py`)

### "Database error"
→ Check MySQL is running and credentials in `config.json` are correct

### "Page not loading"
→ Check browser console (F12) for errors

---

## What Changed from Desktop Version?

**Nothing visible to users!** The app looks and works exactly the same.

Technical changes:
- No more Electron wrapper
- Runs in browser instead of desktop window
- Backend serves web pages
- Automated backups run in background

---

## Features

✅ Login/Logout
✅ Dashboard with statistics
✅ Create purchase slips
✅ View/Edit/Delete slips
✅ Print slips (browser print dialog)
✅ Share on WhatsApp
✅ Automatic database backups (every 24 hours)
✅ User management (admin only)

---

## Production Deployment

For production use with multiple users:

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn (production-ready)
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

See `WEB_DEPLOYMENT_GUIDE.md` for detailed production setup.

---

## Support

- Full documentation: `WEB_DEPLOYMENT_GUIDE.md`
- Conversion details: `CONVERSION_SUMMARY.md`
- Backend logs: Check terminal where `python backend/app.py` is running
- Frontend logs: Browser console (F12)

---

**Enjoy your web-based purchase slip manager!** 🚀
