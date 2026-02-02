# Playwright PDF Service - Quick Installation Guide

## ⚡ Quick Setup (3 steps)

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- `playwright>=1.40.0` (PDF generation engine)
- `jinja2>=3.1.2` (HTML templating)
- All other existing dependencies

### Step 2: Install Chromium Browser
```bash
playwright install chromium
```

**What this does:**
- Downloads Chromium browser binary (~300MB)
- Installs to `~/.cache/ms-playwright/` (Linux/Mac) or `%USERPROFILE%\AppData\Local\ms-playwright\` (Windows)
- Required for PDF generation

**Expected output:**
```
Downloading Chromium 123.0.6312.4 (playwright build v1097)
...
Chromium 123.0.6312.4 (playwright build v1097) downloaded to ...
```

### Step 3: Verify Installation
```bash
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright installed successfully')"
```

---

## 🚀 Start the Application

```bash
cd backend
python app.py
```

**Expected output:**
```
[OK] Centralized PDF service loaded successfully
[OK] Server starting...
[INFO] Backend running on: http://127.0.0.1:5000
```

---

## 🧪 Test PDF Generation

1. Open browser: `http://127.0.0.1:5000`
2. Login: `admin` / `admin`
3. Create a test slip with Marathi text
4. Click "Print/PDF" button
5. PDF should open with perfect Marathi rendering (no black boxes)

---

## 🐧 Production Deployment (Linux/Docker)

### Option 1: Ubuntu/Debian Server
```bash
# Install system dependencies for Chromium
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2

# Install Python dependencies
pip install -r requirements.txt

# Install Chromium
playwright install chromium
```

### Option 2: Docker
```dockerfile
FROM python:3.12-slim

# Install Playwright system dependencies
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Chromium browser
RUN playwright install chromium

COPY . .
CMD ["python", "backend/app.py"]
```

---

## 🔧 Troubleshooting

### Issue: `playwright: command not found`
**Fix:** Ensure Playwright is installed:
```bash
pip install playwright
```

### Issue: `Executable doesn't exist at ...`
**Fix:** Install Chromium browser:
```bash
playwright install chromium
```

### Issue: Missing system libraries (Linux)
**Fix:** Install required packages:
```bash
sudo apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0
```

### Issue: Permission denied
**Fix:** Run as user with proper permissions or use virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
playwright install chromium
```

---

## 📦 What Gets Installed

### Python Packages (from requirements.txt)
```
playwright>=1.40.0      # Browser automation & PDF generation
jinja2>=3.1.2          # HTML template rendering
flask>=3.0.0           # Web framework
flask-cors>=4.0.0      # CORS support
mysql-connector-python # Database
pytz>=2024.1           # Timezone support
```

### Browser Binary
- **Chromium** (~300MB)
- Location: `~/.cache/ms-playwright/chromium-*/`
- Used for headless PDF generation

---

## ✅ Installation Complete!

Your PDF service is now ready to generate beautiful PDFs with perfect Marathi support.

**Next:** Test by creating a purchase slip with Marathi text and generating a PDF.
