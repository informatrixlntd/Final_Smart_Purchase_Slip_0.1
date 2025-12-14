from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import sys
import os
import traceback

print("\n" + "="*60)
print("SMART PURCHASE SLIP BACKEND - STARTUP")
print("="*60)
print(f"[INFO] Python version: {sys.version}")
print(f"[INFO] Platform: {sys.platform}")
print(f"[INFO] Frozen: {getattr(sys, 'frozen', False)}")
print(f"[INFO] CWD: {os.getcwd()}")

# Setup path for imports (works in both dev and PyInstaller)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)
    print(f"[INFO] Bundle dir (_MEIPASS): {bundle_dir}")
    print(f"[INFO] Executable: {sys.executable}")
    print(f"[INFO] Executable dir: {os.path.dirname(sys.executable)}")
else:
    # Running in normal Python environment
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"[INFO] Running in development mode")

print(f"[INFO] sys.path: {sys.path[:3]}...")

# Import modules with detailed error reporting
try:
    print("[INFO] Importing database module...")
    from database import init_db, get_next_bill_no
    print("[OK] Database module imported")

    print("[INFO] Importing routes modules...")
    from routes.slips import slips_bp
    from routes.auth import auth_bp
    print("[OK] Routes modules imported")
except ImportError as e:
    print(f"[FATAL] Import error: {e}")
    print(f"[FATAL] Traceback:\n{traceback.format_exc()}")
    print(f"[FATAL] sys.path: {sys.path}")
    print(f"[FATAL] Current directory: {os.getcwd()}")
    if getattr(sys, 'frozen', False):
        print(f"[FATAL] Bundle directory: {sys._MEIPASS}")
        print(f"[FATAL] Bundle contents: {os.listdir(sys._MEIPASS)[:20]}")
    sys.exit(1)

# Setup Flask paths (works in both dev and PyInstaller)
print("[INFO] Setting up Flask paths...")
if getattr(sys, 'frozen', False):
    # Running as compiled executable - all files are bundled in _MEIPASS
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'desktop', 'static')
    desktop_folder = os.path.join(sys._MEIPASS, 'desktop')
    print(f"[INFO] Template folder: {template_folder}")
    print(f"[INFO] Static folder: {static_folder}")
    print(f"[INFO] Desktop folder: {desktop_folder}")
    print(f"[INFO] Template folder exists: {os.path.exists(template_folder)}")
    print(f"[INFO] Desktop folder exists: {os.path.exists(desktop_folder)}")
    if os.path.exists(template_folder):
        print(f"[INFO] Templates: {os.listdir(template_folder)}")
    if os.path.exists(desktop_folder):
        print(f"[INFO] Desktop files: {os.listdir(desktop_folder)}")
else:
    # Running in normal Python environment
    template_folder = 'templates'
    static_folder = '../desktop/static'
    desktop_folder = '../desktop'

print("[INFO] Creating Flask app...")
app = Flask(__name__,
            static_folder=static_folder,
            template_folder=template_folder)

print("[INFO] Enabling CORS...")
CORS(app)

print("[INFO] Registering blueprints...")
app.register_blueprint(slips_bp)
app.register_blueprint(auth_bp)
print("[OK] Blueprints registered")

# Initialize database with error handling
print("[INFO] Initializing database...")
try:
    init_db()
    print("[OK] Database initialized successfully")
except Exception as e:
    print(f"[ERROR] Database initialization failed: {e}")
    print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
    print("[WARNING] Continuing without database - some features may not work")
    # Don't exit - allow Flask to start so we can see error messages

@app.route('/')
def index():
    """Serve the main form page"""
    return send_from_directory(desktop_folder, 'index.html')

@app.route('/api/next-bill-no')
def next_bill_no_route():
    """Get next bill number"""
    return jsonify({'bill_no': get_next_bill_no()})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("RICE MILL PURCHASE SLIP MANAGER")
    print("="*60)
    print("\n[OK] Server starting...")
    print("[INFO] Backend running on: http://127.0.0.1:5000")
    if getattr(sys, 'frozen', False):
        print("[INFO] Running from packaged executable")
    print("\n[INFO] Press CTRL+C to stop the server\n")

    # Use debug mode only in development
    is_debug = not getattr(sys, 'frozen', False)
    app.run(debug=is_debug, host='127.0.0.1', port=5000)
