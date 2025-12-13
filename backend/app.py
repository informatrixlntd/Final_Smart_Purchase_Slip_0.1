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
    # Running as compiled executable - templates are bundled
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = None  # Not used in desktop app
    print(f"[INFO] Template folder: {template_folder}")
    print(f"[INFO] Template folder exists: {os.path.exists(template_folder)}")
    if os.path.exists(template_folder):
        print(f"[INFO] Templates: {os.listdir(template_folder)}")
else:
    # Running in normal Python environment
    template_folder = 'templates'
    static_folder = '../frontend/static'

print("[INFO] Creating Flask app...")
app = Flask(__name__,
            static_folder=static_folder,
            template_folder=template_folder)

print("[INFO] Enabling CORS...")
CORS(app)

# Setup frontend folder path (for serving HTML pages in desktop app)
if getattr(sys, 'frozen', False):
    # Running as compiled executable - frontend files are bundled
    FRONTEND_FOLDER = os.path.join(sys._MEIPASS, 'frontend')
    print(f"[INFO] Frontend folder (packaged): {FRONTEND_FOLDER}")
else:
    # Running in normal Python environment
    FRONTEND_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')
    print(f"[INFO] Frontend folder (dev): {FRONTEND_FOLDER}")

print(f"[INFO] Frontend folder exists: {os.path.exists(FRONTEND_FOLDER)}")
if os.path.exists(FRONTEND_FOLDER):
    print(f"[INFO] Frontend contents: {os.listdir(FRONTEND_FOLDER)}")

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
    """Serve the main form page (Create New Slip UI)"""
    try:
        return send_from_directory(FRONTEND_FOLDER, 'index.html')
    except Exception as e:
        print(f"[ERROR] Failed to serve index.html: {e}")
        return jsonify({
            'error': 'index.html not found',
            'frontend_folder': FRONTEND_FOLDER,
            'exists': os.path.exists(FRONTEND_FOLDER),
            'files': os.listdir(FRONTEND_FOLDER) if os.path.exists(FRONTEND_FOLDER) else []
        }), 404

@app.route('/reports')
def reports():
    """Serve the reports page"""
    try:
        return send_from_directory(FRONTEND_FOLDER, 'reports.html')
    except Exception as e:
        print(f"[ERROR] Failed to serve reports.html: {e}")
        return jsonify({
            'error': 'reports.html not found',
            'frontend_folder': FRONTEND_FOLDER,
            'exists': os.path.exists(FRONTEND_FOLDER),
            'files': os.listdir(FRONTEND_FOLDER) if os.path.exists(FRONTEND_FOLDER) else []
        }), 404

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images) for the frontend"""
    try:
        static_folder = os.path.join(FRONTEND_FOLDER, 'static')
        return send_from_directory(static_folder, filename)
    except Exception as e:
        print(f"[ERROR] Failed to serve static file {filename}: {e}")
        return jsonify({
            'error': 'Static file not found',
            'filename': filename,
            'static_folder': os.path.join(FRONTEND_FOLDER, 'static')
        }), 404

@app.route('/api/next-bill-no')
def next_bill_no_route():
    """Get next bill number"""
    try:
        return jsonify({'bill_no': get_next_bill_no()})
    except Exception as e:
        print(f"[ERROR] Failed to get next bill number: {e}")
        return jsonify({'error': str(e), 'bill_no': 1}), 500

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
