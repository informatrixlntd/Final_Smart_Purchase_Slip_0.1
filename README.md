# Smart Purchase Slip Manager
**LAN-Based Web Application for Rice Mill Purchase Slip Management**

Version: 2.0 (Web Application)
Database: MySQL
Status: ✅ STABLE & PRODUCTION-READY

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [System Architecture](#system-architecture)
4. [Features](#features)
5. [Installation](#installation)
6. [Usage Guide](#usage-guide)
7. [Database Schema](#database-schema)
8. [API Endpoints](#api-endpoints)
9. [PDF Generation](#pdf-generation)
10. [Troubleshooting](#troubleshooting)
11. [Recent Fixes](#recent-fixes)
12. [Security Considerations](#security-considerations)

---

## 🎯 OVERVIEW

Smart Purchase Slip Manager is a comprehensive web application for rice mill operations, handling:
- Purchase slip creation with auto-calculations
- Payment tracking with installment support
- PDF generation with Marathi/Hindi labels
- Dashboard analytics
- User management (admin/user roles)

**Migration:** Fully migrated from Electron desktop app to LAN-based web application.

---

## 🚀 QUICK START

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Configure database (edit config.json)
{
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "your_password",
  "database": "purchase_slips_db"
}

# 3. Start backend server
cd backend
python3 app.py

# 4. Open browser
http://localhost:5000

# 5. Login
Username: admin
Password: admin
```

**Application will be accessible to all devices on your LAN at `http://YOUR_IP:5000`**

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────┐
│           Frontend (Browser)                │
│  HTML + Vanilla JS + Bootstrap 5            │
│  ├─ Login (authentication)                  │
│  ├─ Dashboard (analytics & charts)          │
│  ├─ Create Slip (form with calculations)    │
│  ├─ View Slips (table with actions)         │
│  └─ Users Management (admin only)           │
└──────────────────┬──────────────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────────────┐
│         Backend (Flask Python)              │
│  ├─ app.py (Flask server)                   │
│  ├─ routes/slips.py (CRUD + analytics)      │
│  ├─ routes/auth.py (authentication)         │
│  ├─ pdf_service.py (PDF generation)         │
│  ├─ database.py (MySQL connection pool)     │
│  └─ whatsapp_service.py (future feature)    │
└──────────────────┬──────────────────────────┘
                   │ MySQL Connection
┌──────────────────▼──────────────────────────┐
│           MySQL Database                    │
│  ├─ purchase_slips (48 columns)             │
│  ├─ users (authentication)                  │
│  └─ unloading_godowns (dropdown data)       │
└─────────────────────────────────────────────┘
```

---

## ✨ FEATURES

### 1. Purchase Slip Management
- **Create Slip**: Comprehensive form with 60+ fields
  - Company & party details
  - Weight calculations (bags, quintal, khandi)
  - Rate-based amount calculation (Quintal or Khandi basis)
  - Multiple deduction types (bank commission, freight, TDS, etc.)
  - Up to 5 payment instalments
  - Auto-calculation of payable amount

- **View Slips**: Paginated table with search
  - Filter by party name
  - View full details in modal
  - Print to PDF
  - Share via WhatsApp (coming soon)
  - Delete with confirmation

- **Edit Slip**: Update existing slips with same form

### 2. Dashboard Analytics
- Total purchase quantity (quintal)
- Total purchase amount
- Net payable amount
- Outstanding amount
- Daily purchase trend (Chart.js)
- Rate trend over time
- Top suppliers by quantity
- Payment mode breakdown
- Godown-wise stock

### 3. PDF Generation
- **Marathi/Hindi bilingual labels**
- Professional layout matching rice mill standards
- Auto-generated with cached performance
- Includes:
  - Company & party details
  - Weight & rate calculations
  - Itemized deductions
  - Payment summary with green highlight
  - Payment installment table
  - Signatures section

### 4. User Management (Admin)
- Add/edit/delete users
- Role-based access (admin/user)
- Password management
- Last login tracking

---

## 💾 INSTALLATION

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

### Step 1: Clone/Extract Project
```bash
cd /path/to/project
```

### Step 2: Install Python Dependencies
```bash
pip3 install -r requirements.txt
```

**Required Packages:**
- flask >= 3.0.0
- flask-cors >= 4.0.0
- mysql-connector-python >= 8.0.0
- pytz >= 2024.1
- xhtml2pdf >= 0.2.11
- requests >= 2.31.0

### Step 3: Configure MySQL Database
Create `config.json` in project root:
```json
{
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "your_mysql_password",
  "database": "purchase_slips_db"
}
```

### Step 4: Initialize Database
```bash
cd backend
python3 app.py
```

On first run, the application will:
- Create `purchase_slips_db` database
- Create all required tables
- Add default admin user (admin/admin)
- Add sample godown data

### Step 5: Access Application
```bash
# Local access
http://localhost:5000

# LAN access (from other devices)
http://YOUR_IP_ADDRESS:5000
```

To find your IP:
```bash
# Linux/Mac
ifconfig | grep inet

# Windows
ipconfig
```

---

## 📖 USAGE GUIDE

### Creating a Purchase Slip

**Flow:** Dashboard → Create New Slip → Fill Form → Save → View in Slips Table

1. Click "Create New Slip" in sidebar
2. Fill in details (auto-calculations happen in real-time):

**Company Details:**
- Company name, address, GST No, Mobile No

**Vehicle & Party:**
- Vehicle number, Date (auto-filled), Bill No (auto-generated)
- Party name, Mobile, Material, Broker

**Weight & Rate:**
- Bags: Number of bags
- Net Weight (KG): From weighing scale
- Gunny/Bora Weight (KG): Empty bag weight
- **Auto-calculated fields:**
  - Avg Bag Weight = Final Weight / Bags
  - Final Weight = Net Weight - Gunny Weight
  - Weight (Quintal) = Final Weight / 100
  - Weight (Khandi) = Final Weight / 150
- Rate Basis: Select "Quintal" or "Khandi"
- Rate Value: Price per unit
- **Auto-calculated:**
  - Total Amount = Weight × Rate

**Deductions:**
- Direct ₹ deductions: Bank commission, Postage, Freight, TDS, etc.
- Percentage deductions: Batav (% of total amount)
- Calculated deductions:
  - Dalali: (Net Weight / 100) × Rate
  - Hammali: (Net Weight / 100) × Rate
- **Auto-calculated:**
  - Total Deductions = Sum of all
  - **Payable Amount = Total Amount - Total Deductions**

**Payment Instalments:** (Optional, up to 5)
- Date, Amount, Payment Method, Bank Account, Comment

3. Click "Save" button
4. Redirected to "View All Slips" with new slip highlighted

---

### Viewing & Managing Slips

**View All Slips Table:**
- Bill No, Date, Party Name, Material, Final Weight, Rate, Amount, Payable, Actions

**Actions:**
- **View**: Opens modal with complete slip details
- **Print**: Generates and downloads PDF
- **Delete**: Confirms and removes slip

**Search:** Filter by party name in search box

---

### Generating PDF Reports

**Method 1: From Slips Table**
1. Click "Print PDF" button on any slip
2. PDF opens in new browser tab
3. Use browser print dialog (Ctrl+P) to print or save

**Method 2: From View Modal**
1. Click "View" on any slip
2. Click "Print PDF" in modal footer

**PDF Features:**
- Bilingual labels (Marathi/Hindi + English data)
- Professional layout on A4 size
- Company letterhead area
- Complete itemized breakdown
- Payment summary with green highlight
- Installment payment table
- Signature lines for prepared by & authorized signatory

---

### Dashboard Analytics

**Metrics Displayed:**
- Total Bills
- Total Paddy Quantity (quintal)
- Total Purchase Amount
- Total Deductions
- Net Payable Amount
- Total Paid
- Total Outstanding
- Average Effective Rate

**Charts:**
- Daily Purchase Trend (line chart)
- Rate Trend Over Time (line chart)
- Deduction Breakdown (bar chart)
- Top 10 Suppliers (bar chart)
- Payment Mode Distribution (pie chart)
- Godown Stock (bar chart)

**Period Filter:** Today, This Week, This Month, This Year

---

## 🗄️ DATABASE SCHEMA

### Table: `purchase_slips`

**Primary Key:** `id` (AUTO_INCREMENT)

**48 Columns organized in categories:**

**Company & Document Info:**
- company_name, company_address, company_gst_no, company_mobile_no
- document_type (default: "Purchase Slip")
- bill_no (unique invoice number)
- date, vehicle_no

**Party Details:**
- party_name, mobile_number
- material_name, broker
- terms_of_delivery, sup_inv_no, gst_no, ticket_no

**Weight & Rate:**
- bags, avg_bag_weight
- net_weight_kg, gunny_weight_kg, final_weight_kg
- weight_quintal, weight_khandi
- rate_basis ("Quintal" or "Khandi")
- rate_value, total_purchase_amount

**Deductions (14 types):**
- bank_commission, postage, freight
- rate_diff, quality_diff (+ quality_diff_comment)
- moisture_ded, moisture_percent, moisture_kg (+ moisture_ded_comment)
- tds
- batav_percent, batav
- shortage_percent, shortage
- dalali_rate, dalali
- hammali_rate, hammali
- total_deduction, payable_amount (calculated)

**Payment Instalments (5 sets):**
- instalment_N_date, instalment_N_amount
- instalment_N_payment_method, instalment_N_payment_bank_account
- instalment_N_comment
(where N = 1 to 5)

**Footer Info:**
- prepared_by, authorised_sign
- paddy_unloading_godown

**Indexes:**
- idx_date (date)
- idx_party_name (party_name)
- idx_bill_no (bill_no)

---

### Table: `users`

**Columns:**
- id (PRIMARY KEY)
- username (UNIQUE)
- password (plaintext - for LAN use only)
- full_name
- role ("admin" or "user")
- is_active (BOOLEAN)
- created_at (TIMESTAMP)
- last_login (TIMESTAMP)

---

### Table: `unloading_godowns`

**Columns:**
- id (PRIMARY KEY)
- name (UNIQUE)
- created_at (TIMESTAMP)

**Purpose:** Dropdown options for "Paddy Unloading Godown" field

---

## 🔌 API ENDPOINTS

### Authentication

**POST `/api/login`**
```json
Request: { "username": "admin", "password": "admin" }
Response: {
  "success": true,
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "Administrator",
    "role": "admin"
  }
}
```

---

### Purchase Slips

**POST `/api/add-slip`**
- Creates new purchase slip
- Auto-calculates all fields
- Returns slip_id and bill_no

**GET `/api/slips?page=1&limit=50`**
- Returns paginated list of all slips
- Includes total_paid_amount and balance_amount

**GET `/api/slip/<slip_id>`**
- Returns complete slip data with all fields

**PUT `/api/slip/<slip_id>`**
- Updates existing slip
- Recalculates all fields
- Invalidates PDF cache

**DELETE `/api/slip/<slip_id>`**
- Deletes slip permanently

**GET `/api/slip/<slip_id>/pdf`**
- Generates and returns PDF
- Uses disk caching for performance
- Filename: `Purchase_Slip_{party_name}_{bill_no}.pdf`

---

### Dashboard

**GET `/api/dashboard?period=today|week|month|year`**
- Returns comprehensive analytics
- Metrics, trends, charts data, top suppliers, etc.

---

### Godowns

**GET `/api/unloading-godowns`**
- Returns list of all godown names

**POST `/api/unloading-godowns`**
```json
Request: { "name": "Godown C" }
Response: {
  "success": true,
  "godown": { "id": 6, "name": "Godown C" },
  "godowns": [ /* all godowns */ ]
}
```

---

### Users (Admin Only)

**GET `/api/users`**
- Returns all users

**POST `/api/users`**
```json
Request: {
  "username": "user1",
  "password": "pass123",
  "full_name": "User One",
  "role": "user",
  "requesting_user_role": "admin"
}
```

**PUT `/api/users/<user_id>`**
- Updates user details

**DELETE `/api/users/<user_id>`**
- Soft deletes user (sets is_active=FALSE)

---

## 📄 PDF GENERATION

### Technology Stack
- **Library:** xhtml2pdf (HTML → PDF conversion)
- **Template Engine:** Jinja2
- **Font:** NotoSansDevanagari-Regular.ttf (embedded Unicode font)
- **Caching:** MD5-based disk cache for performance

### How It Works

1. **Data Retrieval:**
   - Fetch slip data from database
   - Calculate payment totals (total_paid, balance)
   - Format dates to IST timezone

2. **Template Rendering:**
   - Load HTML template: `backend/templates/print_template_new.html`
   - Inject slip data using Jinja2
   - Pass font path for Marathi text support

3. **Font Registration:**
   - Register NotoSansDevanagari font with ReportLab
   - Ensures Devanagari characters render correctly
   - Font embedded in PDF for portability

4. **PDF Generation:**
   - Convert HTML to PDF using xhtml2pdf
   - UTF-8 encoding throughout pipeline
   - A4 portrait layout with 10mm margins

5. **Caching:**
   - Cache key: `slip_{id}_{md5_hash_of_data}`
   - Cache hit: Return cached PDF (instant)
   - Cache miss: Generate new PDF and cache
   - Cache invalidation: On slip update

### Template Structure

**File:** `backend/templates/print_template_new.html`

**Sections:**
1. Header: Company name, address, GST, mobile
2. Document Info: Bill no, date, vehicle no
3. पार्टी डिटेल्स (Party Details): Party, material, broker, GST, mobile
4. वजन व दर तपशील (Weight & Rate): Complete weight breakdown table
5. कपात (Deductions): Itemized deductions table
6. Summary: Gross amount, deductions, net payable
7. 💰 देयक सारांश (Payment Summary): Green-highlighted payment status
8. हप्ते तपशील (Instalments): Payment installment table
9. धान उतार गोदाम (Godown): Unloading location
10. Footer: Signatures (तयार केले / अधिकृत स्वाक्षरी)

### Marathi Labels Mapping

| English | Marathi |
|---------|---------|
| Purchase Slip | Purchase Slip |
| Company / Mill Name | कंपनी / मिल नाव |
| Address | पत्ता |
| Bill No / Invoice No | बिल क्रमांक / इन्व्हॉईस क्रमांक |
| Date | दिनांक |
| Vehicle No | वाहन क्रमांक |
| Party Details | पार्टी डिटेल्स |
| Party Name | पार्टी नाव |
| Ticket No | तिकेट क्रमांक |
| Material | मटेरियल |
| Broker | दलाल |
| Terms of Delivery | डिलिव्हरी अटी |
| Supplier Invoice No | सप्लायर इनव्हॉईस क्रमांक |
| GST No | GST क्रमांक |
| Mobile Number | मोबाईल नंबर |
| Weight & Rate Details | वजन व दर तपशील |
| Bags | बॅग्स |
| Avg Bag Weight | सरासरी बॅग्स वजन |
| Net Weight (KG) | निव्वळ वजन (KG) |
| Gunny Weight (KG) | बोरा वजन (KG) |
| Final Weight (KG) | अंतिम वजन (KG) |
| Weight (Quintal) | वजन (क्विंटल) |
| Weight (Khandi) | वजन (खंडी) |
| Rate Basis | रेट बेसिस |
| Rate | रेट |
| Amount | रक्कम |
| Deductions | कपात |
| Deduction Type | कपातीचा प्रकार |
| Rate/Percentage | दर / टक्केवारी |
| Bank Commission | बँक कमिशन |
| Postage | टपाल खर्च |
| Freight | वाहतूक |
| Rate Difference | दर फरक |
| Quality Difference | गुणवत्ता फरक |
| Moisture Deduction | ओलावा कपात |
| TDS | TDS |
| Batav | बटावं |
| Dalali | दलाली |
| Hamali | हमाली |
| Total Deductions | एकूण कपात |
| Gross Amount | एकूण रक्कम |
| Net Payable Amount | निव्वळ देय रक्कम |
| Payment Summary | देयक सारांश |
| Payable Amount | देय रक्कम |
| Total Paid Amount | एकूण दिलेली रक्कम |
| Balance Amount | शिल्लक रक्कम |
| Payment Instalments | हप्ते तपशील |
| Sr | क्र. |
| Method | पद्धत |
| Bank Account | बँक खाते |
| Comment | टिप्पणी |
| Paddy Unloading Godown | धान उतार गोदाम |
| Prepared By | तयार केले |
| Authorized Signatory | अधिकृत स्वाक्षरी |

---

## 🔧 TROUBLESHOOTING

### Issue: Create Slip form not loading / JavaScript error

**Symptoms:**
- Blank page when clicking "Create New Slip"
- Console error: `ReferenceError: calculateCalculatedRate is not defined`

**Solution:** ✅ FIXED
- Removed undefined function call from `desktop/static/js/script.js` line 282

---

### Issue: PDF shows black squares (■■■■) instead of Marathi text

**Symptoms:**
- PDF generates but Marathi labels appear as black squares
- Devanagari characters not rendering

**Solution:** ✅ FIXED
1. NotoSansDevanagari font installed in `backend/static/fonts/`
2. Font registered with ReportLab before PDF generation
3. HTML template uses @font-face and font-family declarations
4. UTF-8 encoding enforced throughout

**To verify fix is working:**
```bash
# Restart Flask application
cd backend
python3 app.py

# Clear PDF cache
rm -rf /tmp/cc-agent/61361045/project/pdf_cache/*.pdf

# Generate new PDF from any slip
# Marathi text should render correctly
```

---

### Issue: Database connection error

**Symptoms:**
- Error: "Can't connect to MySQL server"
- Application won't start

**Solution:**
1. Verify MySQL is running:
   ```bash
   # Check MySQL status
   sudo systemctl status mysql

   # Start MySQL if not running
   sudo systemctl start mysql
   ```

2. Check `config.json` settings:
   - Host, port, username, password correct?
   - Database exists or can be created?

3. Test connection manually:
   ```bash
   mysql -u root -p -h localhost
   ```

4. Grant permissions if needed:
   ```sql
   GRANT ALL PRIVILEGES ON purchase_slips_db.* TO 'root'@'localhost';
   FLUSH PRIVILEGES;
   ```

---

### Issue: Port 5000 already in use

**Symptoms:**
- Error: "Address already in use"
- Application won't start

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port
# Edit backend/app.py, change:
app.run(host='0.0.0.0', port=5001, debug=True)
```

---

### Issue: Calculations not updating in real-time

**Symptoms:**
- Changing bags/weight doesn't update totals
- Payable amount not calculating

**Solution:**
1. Clear browser cache (Ctrl+Shift+Delete)
2. Hard refresh (Ctrl+Shift+R)
3. Check browser console for JavaScript errors
4. Ensure all input fields have `.calc-input` class

---

### Issue: Cannot delete slips

**Symptoms:**
- Delete button doesn't work
- Error message after clicking delete

**Solution:**
1. Check user role - only admins can delete
2. Check database foreign key constraints
3. Check browser console for errors
4. Verify DELETE endpoint is accessible

---

## 🔥 RECENT FIXES (2026-01-30)

### Critical Fix #1: Create Slip JavaScript Error ✅
**Problem:** `calculateCalculatedRate()` function called but not defined
**Impact:** Create Slip form wouldn't load, ReferenceError in console
**Solution:** Removed undefined function call from `script.js` line 282
**Status:** FIXED

### Critical Fix #2: Marathi PDF Rendering ✅
**Problem:** PDF showed black squares (■■■■) instead of Marathi text
**Impact:** PDFs unusable for Marathi-speaking users
**Solution:**
- Installed NotoSansDevanagari-Regular.ttf font
- Registered font with ReportLab PDF engine
- Added @font-face to HTML template
- Enforced UTF-8 encoding throughout pipeline
- Updated all labels to Marathi/bilingual format
**Status:** FIXED - Requires application restart

### Code Quality Fix #3: Removed Unused Import ✅
**File:** `backend/pdf_service.py`
**Change:** Removed unused `from flask import render_template` (line 13)
**Impact:** Cleaner code, no functional change
**Status:** FIXED

### Documentation Cleanup #4: Removed Electron-Era Files ✅
**Deleted Files:**
- CHANGES_TO_COMMIT.md (Electron backend crash fix)
- ExeIssue.md (EXE packaging guide, 25K)
- FIXING_ACCESS_VIOLATION.md (Windows exe errors)
- swark-output/*.md (stale auto-generated diagrams)
**Total:** ~42K of obsolete documentation removed
**Status:** CLEANED UP

---

## 🔐 SECURITY CONSIDERATIONS

### For Production Deployment

**WARNING:** This application is designed for LAN (Local Area Network) use within a trusted network environment. If deploying to the internet, implement the following security measures:

### 1. Password Hashing
**Current:** Plaintext passwords in database
**Required:** Implement bcrypt or PBKDF2 hashing

```python
# Use bcrypt for password hashing
import bcrypt

# Hash password before storing
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Verify password
if bcrypt.checkpw(password.encode('utf-8'), hashed):
    # Login success
```

### 2. Authentication Tokens
**Current:** Frontend-enforced role checks
**Required:** Server-side JWT tokens or session management

### 3. Environment Variables
**Current:** Credentials in config.json and source code
**Required:** Use environment variables for sensitive data

```bash
export MYSQL_PASSWORD="secure_password"
export SECRET_KEY="random_secret_key"
export GOOGLE_CLIENT_SECRET="oauth_secret"
```

### 4. HTTPS
**Current:** HTTP (port 5000)
**Required:** Use HTTPS with SSL/TLS certificate

```bash
# Using nginx as reverse proxy with SSL
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

### 5. SQL Injection Prevention
**Current:** Parameterized queries used (good!)
**Note:** Continue using parameterized queries for all database operations

### 6. CORS Configuration
**Current:** CORS enabled globally
**For Production:** Restrict CORS to specific origins

```python
CORS(app, origins=['https://yourdomain.com'])
```

### 7. Rate Limiting
**Current:** No rate limiting
**Required:** Implement rate limiting to prevent abuse

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/api/login')
@limiter.limit("5 per minute")
def login():
    # ...
```

---

## 📞 SUPPORT & MAINTENANCE

### Application Logs
Logs are printed to console (stdout). To save logs:
```bash
python3 app.py > app.log 2>&1
```

### Backup Database
```bash
mysqldump -u root -p purchase_slips_db > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
mysql -u root -p purchase_slips_db < backup_20260130.sql
```

### Update Application
```bash
# Pull latest changes
git pull origin main

# Install new dependencies
pip3 install -r requirements.txt

# Restart application
cd backend
python3 app.py
```

---

## 📚 ADDITIONAL DOCUMENTATION

- **QUICK_START.md** - 3-step quick setup guide
- **WEB_DEPLOYMENT_GUIDE.md** - Comprehensive deployment guide
- **ISSUES_IDENTIFIED.md** - Complete issue analysis and fixes
- **requirements.txt** - Python package dependencies

---

## 📜 LICENSE

See LICENSE.txt

---

## 🎉 CHANGELOG

### Version 2.0 (2026-01-30)
- ✅ Migrated from Electron to LAN web application
- ✅ Fixed Create Slip JavaScript error
- ✅ Fixed Marathi PDF rendering (black squares issue)
- ✅ Updated all PDF labels to Marathi/bilingual format
- ✅ Removed Electron-era documentation
- ✅ Cleaned up code quality issues
- ✅ Created comprehensive authoritative documentation

### Version 1.x (Legacy)
- Electron desktop application (deprecated)

---

**END OF DOCUMENTATION**

For technical support or questions, contact your system administrator.
