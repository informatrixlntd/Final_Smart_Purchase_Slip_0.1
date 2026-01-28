"""
Automated Database Backup Service
Runs as a background thread to automatically backup MySQL database
and upload to Google Drive at scheduled intervals.
"""

import os
import json
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

# Backup configuration
BACKUP_INTERVAL_HOURS = 24  # Run backup every 24 hours
BACKUP_DIR = os.path.join(
    os.path.expanduser("~"),
    "Documents",
    "smart_purchase_slip_backup"
)

# Ensure backup directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)


def load_config():
    """Load database configuration from config.json"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[BACKUP] Error loading config: {e}")
        return None


def create_mysql_backup(db_config):
    """Create MySQL database backup using mysqldump"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        backup_filename = f"purchase_slips_backup_{timestamp}.sql"
        backup_filepath = os.path.join(BACKUP_DIR, backup_filename)

        # Build mysqldump command
        command = [
            'mysqldump',
            '-h', db_config['host'],
            '-P', str(db_config['port']),
            '-u', db_config['user'],
            f"-p{db_config['password']}",
            db_config['database']
        ]

        # Execute mysqldump and write to file
        with open(backup_filepath, 'w') as f:
            result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            print(f"[BACKUP] Database backup created: {backup_filepath}")
            return backup_filepath
        else:
            print(f"[BACKUP] mysqldump failed: {result.stderr}")
            return None

    except Exception as e:
        print(f"[BACKUP] Error creating backup: {e}")
        return None


def upload_to_google_drive(filepath):
    """
    Upload backup file to Google Drive using Google Drive API
    Note: This requires google-auth and google-api-python-client packages
    and OAuth credentials configured in tokens.json
    """
    try:
        # Try importing Google Drive libraries
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        TOKEN_PATH = os.path.join(os.path.dirname(__file__), '..', 'desktop', 'tokens.json')

        # Load saved tokens if available
        creds = None
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'r') as token:
                token_data = json.load(token)
                creds = Credentials(
                    token=token_data.get('access_token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id='432729181710-4jnntjamivku6a3in4k0vo4ft4ag8vg6.apps.googleusercontent.com',
                    client_secret='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'
                )

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        if creds:
            # Upload to Google Drive
            service = build('drive', 'v3', credentials=creds)
            file_metadata = {
                'name': os.path.basename(filepath),
                'mimeType': 'application/sql'
            }
            media = MediaFileUpload(filepath, mimetype='application/sql')
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name'
            ).execute()

            print(f"[BACKUP] Uploaded to Google Drive: {file.get('name')} (ID: {file.get('id')})")
            return True
        else:
            print("[BACKUP] No valid Google Drive credentials found. Backup saved locally only.")
            return False

    except ImportError:
        print("[BACKUP] Google Drive API libraries not installed. Backup saved locally only.")
        return False
    except Exception as e:
        print(f"[BACKUP] Error uploading to Google Drive: {e}")
        return False


def perform_backup():
    """Perform full backup workflow: create dump + upload to Drive"""
    print(f"\n[BACKUP] Starting automated backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    config = load_config()
    if not config or 'database' not in config:
        print("[BACKUP] Failed to load database configuration")
        return False

    db_config = config['database']

    # Create MySQL backup
    backup_file = create_mysql_backup(db_config)
    if not backup_file:
        print("[BACKUP] Failed to create database backup")
        return False

    # Upload to Google Drive (optional - fails gracefully if not configured)
    upload_to_google_drive(backup_file)

    print("[BACKUP] Backup process completed")
    return True


def backup_scheduler():
    """Background thread that runs backup at scheduled intervals"""
    print(f"[BACKUP] Scheduler started - backups will run every {BACKUP_INTERVAL_HOURS} hours")
    print(f"[BACKUP] Backup directory: {BACKUP_DIR}")

    while True:
        try:
            perform_backup()
        except Exception as e:
            print(f"[BACKUP] Unexpected error in backup scheduler: {e}")

        # Wait for next backup interval
        time.sleep(BACKUP_INTERVAL_HOURS * 3600)


def start_backup_service():
    """Start the backup service as a daemon thread"""
    backup_thread = threading.Thread(target=backup_scheduler, daemon=True)
    backup_thread.start()
    print("[BACKUP] Background backup service started")


if __name__ == '__main__':
    # For testing - run backup immediately
    perform_backup()
