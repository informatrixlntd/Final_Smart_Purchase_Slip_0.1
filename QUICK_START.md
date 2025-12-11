# 🚀 Quick Start - Build Your .EXE Installer

## ⚡ Super Simple 3-Step Process

### Step 1: Update MySQL Settings (1 minute)

Open `config.json` and update with YOUR MySQL details:

```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "YOUR_PASSWORD_HERE",
    "database": "purchase_slips_db"
  }
}
```

### Step 2: Run Build Script (5-10 minutes)

Open Command Prompt in project folder and run:

```cmd
build-windows.bat
```

Wait for it to complete. You'll see progress messages.

### Step 3: Get Your Installer

Your `.exe` installer is ready at:

```
desktop\dist\Smart Purchase Slip Setup.exe
```

**Size:** ~150-200 MB

---

## 🎯 What You Get

- ✅ Single `.exe` installer file
- ✅ No Python/Node.js needed on client computers
- ✅ Connects to your MySQL server
- ✅ Desktop icon and Start Menu shortcuts
- ✅ Professional Windows installer

---

## 🖥️ Deploying to Other Computers

1. **Copy** `Smart Purchase Slip Setup.exe` to client computer
2. **Run** the installer
3. **Update** config at: `C:\Users\[User]\AppData\Local\Programs\smart-purchase-slip\resources\config.json`
4. **Change** `host` to your server's IP (e.g., `192.168.1.100`)
5. **Launch** the app!

---

## 📚 Need More Details?

See `BUILD_AND_DEPLOY_GUIDE.md` for:
- Network setup
- MySQL remote access
- Firewall configuration
- Troubleshooting
- Security best practices

---

## ⚠️ Before Building

Make sure you have:
- [x] Python 3.8+ installed (`python --version`)
- [x] Node.js 18+ installed (`node --version`)
- [x] MySQL running on your machine
- [x] Updated `config.json` with your MySQL password

---

## 🎉 That's It!

Run `build-windows.bat` and you're done!

The script does everything automatically:
1. ✅ Installs dependencies
2. ✅ Packages backend
3. ✅ Builds Electron app
4. ✅ Creates installer

---

**Questions?** Check `BUILD_AND_DEPLOY_GUIDE.md`
