import os
import sys
import json

# CRITICAL: Force pure-Python MySQL connector to prevent ACCESS_VIOLATION crashes
os.environ['MYSQL_CONNECTOR_PYTHON_USE_PURE'] = '1'

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

# Verify pure-Python mode is enabled
print(f"[INFO] MySQL Connector version: {mysql.connector.__version__}")
print(f"[INFO] MySQL Connector pure mode: {os.environ.get('MYSQL_CONNECTOR_PYTHON_USE_PURE', 'not set')}")

# Load MySQL configuration from config file or environment
def load_db_config():
    # Try multiple locations for config.json
    config_paths = []

    # If running as PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        bundle_dir = sys._MEIPASS
        exe_dir = os.path.dirname(sys.executable)

        # Try these locations in order:
        # 1. In resources folder (Electron packaged app)
        config_paths.append(os.path.join(exe_dir, '..', '..', 'resources', 'config.json'))
        # 2. Next to dist-backend folder
        config_paths.append(os.path.join(exe_dir, '..', 'config.json'))
        # 3. In bundle directory
        config_paths.append(os.path.join(bundle_dir, 'config.json'))
        # 4. Same directory as executable
        config_paths.append(os.path.join(exe_dir, 'config.json'))

        print(f"[INFO] Running as packaged exe from: {exe_dir}")
        print(f"[INFO] Bundle dir (_MEIPASS): {bundle_dir}")
    else:
        # Running in normal Python environment
        config_paths.append(os.path.join(os.path.dirname(__file__), '..', 'config.json'))
        print(f"[INFO] Running in development mode from: {os.path.dirname(__file__)}")

    # Try each path
    for config_file in config_paths:
        normalized_path = os.path.normpath(os.path.abspath(config_file))
        print(f"[INFO] Trying config path: {normalized_path}")

        if os.path.exists(normalized_path):
            try:
                with open(normalized_path, 'r') as f:
                    config = json.load(f)
                    db_config = config.get('database', {})
                    print(f"[OK] Loaded config from: {normalized_path}")
                    print(f"[INFO] MySQL connection: {db_config.get('user')}@{db_config.get('host')}:{db_config.get('port')}/{db_config.get('database')}")
                    return db_config
            except Exception as e:
                print(f"[WARNING] Error reading config from {normalized_path}: {e}")
                continue

    # Fallback to defaults
    print("[WARNING] No config.json found in any location, using default configuration")
    print(f"[WARNING] Searched paths: {config_paths}")
    return {
        'host': 'localhost',
        'port': 1396,
        'user': 'root',
        'password': 'root',
        'database': 'purchase_slips_db'
    }

# MySQL Configuration
DB_CONFIG = load_db_config()

# Global connection pool
connection_pool = None

def init_connection_pool():
    """
    Initialize MySQL connection pool using mysql.connector
    """
    global connection_pool
    try:
        # Force pure-Python implementation (prevents ACCESS_VIOLATION crashes)
        pool_config = DB_CONFIG.copy()
        pool_config['use_pure'] = True  # CRITICAL: Force pure-Python mode

        connection_pool = MySQLConnectionPool(
            pool_name="purchase_pool",
            pool_size=10,
            pool_reset_session=True,
            **pool_config
        )
        print("[OK] MySQL connection pool created successfully (size: 10, pure-Python mode)")
    except mysql.connector.Error as err:
        if err.errno == 1049:
            print("Database doesn't exist. Creating database...")
            create_database()
            connection_pool = MySQLConnectionPool(
                pool_name="purchase_pool",
                pool_size=10,
                pool_reset_session=True,
                **pool_config
            )
        else:
            print(f"[ERROR] Error creating connection pool: {err}")
            raise

def create_database():
    """Create the database if it doesn't exist"""
    conn = None
    cursor = None
    try:
        temp_config = DB_CONFIG.copy()
        database_name = temp_config.pop('database')
        temp_config['use_pure'] = True  # Force pure-Python mode

        conn = mysql.connector.connect(**temp_config)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        print(f"[OK] Database '{database_name}' created successfully")
    except mysql.connector.Error as err:
        print(f"[ERROR] Error creating database: {err}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_db_connection():
    """
    Get a database connection from the pool
    ALWAYS returns a connection with dictionary cursor support
    """
    global connection_pool
    if connection_pool is None:
        init_connection_pool()

    try:
        conn = connection_pool.get_connection()
        conn.ping(reconnect=True, attempts=3, delay=2)
        return conn
    except mysql.connector.Error as e:
        print(f"[ERROR] Error getting connection from pool: {e}")
        raise

def init_db():
    """
    Initialize the database and create tables if they don't exist
    """
    conn = None
    cursor = None
    try:
        init_connection_pool()

        print(f"[OK] Initializing database: {DB_CONFIG['database']}")
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Create purchase_slips table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_slips (
                id INT AUTO_INCREMENT PRIMARY KEY,
                company_name TEXT,
                company_address TEXT,
                document_type VARCHAR(255) DEFAULT 'Purchase Slip',
                vehicle_no VARCHAR(255),
                date DATETIME NOT NULL,
                bill_no INT NOT NULL,
                party_name TEXT,
                material_name TEXT,
                ticket_no VARCHAR(255),
                broker VARCHAR(255),
                terms_of_delivery TEXT,
                sup_inv_no VARCHAR(255),
                gst_no VARCHAR(255),
                bags DOUBLE DEFAULT 0,
                avg_bag_weight DOUBLE DEFAULT 0,
                net_weight DOUBLE DEFAULT 0,
                net_weight_kg DOUBLE DEFAULT 0,
                gunny_weight_kg DOUBLE DEFAULT 0,
                final_weight_kg DOUBLE DEFAULT 0,
                weight_quintal DOUBLE DEFAULT 0,
                weight_khandi DOUBLE DEFAULT 0,
                shortage_kg DOUBLE DEFAULT 0,
                rate DOUBLE DEFAULT 0,
                rate_basis VARCHAR(50) DEFAULT 'Quintal',
                rate_value DOUBLE DEFAULT 0,
                calculated_rate DOUBLE DEFAULT 0,
                total_purchase_amount DOUBLE DEFAULT 0,
                amount DOUBLE DEFAULT 0,
                bank_commission DOUBLE DEFAULT 0,
                postage DOUBLE DEFAULT 0,
                batav_percent DOUBLE DEFAULT 0,
                batav DOUBLE DEFAULT 0,
                shortage_percent DOUBLE DEFAULT 0,
                shortage DOUBLE DEFAULT 0,
                dalali_rate DOUBLE DEFAULT 0,
                dalali DOUBLE DEFAULT 0,
                hammali_rate DOUBLE DEFAULT 0,
                hammali DOUBLE DEFAULT 0,
                freight DOUBLE DEFAULT 0,
                rate_diff DOUBLE DEFAULT 0,
                quality_diff DOUBLE DEFAULT 0,
                quality_diff_comment TEXT,
                moisture_ded DOUBLE DEFAULT 0,
                moisture_ded_percent DOUBLE DEFAULT 0,
                tds DOUBLE DEFAULT 0,
                total_deduction DOUBLE DEFAULT 0,
                payable_amount DOUBLE DEFAULT 0,
                payment_method VARCHAR(255),
                payment_date DATETIME,
                payment_amount DOUBLE DEFAULT 0,
                payment_bank_account TEXT,
                payment_due_date DATETIME,
                payment_due_comment TEXT,
                instalment_1_date DATETIME,
                instalment_1_amount DOUBLE DEFAULT 0,
                instalment_1_comment TEXT,
                instalment_1_payment_method VARCHAR(255),
                instalment_1_payment_bank_account TEXT,
                instalment_2_date DATETIME,
                instalment_2_amount DOUBLE DEFAULT 0,
                instalment_2_comment TEXT,
                instalment_2_payment_method VARCHAR(255),
                instalment_2_payment_bank_account TEXT,
                instalment_3_date DATETIME,
                instalment_3_amount DOUBLE DEFAULT 0,
                instalment_3_comment TEXT,
                instalment_3_payment_method VARCHAR(255),
                instalment_3_payment_bank_account TEXT,
                instalment_4_date DATETIME,
                instalment_4_amount DOUBLE DEFAULT 0,
                instalment_4_comment TEXT,
                instalment_4_payment_method VARCHAR(255),
                instalment_4_payment_bank_account TEXT,
                instalment_5_date DATETIME,
                instalment_5_amount DOUBLE DEFAULT 0,
                instalment_5_comment TEXT,
                instalment_5_payment_method VARCHAR(255),
                instalment_5_payment_bank_account TEXT,
                prepared_by VARCHAR(255),
                authorised_sign VARCHAR(255),
                paddy_unloading_godown TEXT,
                INDEX idx_date (date),
                INDEX idx_party_name (party_name(255)),
                INDEX idx_bill_no (bill_no)
            )
        ''')

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL
            )
        ''')

        # Create unloading_godowns table for dynamic dropdown
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unloading_godowns (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("[OK] Table 'unloading_godowns' verified/created")

        # Check and add missing columns to purchase_slips
        cursor.execute("SHOW COLUMNS FROM purchase_slips")
        existing_columns = {row['Field'] for row in cursor.fetchall()}

        columns_to_add = {
            'shortage_kg': "DOUBLE DEFAULT 0",
            'rate_basis': "VARCHAR(50) DEFAULT 'Quintal'",
            'calculated_rate': "DOUBLE DEFAULT 0",
            'postage': "DOUBLE DEFAULT 0",
            'payment_due_comment': "TEXT",
            'payment_bank_account': "TEXT",
            'mobile_number': "VARCHAR(255)",
            'moisture_ded_comment': "TEXT",
            'moisture_percent': "DOUBLE DEFAULT 0",
            'moisture_kg': "DOUBLE DEFAULT 0",
            'company_gst_no': "VARCHAR(255)",
            'company_mobile_no': "VARCHAR(255)",
            'instalment_1_amount': "DOUBLE DEFAULT 0",
            'instalment_1_comment': "TEXT",
            'instalment_1_payment_method': "VARCHAR(255)",
            'instalment_1_payment_bank_account': "TEXT",
            'instalment_2_amount': "DOUBLE DEFAULT 0",
            'instalment_2_comment': "TEXT",
            'instalment_2_payment_method': "VARCHAR(255)",
            'instalment_2_payment_bank_account': "TEXT",
            'instalment_3_amount': "DOUBLE DEFAULT 0",
            'instalment_3_comment': "TEXT",
            'instalment_3_payment_method': "VARCHAR(255)",
            'instalment_3_payment_bank_account': "TEXT",
            'instalment_4_amount': "DOUBLE DEFAULT 0",
            'instalment_4_comment': "TEXT",
            'instalment_4_payment_method': "VARCHAR(255)",
            'instalment_4_payment_bank_account': "TEXT",
            'instalment_5_amount': "DOUBLE DEFAULT 0",
            'instalment_5_comment': "TEXT",
            'instalment_5_payment_method': "VARCHAR(255)",
            'instalment_5_payment_bank_account': "TEXT",
            'quality_diff_comment': "TEXT",
            'moisture_ded_percent': "DOUBLE DEFAULT 0",
            'prepared_by': "VARCHAR(255)",
            'authorised_sign': "VARCHAR(255)",
            'paddy_unloading_godown': "TEXT",
            'net_weight_kg': "DOUBLE DEFAULT 0",
            'gunny_weight_kg': "DOUBLE DEFAULT 0",
            'final_weight_kg': "DOUBLE DEFAULT 0",
            'weight_quintal': "DOUBLE DEFAULT 0",
            'weight_khandi': "DOUBLE DEFAULT 0",
            'rate_value': "DOUBLE DEFAULT 0",
            'total_purchase_amount': "DOUBLE DEFAULT 0"
        }

        # Convert date columns to DATETIME
        date_columns_to_convert = [
            'date', 'payment_date', 'payment_due_date',
            'instalment_1_date', 'instalment_2_date', 'instalment_3_date',
            'instalment_4_date', 'instalment_5_date'
        ]

        for col_name in date_columns_to_convert:
            if col_name in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE purchase_slips MODIFY COLUMN {col_name} DATETIME")
                    print(f"[OK] Converted column {col_name} to DATETIME")
                except mysql.connector.Error as err:
                    print(f"Warning: Could not convert column {col_name}: {err}")

        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE purchase_slips ADD COLUMN {col_name} {col_type}")
                    print(f"[OK] Added column: {col_name}")
                except mysql.connector.Error as err:
                    if err.errno != 1060:  # Ignore duplicate column error
                        print(f"Warning: Could not add column {col_name}: {err}")

        # Create default admin user if no users exist
        cursor.execute("SELECT COUNT(*) as count FROM users")
        result = cursor.fetchone()
        user_count = result['count']

        if user_count == 0:
            cursor.execute('''
                INSERT INTO users (username, password, full_name, role)
                VALUES (%s, %s, %s, %s)
            ''', ('admin', 'admin', 'Administrator', 'admin'))
            print("[OK] Default admin user created (username: admin, password: admin)")

        # Add default unloading godowns if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM unloading_godowns")
        result = cursor.fetchone()
        godown_count = result['count']

        if godown_count == 0:
            default_godowns = [
                'Godown A',
                'Godown B',
                'Main Warehouse',
                'Storage Unit 1'
            ]
            for godown in default_godowns:
                cursor.execute('INSERT IGNORE INTO unloading_godowns (name) VALUES (%s)', (godown,))
            print(f"[OK] Added {len(default_godowns)} default unloading godowns")

        conn.commit()
        print("[OK] Database tables initialized successfully")

    except mysql.connector.Error as err:
        print(f"[ERROR] Error initializing database: {err}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_next_bill_no():
    """
    Get the next bill number
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT MAX(bill_no) as max_bill FROM purchase_slips')
        result = cursor.fetchone()

        if result['max_bill'] is None:
            return 1
        return result['max_bill'] + 1

    except mysql.connector.Error as err:
        print(f"[ERROR] Error getting next bill number: {err}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
