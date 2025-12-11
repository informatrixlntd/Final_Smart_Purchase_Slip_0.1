# Smart Purchase Slip - Build & Deployment Guide

## 📋 Overview

This guide explains how to:
1. Build a single `.exe` installer on your Windows machine
2. Deploy it to client computers
3. Configure MySQL database connection

---

## 🏗️ Building the Installer

### Prerequisites

Before building, ensure you have:

1. **Windows 10/11** operating system
2. **Python 3.8+** installed ([Download](https://www.python.org/downloads/))
   - ✅ Check: Open CMD and run `python --version`
   - Make sure "Add Python to PATH" was checked during installation

3. **Node.js 18+** installed ([Download](https://nodejs.org/))
   - ✅ Check: Open CMD and run `node --version`

4. **MySQL Server** running on your machine
   - ✅ Check: MySQL should be accessible at `localhost:3306`
   - Note your database credentials (username, password)

### Step 1: Configure MySQL Connection

1. Open `config.json` in the project root
2. Update the database settings:

```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "your_mysql_password",
    "database": "purchase_slips_db"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

**Important Notes:**
- `host`: Your computer's IP address on the local network (use `localhost` for same machine)
- `port`: MySQL port (default is 3306)
- `user`: MySQL username
- `password`: MySQL password
- `database`: Database name (will be created automatically if it doesn't exist)

### Step 2: Build the Installer

1. Open **Command Prompt** or **PowerShell**
2. Navigate to the project folder:
   ```cmd
   cd path\to\project
   ```

3. Run the build script:
   ```cmd
   build-windows.bat
   ```

4. The script will:
   - Install Python dependencies
   - Package the backend into `purchase_slips_backend.exe`
   - Install Node.js dependencies
   - Build the Electron installer
   - Create `Smart Purchase Slip Setup.exe`

5. **Build time:** 5-10 minutes depending on your computer

6. **Result:** The installer will be created at:
   ```
   desktop\dist\Smart Purchase Slip Setup.exe
   ```

**Installer Size:** Approximately 150-200 MB

---

## 🚀 Deploying to Client Computers

### Architecture

Your setup will work as follows:

```
┌─────────────────────────────────────┐
│   YOUR SERVER COMPUTER              │
│                                     │
│   ┌─────────────────────────┐      │
│   │  MySQL Server           │      │
│   │  (localhost:3306)       │      │
│   │  Database:              │      │
│   │  purchase_slips_db      │      │
│   └─────────────────────────┘      │
│                                     │
│   IP Address: 192.168.1.100        │
│   (example)                         │
└─────────────────────────────────────┘
                 ▲
                 │
                 │ Network Connection
                 │
    ┌────────────┴────────────┐
    │                         │
┌───▼──────────┐      ┌──────▼────┐
│ Client PC 1  │      │ Client PC 2│
│              │      │             │
│ Runs .exe    │      │ Runs .exe   │
│ Connects to  │      │ Connects to │
│ 192.168.1.100│      │ 192.168.1.100│
└──────────────┘      └─────────────┘
```

### Server Computer Setup

1. **Find your IP address:**
   ```cmd
   ipconfig
   ```
   - Look for `IPv4 Address` under your active network adapter
   - Example: `192.168.1.100`

2. **Configure MySQL for remote access:**

   Open MySQL Command Line or MySQL Workbench and run:

   ```sql
   -- Create a user for remote access
   CREATE USER 'purchase_slip_user'@'%' IDENTIFIED BY 'secure_password';

   -- Grant permissions
   GRANT ALL PRIVILEGES ON purchase_slips_db.* TO 'purchase_slip_user'@'%';

   -- Apply changes
   FLUSH PRIVILEGES;
   ```

3. **Configure Windows Firewall:**

   Open PowerShell as Administrator:

   ```powershell
   # Allow MySQL through firewall
   New-NetFirewallRule -DisplayName "MySQL Server" -Direction Inbound -Protocol TCP -LocalPort 3306 -Action Allow

   # Allow Backend Server through firewall
   New-NetFirewallRule -DisplayName "Purchase Slip Backend" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
   ```

4. **Edit MySQL Configuration (if needed):**

   Open `my.ini` (usually at `C:\ProgramData\MySQL\MySQL Server 8.0\my.ini`):

   Find and change:
   ```ini
   bind-address = 0.0.0.0
   ```

   Then restart MySQL service:
   ```cmd
   net stop MySQL80
   net start MySQL80
   ```

### Client Computer Installation

1. **Copy the installer** to the client computer:
   - Transfer `Smart Purchase Slip Setup.exe` via USB drive, network share, or email

2. **Run the installer** on the client computer:
   - Double-click `Smart Purchase Slip Setup.exe`
   - Follow the installation wizard
   - Choose installation location
   - The app will install (takes ~2-3 minutes)

3. **Configure connection to server:**

   After installation, navigate to:
   ```
   C:\Users\[Username]\AppData\Local\Programs\smart-purchase-slip\resources\config.json
   ```

   Edit with Notepad:
   ```json
   {
     "database": {
       "host": "192.168.1.100",
       "port": 3306,
       "user": "purchase_slip_user",
       "password": "secure_password",
       "database": "purchase_slips_db"
     }
   }
   ```

   **Replace:**
   - `192.168.1.100` with your server's IP address
   - `purchase_slip_user` with your MySQL username
   - `secure_password` with your MySQL password

4. **Launch the application:**
   - Open from Desktop shortcut or Start Menu
   - Login with default credentials:
     - Username: `admin`
     - Password: `admin`

---

## 🔧 Troubleshooting

### Issue: "Cannot connect to MySQL server"

**Solutions:**
1. Check if MySQL is running on the server:
   ```cmd
   net start MySQL80
   ```

2. Verify the IP address is correct:
   ```cmd
   ping 192.168.1.100
   ```

3. Check Windows Firewall settings

4. Verify MySQL user has remote access permissions

### Issue: "Backend not starting"

**Solutions:**
1. Check if another program is using port 5000:
   ```cmd
   netstat -ano | findstr :5000
   ```

2. Try running the app as Administrator

3. Check antivirus isn't blocking the executable

### Issue: "Database not found"

**Solution:**
The database will be created automatically on first run. If it fails:

```sql
CREATE DATABASE purchase_slips_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 🔐 Security Best Practices

1. **Change default admin password immediately**
   - Login → Settings → Change Password

2. **Use strong MySQL passwords**
   - At least 12 characters
   - Mix of letters, numbers, symbols

3. **Limit MySQL user permissions**
   - Only grant access to `purchase_slips_db`
   - Don't use root account for clients

4. **Regular backups**
   - Set up automated MySQL backups
   - Store backups in multiple locations

---

## 📊 Network Requirements

- **Local Network:** All computers must be on the same network
- **Bandwidth:** Minimal (< 1 MB per transaction)
- **Latency:** Works well on standard LAN (< 50ms ping)

---

## 🆕 Updating the Application

### To update all clients:

1. Make changes to the code
2. Run `build-windows.bat` again
3. Distribute new `.exe` installer
4. Clients run the new installer (it will update existing installation)

**Note:** Database structure updates may require running migration scripts

---

## 💡 Alternative: Standalone Mode (Each PC has own database)

If you want each computer to have its own database:

1. Install MySQL on each client computer
2. Keep `config.json` with `host: "localhost"`
3. Each computer maintains separate data

**Pros:**
- Works without network
- No single point of failure

**Cons:**
- No centralized data
- Harder to sync across locations
- More maintenance (backup each PC)

---

## 📞 Support

For technical support or issues:
- Check the troubleshooting section above
- Review application logs in: `C:\Users\[Username]\AppData\Local\Programs\smart-purchase-slip\`
- Contact your system administrator

---

## ✅ Checklist

Before deployment, ensure:

- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed
- [ ] MySQL server running and accessible
- [ ] `config.json` configured correctly
- [ ] Windows Firewall rules added
- [ ] MySQL remote access configured
- [ ] Build completed successfully
- [ ] Installer tested on at least one client computer
- [ ] Default admin password changed
- [ ] Backup strategy in place

---

**Version:** 2.0.0
**Last Updated:** December 2024
