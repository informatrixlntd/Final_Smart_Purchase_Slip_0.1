"""
Centralized PDF Generation Service using ReportLab
Fast, lightweight, no external dependencies
Includes disk caching for optimal performance
"""
import os
import sys
import hashlib
from io import BytesIO
from datetime import datetime

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import get_db_connection
from backend.routes.slips import format_ist_datetime, calculate_payment_totals

# Cache directory for generated PDFs
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'pdf_cache')
os.makedirs(CACHE_DIR, exist_ok=True)


def get_cache_key(slip_id, slip_data):
    """
    Generate cache key based on slip ID and last update timestamp
    Returns: cache_key (str), cache_path (str)
    """
    # Use updated_at or created_at timestamp as part of cache key
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
    Generate PDF for a purchase slip using ReportLab
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
        # Fetch slip data
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

        # Check cache
        cache_key, cache_path = get_cache_key(slip_id, slip)

        if not force_regenerate and os.path.exists(cache_path):
            # Return cached PDF
            print(f"[CACHE HIT] Returning cached PDF for slip {slip_id}")
            with open(cache_path, 'rb') as f:
                pdf_bytes = BytesIO(f.read())
            return pdf_bytes

        print(f"[CACHE MISS] Generating new PDF for slip {slip_id}")

        # Clear old cache files for this slip
        clear_old_cache_files(slip_id)

        # Generate PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )

        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#1a1a1a')
        )

        # Add logo if available
        try:
            logo_path = os.path.join(os.path.dirname(__file__), '..', 'desktop', 'assets', 'spslogo.png')
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=1.5*inch, height=1.5*inch)
                logo.hAlign = 'CENTER'
                elements.append(logo)
                elements.append(Spacer(1, 0.2*inch))
        except:
            pass

        # Title
        elements.append(Paragraph(slip.get('document_type', 'Purchase Slip'), title_style))
        elements.append(Spacer(1, 0.1*inch))

        # Company Details
        elements.append(Paragraph('Company Details', heading_style))
        company_data = [
            ['Company Name:', slip.get('company_name', '-')],
            ['Address:', slip.get('company_address', '-')],
            ['GST No:', slip.get('company_gst_no', '-')],
            ['Mobile:', slip.get('company_mobile_no', '-')]
        ]
        company_table = Table(company_data, colWidths=[2*inch, 4.5*inch])
        company_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a1a1a')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(company_table)
        elements.append(Spacer(1, 0.15*inch))

        # Slip Details
        elements.append(Paragraph('Slip Details', heading_style))

        # Format date
        date_formatted = format_ist_datetime(slip.get('date')) if slip.get('date') else '-'

        slip_data = [
            ['Bill No:', slip.get('bill_no', '-'), 'Date:', date_formatted],
            ['Vehicle No:', slip.get('vehicle_no', '-'), 'Ticket No:', slip.get('ticket_no', '-')],
            ['Party Name:', slip.get('party_name', '-'), 'Mobile:', slip.get('mobile_number', '-')],
            ['Material:', slip.get('material_name', '-'), 'Broker:', slip.get('broker', '-')],
        ]
        slip_table = Table(slip_data, colWidths=[1.3*inch, 2*inch, 1.3*inch, 2*inch])
        slip_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a1a1a')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(slip_table)
        elements.append(Spacer(1, 0.15*inch))

        # Weight Details
        elements.append(Paragraph('Weight Details', heading_style))
        weight_data = [
            ['Net Weight (KG):', f"{slip.get('net_weight_kg', 0):.2f}", 'Bags:', str(slip.get('bags', 0))],
            ['Gunny Weight (KG):', f"{slip.get('gunny_weight_kg', 0):.2f}", 'Avg Bag Weight:', f"{slip.get('avg_bag_weight', 0):.2f} KG"],
            ['Final Weight (KG):', f"{slip.get('final_weight_kg', 0):.2f}", 'Weight (Quintal):', f"{slip.get('weight_quintal', 0):.3f}"],
        ]
        weight_table = Table(weight_data, colWidths=[1.8*inch, 1.8*inch, 1.6*inch, 1.8*inch])
        weight_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a1a1a')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(weight_table)
        elements.append(Spacer(1, 0.15*inch))

        # Financial Details
        elements.append(Paragraph('Financial Details', heading_style))
        financial_data = [
            ['Rate Basis:', slip.get('rate_basis', 'Quintal'), 'Rate Value:', f"₹{slip.get('rate_value', 0):.2f}"],
            ['Total Purchase Amount:', f"₹{slip.get('total_purchase_amount', 0):.2f}", '', ''],
            ['Deductions:', '', '', ''],
            ['  Bank Commission:', f"₹{slip.get('bank_commission', 0):.2f}", '  Postage:', f"₹{slip.get('postage', 0):.2f}"],
            ['  Dalali:', f"₹{slip.get('dalali', 0):.2f}", '  Hammali:', f"₹{slip.get('hammali', 0):.2f}"],
            ['  Freight:', f"₹{slip.get('freight', 0):.2f}", '  TDS:', f"₹{slip.get('tds', 0):.2f}"],
            ['Total Deduction:', f"₹{slip.get('total_deduction', 0):.2f}", '', ''],
            ['Payable Amount:', f"₹{slip.get('payable_amount', 0):.2f}", '', ''],
        ]
        financial_table = Table(financial_data, colWidths=[1.8*inch, 1.8*inch, 1.6*inch, 1.8*inch])
        financial_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTNAME', (0, 7), (-1, 7), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a1a1a')),
            ('BACKGROUND', (0, 7), (-1, 7), colors.HexColor('#e8f5e9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(financial_table)
        elements.append(Spacer(1, 0.15*inch))

        # Payment Summary
        elements.append(Paragraph('Payment Summary', heading_style))
        payment_summary_data = [
            ['Payable Amount:', f"₹{slip.get('payable_amount', 0):.2f}"],
            ['Total Paid:', f"₹{total_paid:.2f}"],
            ['Balance:', f"₹{balance_amount:.2f}"]
        ]
        payment_summary_table = Table(payment_summary_data, colWidths=[2*inch, 4.5*inch])
        payment_summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1a1a1a')),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#fef3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(payment_summary_table)

        # Build PDF
        doc.build(elements)

        # Save to cache
        try:
            with open(cache_path, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            print(f"[OK] PDF cached at: {cache_path}")
        except Exception as e:
            print(f"[WARNING] Could not cache PDF: {e}")

        # Reset buffer position
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
