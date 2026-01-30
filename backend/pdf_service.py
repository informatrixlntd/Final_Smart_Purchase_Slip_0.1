"""
Centralized PDF Generation Service using xhtml2pdf
Fast HTML-to-PDF conversion with template support
Includes disk caching for optimal performance
Supports Marathi (Devanagari) text with embedded Unicode font
"""
import os
import sys
import hashlib
from io import BytesIO
from datetime import datetime
from xhtml2pdf import pisa
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_connection
from backend.routes.slips import format_ist_datetime, calculate_payment_totals

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'pdf_cache')
os.makedirs(CACHE_DIR, exist_ok=True)

FONT_PATH = os.path.join(os.path.dirname(__file__), 'static', 'fonts', 'NotoSansDevanagari-Regular.ttf')
FONT_REGISTERED = False


def register_devanagari_font():
    """
    Register Devanagari Unicode font with ReportLab
    MUST be called BEFORE pisa.CreatePDF for Marathi text support
    """
    global FONT_REGISTERED

    if FONT_REGISTERED:
        return

    try:
        if not os.path.exists(FONT_PATH):
            print(f"[WARNING] Font file not found: {FONT_PATH}")
            return

        pdfmetrics.registerFont(TTFont('NotoSansDevanagari', FONT_PATH))
        FONT_REGISTERED = True
        print(f"[OK] Devanagari font registered: {FONT_PATH}")
    except Exception as e:
        print(f"[ERROR] Failed to register Devanagari font: {e}")


def get_cache_key(slip_id, slip_data):
    """
    Generate cache key based on slip ID and last update timestamp
    Returns: cache_key (str), cache_path (str)
    """
    timestamp = slip_data.get('updated_at') or slip_data.get('created_at') or datetime.now()
    if isinstance(timestamp, datetime):
        timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
    else:
        timestamp_str = str(timestamp)

    cache_key = f"slip_{slip_id}_{timestamp_str}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    cache_filename = f"slip_{slip_id}_{cache_hash}.pdf"
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    return cache_key, cache_path


def clear_old_cache_files(slip_id):
    """Remove old cached PDF files for a specific slip"""
    try:
        for filename in os.listdir(CACHE_DIR):
            if filename.startswith(f"slip_{slip_id}_") and filename.endswith('.pdf'):
                file_path = os.path.join(CACHE_DIR, filename)
                try:
                    os.remove(file_path)
                except:
                    pass
    except:
        pass


def generate_purchase_slip_pdf(slip_id, force_regenerate=False):
    """
    Generate PDF for a purchase slip using xhtml2pdf with HTML template
    Includes intelligent caching for fast repeated access

    Args:
        slip_id (int): ID of the slip
        force_regenerate (bool): Force PDF regeneration even if cached

    Returns:
        BytesIO: PDF content as bytes
    """
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM purchase_slips WHERE id = %s', (slip_id,))
        slip = cursor.fetchone()

        if not slip:
            raise ValueError(f'Slip with ID {slip_id} not found')

        total_paid, balance_amount = calculate_payment_totals(slip)
        slip['total_paid_amount'] = total_paid
        slip['balance_amount'] = balance_amount

        slip['date_formatted'] = format_ist_datetime(slip.get('date')) if slip.get('date') else '-'

        cache_key, cache_path = get_cache_key(slip_id, slip)

        if not force_regenerate and os.path.exists(cache_path):
            print(f"[CACHE HIT] Returning cached PDF for slip {slip_id}")
            with open(cache_path, 'rb') as f:
                pdf_bytes = BytesIO(f.read())
            return pdf_bytes

        print(f"[CACHE MISS] Generating new PDF for slip {slip_id}")

        clear_old_cache_files(slip_id)

        register_devanagari_font()

        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'print_template_new.html')

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        html_content = render_template_string(template_content, slip=slip)

        html_bytes = html_content.encode('utf-8')

        pdf_buffer = BytesIO()

        pisa_status = pisa.CreatePDF(
            html_bytes,
            dest=pdf_buffer,
            encoding='utf-8'
        )

        if pisa_status.err:
            raise Exception(f'PDF generation failed with error code: {pisa_status.err}')

        try:
            with open(cache_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            print(f"[OK] PDF cached at: {cache_path}")
        except Exception as e:
            print(f"[WARNING] Could not cache PDF: {e}")

        pdf_buffer.seek(0)
        return pdf_buffer

    except Exception as e:
        print(f"[ERROR] Error generating PDF for slip {slip_id}: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def render_template_string(template_content, **context):
    """
    Simple template renderer using Jinja2-like syntax
    Replaces {{ variable }} with actual values
    """
    from jinja2 import Template
    template = Template(template_content)
    return template.render(**context)


def get_pdf_filename(slip_data):
    """Generate standardized PDF filename"""
    party_name = slip_data.get('party_name', 'Unknown')
    bill_no = slip_data.get('bill_no', 'XXXX')

    party_name_safe = "".join(c for c in party_name if c.isalnum() or c in (' ', '_', '-')).strip()
    party_name_safe = party_name_safe.replace(' ', '_')

    return f"Purchase_Slip_{party_name_safe}_{bill_no}.pdf"


def invalidate_cache(slip_id):
    """Invalidate cached PDF for a slip (call after update)"""
    clear_old_cache_files(slip_id)
    print(f"[OK] Cache invalidated for slip {slip_id}")
