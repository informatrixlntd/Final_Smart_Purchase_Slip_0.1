"""
Centralized PDF Generation Service using Playwright (Chromium)
Native HTML-to-PDF conversion with full Unicode/Marathi (Devanagari) support
Zero dependencies on xhtml2pdf or ReportLab - uses browser engine for rendering

ARCHITECTURE:
- Playwright (Chromium) handles PDF generation via headless browser
- Async Playwright API wrapped in sync functions for Flask compatibility
- No temporary files - PDF generated in-memory and streamed to browser
- Fonts loaded via CSS @font-face in HTML template
- Chromium's HarfBuzz engine handles complex text shaping (Devanagari)

REQUIREMENTS:
- pip install playwright
- playwright install chromium
"""
import os
import asyncio
from io import BytesIO
from datetime import datetime
from pytz import timezone
from jinja2 import Template

from backend.database import get_db_connection


def safe_float(value, default=0.0):
    """Safely convert value to float, return default if conversion fails"""
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def format_ist_datetime(dt):
    """
    Format datetime to IST display format DD-MM-YYYY HH:MM
    Handles None, string ISO dates, and datetime objects
    """
    if dt is None:
        return None

    ist = timezone('Asia/Kolkata')

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d')
            except:
                return dt

    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = ist.localize(dt)
        else:
            dt = dt.astimezone(ist)
        return dt.strftime('%d-%m-%Y %H:%M')

    return str(dt)


def calculate_payment_totals(data):
    """
    Calculate Total Paid Amount and Balance Amount
    Total Paid = Sum of all 5 instalment amounts
    Balance = Payable Amount - Total Paid

    Args:
        data (dict): Slip data dictionary

    Returns:
        tuple: (total_paid, balance_amount)
    """
    payable_amount = safe_float(data.get('payable_amount', 0), 0)

    total_paid = 0.0
    for i in range(1, 6):
        instalment_amount = safe_float(data.get(f'instalment_{i}_amount', 0), 0)
        total_paid += instalment_amount

    total_paid = round(total_paid, 2)
    balance_amount = round(payable_amount - total_paid, 2)

    return total_paid, balance_amount


def get_pdf_filename(slip_data):
    """
    Generate standardized PDF filename from slip data
    Format: Purchase_Slip_PartyName_BillNo.pdf
    """
    party_name = slip_data.get('party_name', 'Unknown')
    bill_no = slip_data.get('bill_no', 'XXXX')

    party_name_safe = "".join(c for c in party_name if c.isalnum() or c in (' ', '_', '-')).strip()
    party_name_safe = party_name_safe.replace(' ', '_')

    return f"Purchase_Slip_{party_name_safe}_{bill_no}.pdf"


async def _generate_pdf_async(html_content):
    """
    Internal async function to generate PDF using Playwright
    Launches Chromium browser, renders HTML, generates PDF in-memory

    Args:
        html_content (str): Rendered HTML content

    Returns:
        bytes: PDF content as bytes
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage', '--no-sandbox']
        )

        try:
            page = await browser.new_page()

            await page.set_content(html_content, wait_until='networkidle')

            pdf_bytes = await page.pdf(
                format='A4',
                print_background=True,
                margin={
                    'top': '10mm',
                    'right': '10mm',
                    'bottom': '10mm',
                    'left': '10mm'
                },
                prefer_css_page_size=True
            )

            return pdf_bytes

        finally:
            await browser.close()


def generate_purchase_slip_pdf(slip_id, force_regenerate=False):
    """
    Generate PDF for a purchase slip using Playwright/Chromium
    Main entry point for PDF generation - called by Flask routes

    WORKFLOW:
    1. Fetch slip data from database
    2. Calculate payment totals and format dates
    3. Render HTML template with slip data
    4. Launch Chromium via Playwright
    5. Generate PDF from HTML (in-memory)
    6. Return PDF as BytesIO stream

    Args:
        slip_id (int): ID of the slip to generate PDF for
        force_regenerate (bool): Ignored (kept for API compatibility)

    Returns:
        BytesIO: PDF content as bytes stream

    Raises:
        ValueError: If slip not found
        Exception: If PDF generation fails
    """
    conn = None
    cursor = None

    try:
        print(f"[INFO] Generating PDF for slip ID: {slip_id}")

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

        for i in range(1, 6):
            date_key = f'instalment_{i}_date'
            if slip.get(date_key):
                slip[f'instalment_{i}_date_formatted'] = format_ist_datetime(slip[date_key])

        template_path = os.path.join(
            os.path.dirname(__file__),
            'templates',
            'print_template_new.html'
        )

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        template = Template(template_content)
        html_content = template.render(slip=slip)

        print(f"[OK] HTML template rendered successfully")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            pdf_bytes = loop.run_until_complete(_generate_pdf_async(html_content))
        finally:
            loop.close()

        print(f"[OK] PDF generated successfully ({len(pdf_bytes)} bytes)")

        pdf_buffer = BytesIO(pdf_bytes)
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


def invalidate_cache(slip_id):
    """
    Cache invalidation stub - kept for API compatibility
    Playwright generates PDFs on-demand, no caching needed
    """
    print(f"[INFO] Cache invalidation called for slip {slip_id} (no-op with Playwright)")
    pass
