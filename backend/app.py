from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import sys
import os

# Setup path for imports (works in both dev and PyInstaller)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)
else:
    # Running in normal Python environment
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import init_db, get_next_bill_no
    from routes.slips import slips_bp
    from routes.auth import auth_bp
except ImportError as e:
    print(f"Import error: {e}")
    print(f"sys.path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    if getattr(sys, 'frozen', False):
        print(f"Bundle directory: {sys._MEIPASS}")
    raise

# Setup Flask paths (works in both dev and PyInstaller)
if getattr(sys, 'frozen', False):
    # Running as compiled executable - templates are bundled
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = None  # Not used in desktop app
else:
    # Running in normal Python environment
    template_folder = 'templates'
    static_folder = '../frontend/static'

app = Flask(__name__,
            static_folder=static_folder,
            template_folder=template_folder)

CORS(app)

app.register_blueprint(slips_bp)
app.register_blueprint(auth_bp)

init_db()

@app.route('/')
def index():
    """Serve the main form page"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/reports')
def reports():
    """Serve the reports page"""
    return send_from_directory('../frontend', 'reports.html')

@app.route('/api/next-bill-no')
def next_bill_no_route():
    """Get next bill number"""
    return jsonify({'bill_no': get_next_bill_no()})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌾 RICE MILL PURCHASE SLIP MANAGER")
    print("="*60)
    print("\n✅ Server starting...")
    print("📍 Backend running on: http://127.0.0.1:5000")
    if getattr(sys, 'frozen', False):
        print("📦 Running from packaged executable")
    print("\n💡 Press CTRL+C to stop the server\n")

    # Use debug mode only in development
    is_debug = not getattr(sys, 'frozen', False)
    app.run(debug=is_debug, host='127.0.0.1', port=5000)
