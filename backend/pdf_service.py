"""
Centralized PDF Generation Service
Single source of truth for all PDF generation using WeasyPrint
"""
import os
import sys
import tempfile
from flask import render_template
from weasyprint import HTML, CSS
from io import BytesIO

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_connection
from backend.routes.slips import format_ist_datetime, calculate_payment_totals


def generate_purchase_slip_pdf(slip_id, output_path=None):
    """
    Generate PDF for a purchase slip

    Args:
        slip_id (int): ID of the slip to generate PDF for
        output_path (str, optional): Path to save PDF file. If None, returns BytesIO object

    Returns:
        BytesIO or str: PDF content as BytesIO or path to saved file

    Raises:
        ValueError: If slip not found
        Exception: For database or PDF generation errors
    """
    conn = None
    cursor = None

    try:
        # Fetch slip data from database
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM purchase_slips WHERE id = %s', (slip_id,))
        slip = cursor.fetchone()

        if not slip:
            raise ValueError(f'Slip with ID {slip_id} not found')

        # Calculate payment totals
        total_paid, balance_amount = calculate_payment_totals(slip)
        slip['total_paid_amount'] = total_paid
        slip['balance_amount'] = balance_amount

        # Format datetime fields for display
        datetime_fields = ['date', 'instalment_1_date', 'instalment_2_date',
                          'instalment_3_date', 'instalment_4_date', 'instalment_5_date']

        for field in datetime_fields:
            if slip.get(field):
                slip[f'{field}_formatted'] = format_ist_datetime(slip[field])

        # Get template path (works in both dev and packaged mode)
        if getattr(sys, 'frozen', False):
            template_folder = os.path.join(sys._MEIPASS, 'templates')
        else:
            template_folder = os.path.join(os.path.dirname(__file__), 'templates')

        # Get logo path for embedding
        if getattr(sys, 'frozen', False):
            logo_path = os.path.join(sys._MEIPASS, 'desktop', 'assets', 'spslogo.png')
        else:
            logo_path = os.path.join(os.path.dirname(__file__), '..', 'desktop', 'assets', 'spslogo.png')

        logo_path = os.path.abspath(logo_path)

        # Render HTML template (ONLY use print_template_new.html)
        template_path = os.path.join(template_folder, 'print_template_new.html')

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Manual template rendering (simple replacement)
        html_content = _render_template(template_content, slip, logo_path)

        # Generate PDF using WeasyPrint
        pdf_options = {
            'presentational_hints': True,
            'optimize_size': ('fonts',)
        }

        html_doc = HTML(string=html_content, base_url=template_folder)

        if output_path:
            # Save to file
            html_doc.write_pdf(output_path, **pdf_options)
            print(f"[OK] PDF generated successfully: {output_path}")
            return output_path
        else:
            # Return as BytesIO
            pdf_bytes = BytesIO()
            html_doc.write_pdf(pdf_bytes, **pdf_options)
            pdf_bytes.seek(0)
            print(f"[OK] PDF generated successfully for slip ID {slip_id}")
            return pdf_bytes

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


def _render_template(template_content, slip, logo_path):
    """
    Simple template rendering (replaces Jinja2 variables)
    This is a simplified version - in production, use Flask's render_template
    """
    # For now, use Flask's render_template directly
    from flask import Flask
    app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)) + '/templates')

    with app.app_context():
        html = render_template('print_template_new.html', slip=slip, logo_path=logo_path)

    return html


def get_pdf_filename(slip_data):
    """
    Generate standardized PDF filename
    Format: Purchase_Slip_<PartyName>_<BillNo>.pdf
    """
    party_name = slip_data.get('party_name', 'Unknown')
    bill_no = slip_data.get('bill_no', 'XXXX')

    # Sanitize filename (remove invalid characters)
    party_name_safe = "".join(c for c in party_name if c.isalnum() or c in (' ', '_', '-')).strip()
    party_name_safe = party_name_safe.replace(' ', '_')

    return f"Purchase_Slip_{party_name_safe}_{bill_no}.pdf"


# Quick test function
if __name__ == '__main__':
    print("Testing PDF generation service...")
    try:
        pdf_bytes = generate_purchase_slip_pdf(1)
        print(f"Success! Generated PDF size: {len(pdf_bytes.getvalue())} bytes")
    except Exception as e:
        print(f"Test failed: {e}")
