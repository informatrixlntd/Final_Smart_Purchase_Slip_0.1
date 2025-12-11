from flask import Blueprint, request, jsonify, render_template, send_file
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_connection, get_next_bill_no
from datetime import datetime
from pytz import timezone

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    print("Warning: pdfkit not available. PDF generation will be disabled.")

slips_bp = Blueprint('slips', __name__)

def safe_float(value, default=0.0):
    """Safely convert value to float, handling empty strings and None"""
    try:
        if value in (None, '', ' '):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def get_ist_datetime():
    """Get current datetime in IST timezone"""
    ist = timezone('Asia/Kolkata')
    return datetime.now(ist)

def parse_datetime_to_ist(value):
    """Parse date/datetime string and convert to IST datetime object"""
    if value in (None, '', ' '):
        return None

    ist = timezone('Asia/Kolkata')

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return ist.localize(value)
        return value.astimezone(ist)

    if isinstance(value, str):
        try:
            if 'T' in value or ' ' in value:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(value, '%Y-%m-%d')
                dt = dt.replace(hour=0, minute=0, second=0)

            if dt.tzinfo is None:
                dt = ist.localize(dt)
            else:
                dt = dt.astimezone(ist)

            return dt.replace(tzinfo=None)
        except:
            return None

    return None

def format_ist_datetime(dt):
    """Format datetime to IST display format DD-MM-YYYY HH:MM"""
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

    return None


def calculate_payment_totals(data):
    """
    Calculate Total Paid Amount and Balance Amount dynamically
    Total Paid = Sum of all instalment amounts
    Balance = Payable Amount - Total Paid
    """
    payable_amount = safe_float(data.get('payable_amount', 0), 0)

    # Sum all instalment amounts
    total_paid = 0.0
    for i in range(1, 6):
        instalment_amount = safe_float(data.get(f'instalment_{i}_amount', 0), 0)
        total_paid += instalment_amount

    total_paid = round(total_paid, 2)
    balance_amount = round(payable_amount - total_paid, 2)

    return total_paid, balance_amount


def calculate_fields(data):
    """Calculate all computed fields with NEW weight & rate system"""
    net_weight_kg = safe_float(data.get('net_weight_kg', 0), 0)
    gunny_weight_kg = safe_float(data.get('gunny_weight_kg', 0), 0)
    bags = safe_float(data.get('bags', 0), 0)
    rate_basis = data.get('rate_basis', 'Quintal')
    rate_value = safe_float(data.get('rate_value', 0), 0)

    bank_commission = safe_float(data.get('bank_commission', 0), 0)
    postage = safe_float(data.get('postage', 0), 0)
    freight = safe_float(data.get('freight', 0), 0)
    rate_diff = safe_float(data.get('rate_diff', 0), 0)
    quality_diff = safe_float(data.get('quality_diff', 0), 0)
    moisture_ded = safe_float(data.get('moisture_ded', 0), 0)
    tds = safe_float(data.get('tds', 0), 0)
    batav_percent = safe_float(data.get('batav_percent', 0), 0)
    shortage_percent = safe_float(data.get('shortage_percent', 0), 0)
    dalali_rate = safe_float(data.get('dalali_rate', 0), 0)
    hammali_rate = safe_float(data.get('hammali_rate', 0), 0)

    final_weight_kg = round(max(0, net_weight_kg - gunny_weight_kg), 2)
    weight_quintal = round(final_weight_kg / 100, 3)
    weight_khandi = round(final_weight_kg / 150, 3)
    avg_bag_weight = round(final_weight_kg / bags, 2) if bags > 0 else 0

    if rate_basis == 'Quintal':
        total_purchase_amount = round(weight_quintal * rate_value, 2)
    elif rate_basis == 'Khandi':
        total_purchase_amount = round(weight_khandi * rate_value, 2)
    else:
        total_purchase_amount = 0

    batav = round(total_purchase_amount * (batav_percent / 100), 2) if batav_percent > 0 else 0
    shortage = round(total_purchase_amount * (shortage_percent / 100), 2) if shortage_percent > 0 else 0

    # NEW CALCULATION: Dalali & Hamali based on Net Weight KG / 100
    dalali = round((net_weight_kg / 100) * dalali_rate, 2) if dalali_rate > 0 else 0
    hammali = round((net_weight_kg / 100) * hammali_rate, 2) if hammali_rate > 0 else 0

    total_deduction = round(bank_commission + postage + batav + shortage + dalali + hammali + freight + rate_diff + quality_diff + moisture_ded + tds, 2)
    payable_amount = round(total_purchase_amount - total_deduction, 2)

    data.update({
        'net_weight_kg': net_weight_kg,
        'gunny_weight_kg': gunny_weight_kg,
        'final_weight_kg': final_weight_kg,
        'weight_quintal': weight_quintal,
        'weight_khandi': weight_khandi,
        'avg_bag_weight': avg_bag_weight,
        'rate_basis': rate_basis,
        'rate_value': rate_value,
        'total_purchase_amount': total_purchase_amount,
        'batav': batav,
        'shortage': shortage,
        'dalali': dalali,
        'hammali': hammali,
        'freight': freight,
        'rate_diff': rate_diff,
        'quality_diff': quality_diff,
        'moisture_ded': moisture_ded,
        'tds': tds,
        'postage': postage,
        'total_deduction': total_deduction,
        'payable_amount': payable_amount
    })
    return data

@slips_bp.route('/api/add-slip', methods=['POST'])
def add_slip():
    """Add a new purchase slip with structured instalments"""
    conn = None
    cursor = None
    try:
        data = request.json
        print("📝 Incoming slip data:", {k: v for k, v in data.items() if k in ['party_name', 'date', 'bags', 'net_weight_kg']})
        data = calculate_fields(data)

        bill_no = get_next_bill_no()

        conn = get_db_connection()
        cursor = conn.cursor()

        slip_date = parse_datetime_to_ist(data.get('date')) or get_ist_datetime()

        print(f"✓ Calculated fields: payable={data.get('payable_amount')}, total_purchase={data.get('total_purchase_amount')}")

        cursor.execute('''
            INSERT INTO purchase_slips (
                company_name, company_address, company_gst_no, company_mobile_no, document_type, vehicle_no, date,
                bill_no, party_name, mobile_number, material_name, ticket_no, broker,
                terms_of_delivery, sup_inv_no, gst_no,
                bags, avg_bag_weight,
                net_weight_kg, gunny_weight_kg, final_weight_kg,
                weight_quintal, weight_khandi,
                rate_basis, rate_value, total_purchase_amount,
                bank_commission, postage, batav_percent, batav,
                shortage_percent, shortage, dalali_rate, dalali, hammali_rate,
                hammali, freight, rate_diff, quality_diff, quality_diff_comment,
                moisture_ded, moisture_ded_comment, moisture_percent, moisture_kg, tds, total_deduction, payable_amount,
                instalment_1_date, instalment_1_amount, instalment_1_payment_method, instalment_1_payment_bank_account, instalment_1_comment,
                instalment_2_date, instalment_2_amount, instalment_2_payment_method, instalment_2_payment_bank_account, instalment_2_comment,
                instalment_3_date, instalment_3_amount, instalment_3_payment_method, instalment_3_payment_bank_account, instalment_3_comment,
                instalment_4_date, instalment_4_amount, instalment_4_payment_method, instalment_4_payment_bank_account, instalment_4_comment,
                instalment_5_date, instalment_5_amount, instalment_5_payment_method, instalment_5_payment_bank_account, instalment_5_comment,
                prepared_by, authorised_sign, paddy_unloading_godown
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            data.get('company_name', ''),
            data.get('company_address', ''),
            data.get('company_gst_no', ''),
            data.get('company_mobile_no', ''),
            data.get('document_type', 'Purchase Slip'),
            data.get('vehicle_no', ''),
            slip_date,
            bill_no,
            data.get('party_name', ''),
            data.get('mobile_number', ''),
            data.get('material_name', ''),
            data.get('ticket_no', ''),
            data.get('broker', ''),
            data.get('terms_of_delivery', ''),
            data.get('sup_inv_no', ''),
            data.get('gst_no', ''),
            safe_float(data.get('bags', 0), 0),
            safe_float(data.get('avg_bag_weight', 0), 0),
            safe_float(data.get('net_weight_kg', 0), 0),
            safe_float(data.get('gunny_weight_kg', 0), 0),
            safe_float(data.get('final_weight_kg', 0), 0),
            safe_float(data.get('weight_quintal', 0), 0),
            safe_float(data.get('weight_khandi', 0), 0),
            data.get('rate_basis', 'Quintal'),
            safe_float(data.get('rate_value', 0), 0),
            safe_float(data.get('total_purchase_amount', 0), 0),
            safe_float(data.get('bank_commission', 0), 0),
            safe_float(data.get('postage', 0), 0),
            safe_float(data.get('batav_percent', 0), 0),
            safe_float(data.get('batav', 0), 0),
            safe_float(data.get('shortage_percent', 0), 0),
            safe_float(data.get('shortage', 0), 0),
            safe_float(data.get('dalali_rate', 0), 0),
            safe_float(data.get('dalali', 0), 0),
            safe_float(data.get('hammali_rate', 0), 0),
            safe_float(data.get('hammali', 0), 0),
            safe_float(data.get('freight', 0), 0),
            safe_float(data.get('rate_diff', 0), 0),
            safe_float(data.get('quality_diff', 0), 0),
            data.get('quality_diff_comment', ''),
            safe_float(data.get('moisture_ded', 0), 0),
            data.get('moisture_ded_comment', ''),
            safe_float(data.get('moisture_percent', 0), 0),
            safe_float(data.get('moisture_kg', 0), 0),
            safe_float(data.get('tds', 0), 0),
            safe_float(data.get('total_deduction', 0), 0),
            safe_float(data.get('payable_amount', 0), 0),
            # Instalment 1
            parse_datetime_to_ist(data.get('instalment_1_date')),
            safe_float(data.get('instalment_1_amount', 0), 0),
            data.get('instalment_1_payment_method', ''),
            data.get('instalment_1_payment_bank_account', ''),
            data.get('instalment_1_comment', ''),
            # Instalment 2
            parse_datetime_to_ist(data.get('instalment_2_date')),
            safe_float(data.get('instalment_2_amount', 0), 0),
            data.get('instalment_2_payment_method', ''),
            data.get('instalment_2_payment_bank_account', ''),
            data.get('instalment_2_comment', ''),
            # Instalment 3
            parse_datetime_to_ist(data.get('instalment_3_date')),
            safe_float(data.get('instalment_3_amount', 0), 0),
            data.get('instalment_3_payment_method', ''),
            data.get('instalment_3_payment_bank_account', ''),
            data.get('instalment_3_comment', ''),
            # Instalment 4
            parse_datetime_to_ist(data.get('instalment_4_date')),
            safe_float(data.get('instalment_4_amount', 0), 0),
            data.get('instalment_4_payment_method', ''),
            data.get('instalment_4_payment_bank_account', ''),
            data.get('instalment_4_comment', ''),
            # Instalment 5
            parse_datetime_to_ist(data.get('instalment_5_date')),
            safe_float(data.get('instalment_5_amount', 0), 0),
            data.get('instalment_5_payment_method', ''),
            data.get('instalment_5_payment_bank_account', ''),
            data.get('instalment_5_comment', ''),
            data.get('prepared_by', ''),
            data.get('authorised_sign', ''),
            data.get('paddy_unloading_godown', '')
        ))

        slip_id = cursor.lastrowid
        conn.commit()

        print(f"✅ Slip saved successfully: ID={slip_id}, Bill No={bill_no}")

        return jsonify({
            'success': True,
            'message': 'Purchase slip saved successfully',
            'slip_id': slip_id,
            'bill_no': bill_no
        }), 201

    except Exception as e:
        print(f"❌ Error adding slip: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@slips_bp.route('/api/slips', methods=['GET'])
def get_slips():
    """Get all purchase slips with calculated Total Paid and Balance - optimized for list view"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit

        cursor.execute('''
            SELECT id, bill_no, date, party_name, mobile_number, final_weight_kg, rate_basis,
                   payable_amount, instalment_1_amount, instalment_2_amount,
                   instalment_3_amount, instalment_4_amount, instalment_5_amount
            FROM purchase_slips
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        ''', (limit, offset))
        slips = cursor.fetchall()

        cursor.execute('SELECT COUNT(*) as total FROM purchase_slips')
        total_count = cursor.fetchone()['total']

        for slip in slips:
            total_paid, balance_amount = calculate_payment_totals(slip)
            slip['total_paid_amount'] = total_paid
            slip['balance_amount'] = balance_amount

            if slip.get('date'):
                slip['date'] = format_ist_datetime(slip['date'])

        return jsonify({
            'success': True,
            'slips': slips,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        }), 200

    except Exception as e:
        print(f"Error fetching slips: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@slips_bp.route('/api/slip/<int:slip_id>', methods=['GET'])
def get_slip(slip_id):
    """Get a single purchase slip by ID with calculated amounts"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM purchase_slips WHERE id = %s', (slip_id,))
        slip = cursor.fetchone()

        if slip is None:
            return jsonify({
                'success': False,
                'message': 'Slip not found'
            }), 404

        # Calculate Total Paid and Balance
        total_paid, balance_amount = calculate_payment_totals(slip)
        slip['total_paid_amount'] = total_paid
        slip['balance_amount'] = balance_amount

        # Format all datetime fields to IST
        datetime_fields = ['date', 'payment_date', 'payment_due_date',
                          'instalment_1_date', 'instalment_2_date', 'instalment_3_date',
                          'instalment_4_date', 'instalment_5_date']

        for field in datetime_fields:
            if slip.get(field):
                slip[field] = format_ist_datetime(slip[field])

        return jsonify({
            'success': True,
            'slip': slip
        }), 200

    except Exception as e:
        print(f"Error fetching slip: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@slips_bp.route('/api/slip/<int:slip_id>', methods=['PUT'])
def update_slip(slip_id):
    """Update a purchase slip with structured instalments"""
    conn = None
    cursor = None
    try:
        data = request.json

        # Get existing slip and merge with new data
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM purchase_slips WHERE id = %s', (slip_id,))
        existing_slip = cursor.fetchone()
        cursor.close()

        if existing_slip:
            merged_data = dict(existing_slip)
            merged_data.update(data)
            merged_data = calculate_fields(merged_data)
        else:
            merged_data = calculate_fields(data)

        cursor = conn.cursor()

        cursor.execute('''
            UPDATE purchase_slips SET
                company_name = %s, company_address = %s, company_gst_no = %s, company_mobile_no = %s, document_type = %s,
                vehicle_no = %s, date = %s,
                party_name = %s, mobile_number = %s, material_name = %s, ticket_no = %s, broker = %s,
                terms_of_delivery = %s, sup_inv_no = %s, gst_no = %s,
                bags = %s, avg_bag_weight = %s,
                net_weight_kg = %s, gunny_weight_kg = %s, final_weight_kg = %s,
                weight_quintal = %s, weight_khandi = %s,
                rate_basis = %s, rate_value = %s, total_purchase_amount = %s,
                bank_commission = %s, postage = %s, batav_percent = %s, batav = %s,
                shortage_percent = %s, shortage = %s, dalali_rate = %s, dalali = %s,
                hammali_rate = %s, hammali = %s, freight = %s, rate_diff = %s,
                quality_diff = %s, quality_diff_comment = %s, moisture_ded = %s, moisture_ded_comment = %s,
                moisture_percent = %s, moisture_kg = %s, tds = %s, total_deduction = %s, payable_amount = %s,
                instalment_1_date = %s, instalment_1_amount = %s, instalment_1_payment_method = %s, instalment_1_payment_bank_account = %s, instalment_1_comment = %s,
                instalment_2_date = %s, instalment_2_amount = %s, instalment_2_payment_method = %s, instalment_2_payment_bank_account = %s, instalment_2_comment = %s,
                instalment_3_date = %s, instalment_3_amount = %s, instalment_3_payment_method = %s, instalment_3_payment_bank_account = %s, instalment_3_comment = %s,
                instalment_4_date = %s, instalment_4_amount = %s, instalment_4_payment_method = %s, instalment_4_payment_bank_account = %s, instalment_4_comment = %s,
                instalment_5_date = %s, instalment_5_amount = %s, instalment_5_payment_method = %s, instalment_5_payment_bank_account = %s, instalment_5_comment = %s,
                prepared_by = %s, authorised_sign = %s, paddy_unloading_godown = %s
            WHERE id = %s
        ''', (
            merged_data.get('company_name', ''),
            merged_data.get('company_address', ''),
            merged_data.get('company_gst_no', ''),
            merged_data.get('company_mobile_no', ''),
            merged_data.get('document_type', 'Purchase Slip'),
            merged_data.get('vehicle_no', ''),
            parse_datetime_to_ist(merged_data.get('date')),
            merged_data.get('party_name', ''),
            merged_data.get('mobile_number', ''),
            merged_data.get('material_name', ''),
            merged_data.get('ticket_no', ''),
            merged_data.get('broker', ''),
            merged_data.get('terms_of_delivery', ''),
            merged_data.get('sup_inv_no', ''),
            merged_data.get('gst_no', ''),
            safe_float(merged_data.get('bags', 0), 0),
            safe_float(merged_data.get('avg_bag_weight', 0), 0),
            safe_float(merged_data.get('net_weight_kg', 0), 0),
            safe_float(merged_data.get('gunny_weight_kg', 0), 0),
            safe_float(merged_data.get('final_weight_kg', 0), 0),
            safe_float(merged_data.get('weight_quintal', 0), 0),
            safe_float(merged_data.get('weight_khandi', 0), 0),
            merged_data.get('rate_basis', 'Quintal'),
            safe_float(merged_data.get('rate_value', 0), 0),
            safe_float(merged_data.get('total_purchase_amount', 0), 0),
            safe_float(merged_data.get('bank_commission', 0), 0),
            safe_float(merged_data.get('postage', 0), 0),
            safe_float(merged_data.get('batav_percent', 0), 0),
            safe_float(merged_data.get('batav', 0), 0),
            safe_float(merged_data.get('shortage_percent', 0), 0),
            safe_float(merged_data.get('shortage', 0), 0),
            safe_float(merged_data.get('dalali_rate', 0), 0),
            safe_float(merged_data.get('dalali', 0), 0),
            safe_float(merged_data.get('hammali_rate', 0), 0),
            safe_float(merged_data.get('hammali', 0), 0),
            safe_float(merged_data.get('freight', 0), 0),
            safe_float(merged_data.get('rate_diff', 0), 0),
            safe_float(merged_data.get('quality_diff', 0), 0),
            merged_data.get('quality_diff_comment', ''),
            safe_float(merged_data.get('moisture_ded', 0), 0),
            merged_data.get('moisture_ded_comment', ''),
            safe_float(merged_data.get('moisture_percent', 0), 0),
            safe_float(merged_data.get('moisture_kg', 0), 0),
            safe_float(merged_data.get('tds', 0), 0),
            safe_float(merged_data.get('total_deduction', 0), 0),
            safe_float(merged_data.get('payable_amount', 0), 0),
            # Instalment 1
            parse_datetime_to_ist(merged_data.get('instalment_1_date')),
            safe_float(merged_data.get('instalment_1_amount', 0), 0),
            merged_data.get('instalment_1_payment_method', ''),
            merged_data.get('instalment_1_payment_bank_account', ''),
            merged_data.get('instalment_1_comment', ''),
            # Instalment 2
            parse_datetime_to_ist(merged_data.get('instalment_2_date')),
            safe_float(merged_data.get('instalment_2_amount', 0), 0),
            merged_data.get('instalment_2_payment_method', ''),
            merged_data.get('instalment_2_payment_bank_account', ''),
            merged_data.get('instalment_2_comment', ''),
            # Instalment 3
            parse_datetime_to_ist(merged_data.get('instalment_3_date')),
            safe_float(merged_data.get('instalment_3_amount', 0), 0),
            merged_data.get('instalment_3_payment_method', ''),
            merged_data.get('instalment_3_payment_bank_account', ''),
            merged_data.get('instalment_3_comment', ''),
            # Instalment 4
            parse_datetime_to_ist(merged_data.get('instalment_4_date')),
            safe_float(merged_data.get('instalment_4_amount', 0), 0),
            merged_data.get('instalment_4_payment_method', ''),
            merged_data.get('instalment_4_payment_bank_account', ''),
            merged_data.get('instalment_4_comment', ''),
            # Instalment 5
            parse_datetime_to_ist(merged_data.get('instalment_5_date')),
            safe_float(merged_data.get('instalment_5_amount', 0), 0),
            merged_data.get('instalment_5_payment_method', ''),
            merged_data.get('instalment_5_payment_bank_account', ''),
            merged_data.get('instalment_5_comment', ''),
            merged_data.get('prepared_by', ''),
            merged_data.get('authorised_sign', ''),
            merged_data.get('paddy_unloading_godown', ''),
            slip_id
        ))

        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Purchase slip updated successfully',
            'slip_id': slip_id
        }), 200

    except Exception as e:
        print(f"Error updating slip: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@slips_bp.route('/api/slip/<int:slip_id>', methods=['DELETE'])
def delete_slip(slip_id):
    """Delete a purchase slip"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM purchase_slips WHERE id = %s', (slip_id,))
        conn.commit()

        return jsonify({
            'success': True,
            'message': 'Slip deleted successfully'
        }), 200

    except Exception as e:
        print(f"Error deleting slip: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@slips_bp.route('/api/slip/<int:slip_id>/pdf', methods=['GET'])
def generate_slip_pdf(slip_id):
    """Generate PDF for a purchase slip"""
    if not PDFKIT_AVAILABLE:
        return jsonify({
            'success': False,
            'message': 'PDF generation is not available. Please install wkhtmltopdf.'
        }), 500

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM purchase_slips WHERE id = %s', (slip_id,))
        slip = cursor.fetchone()

        if not slip:
            return jsonify({'success': False, 'message': 'Slip not found'}), 404

        # Format datetime fields
        datetime_fields = ['date', 'instalment_1_date', 'instalment_2_date',
                          'instalment_3_date', 'instalment_4_date', 'instalment_5_date']
        for field in datetime_fields:
            if slip.get(field):
                slip[f'{field}_formatted'] = format_ist_datetime(slip[field])

        # Render HTML
        html_content = render_template('print_template.html', slip=slip)

        # Generate PDF
        pdf_options = {
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-right': '10mm',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None
        }

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            pdfkit.from_string(html_content, temp_pdf.name, options=pdf_options)
            temp_pdf_path = temp_pdf.name

        # Send file and schedule cleanup
        response = send_file(
            temp_pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'purchase_slip_{slip_id}.pdf'
        )

        # Schedule temp file cleanup after response
        @response.call_on_close
        def cleanup():
            try:
                if os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)
            except:
                pass

        return response

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@slips_bp.route('/print/<int:slip_id>')
def print_slip(slip_id):
    """Render print template for a slip with calculated amounts"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('SELECT * FROM purchase_slips WHERE id = %s', (slip_id,))
        slip = cursor.fetchone()

        if slip is None:
            return "Slip not found", 404

        # Calculate Total Paid and Balance for print
        total_paid, balance_amount = calculate_payment_totals(slip)
        slip['total_paid_amount'] = total_paid
        slip['balance_amount'] = balance_amount

        # Format all datetime fields to IST for printing
        datetime_fields = ['date', 'payment_date', 'payment_due_date',
                          'instalment_1_date', 'instalment_2_date', 'instalment_3_date',
                          'instalment_4_date', 'instalment_5_date']

        for field in datetime_fields:
            if slip.get(field):
                slip[f'{field}_formatted'] = format_ist_datetime(slip[field])

        # Get logo path for the print template
        logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'desktop', 'assets', 'spslogo.png'))

        return render_template('print_template_new.html', slip=slip, logo_path=logo_path)

    except Exception as e:
        print(f"Error rendering print: {e}")
        return str(e), 400
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# UNLOADING GODOWN DYNAMIC DROPDOWN APIs

@slips_bp.route('/api/unloading-godowns', methods=['GET'])
def get_unloading_godowns():
    """Get all unloading godown names for dropdown"""
    print("\n" + "="*60)
    print("🔵 GET /api/unloading-godowns - Request received")
    print("="*60)

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute('''
            SELECT id, name
            FROM unloading_godowns
            ORDER BY name ASC
        ''')

        godowns = cursor.fetchall()

        print(f"✅ Fetched {len(godowns)} unloading godowns")
        if godowns:
            print(f"📋 Godown list: {[g['name'] for g in godowns]}")

        return jsonify({
            'success': True,
            'godowns': godowns
        }), 200

    except Exception as e:
        error_msg = f"Error fetching unloading godowns: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@slips_bp.route('/api/unloading-godowns', methods=['POST'])
def add_unloading_godown():
    """Add a new unloading godown (or return existing if duplicate)"""
    print("\n" + "="*60)
    print("🔵 POST /api/unloading-godowns - Request received")
    print("="*60)

    conn = None
    cursor = None
    try:
        data = request.get_json()
        print(f"📥 Request data: {data}")

        godown_name = data.get('name', '').strip()
        print(f"📝 Godown name: '{godown_name}'")

        if not godown_name:
            return jsonify({
                'success': False,
                'message': 'Godown name is required'
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Check if it already exists (MySQL uses %s placeholder)
        cursor.execute('SELECT id, name FROM unloading_godowns WHERE name = %s', (godown_name,))
        existing = cursor.fetchone()

        if existing:
            print(f"✓ Godown '{godown_name}' already exists")
            return jsonify({
                'success': True,
                'godown': {'id': existing['id'], 'name': existing['name']},
                'message': 'Godown already exists'
            }), 200

        # Insert new godown (MySQL uses %s placeholder)
        cursor.execute('INSERT INTO unloading_godowns (name) VALUES (%s)', (godown_name,))
        conn.commit()

        new_id = cursor.lastrowid
        print(f"✓ Added new godown: {godown_name} (ID: {new_id})")

        # Fetch all godowns to return updated list
        cursor.execute('SELECT id, name FROM unloading_godowns ORDER BY name ASC')
        all_godowns = cursor.fetchall()

        return jsonify({
            'success': True,
            'godown': {'id': new_id, 'name': godown_name},
            'godowns': all_godowns,
            'message': 'Godown added successfully'
        }), 201

    except Exception as e:
        error_msg = f"Error adding unloading godown: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==================== DASHBOARD API ====================

@slips_bp.route('/api/dashboard', methods=['GET'])
def get_dashboard_data():
    """Get comprehensive dashboard data with analytics"""
    print("\n" + "="*60)
    print("📊 GET /api/dashboard - Dashboard data request")
    print("="*60)

    conn = None
    cursor = None
    try:
        period = request.args.get('period', 'month')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Date filter based on period
        date_filter = ""
        if period == 'today':
            date_filter = "AND DATE(date) = CURDATE()"
        elif period == 'week':
            date_filter = "AND date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
        elif period == 'month':
            date_filter = "AND date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
        elif period == 'year':
            date_filter = "AND date >= DATE_SUB(CURDATE(), INTERVAL 365 DAY)"

        # ===== METRICS =====
        cursor.execute(f'''
            SELECT
                COALESCE(SUM(weight_quintal), 0) as totalPaddyQntl,
                COALESCE(SUM(total_purchase_amount), 0) as totalPurchaseAmount,
                COALESCE(SUM(total_deduction), 0) as totalDeductions,
                COALESCE(SUM(payable_amount), 0) as netPayable,
                COUNT(*) as totalBills
            FROM purchase_slips
            WHERE 1=1 {date_filter}
        ''')
        metrics = cursor.fetchone()

        # Calculate total paid from instalments
        cursor.execute(f'''
            SELECT COALESCE(SUM(
                COALESCE(instalment_1_amount, 0) +
                COALESCE(instalment_2_amount, 0) +
                COALESCE(instalment_3_amount, 0) +
                COALESCE(instalment_4_amount, 0) +
                COALESCE(instalment_5_amount, 0)
            ), 0) as totalPaid
            FROM purchase_slips
            WHERE 1=1 {date_filter}
        ''')
        paid_result = cursor.fetchone()
        metrics['totalPaid'] = paid_result['totalPaid']
        metrics['totalOutstanding'] = metrics['netPayable'] - metrics['totalPaid']

        # Average effective rate
        if metrics['totalPaddyQntl'] > 0:
            metrics['avgEffectiveRate'] = metrics['netPayable'] / metrics['totalPaddyQntl']
        else:
            metrics['avgEffectiveRate'] = 0

        # ===== DAILY PURCHASE TREND =====
        cursor.execute(f'''
            SELECT DATE(date) as purchase_date, SUM(weight_quintal) as total_qntl
            FROM purchase_slips
            WHERE 1=1 {date_filter}
            GROUP BY DATE(date)
            ORDER BY purchase_date
            LIMIT 30
        ''')
        daily_data = cursor.fetchall()
        daily_purchase = {
            'dates': [row['purchase_date'].strftime('%Y-%m-%d') if row['purchase_date'] else '' for row in daily_data],
            'quantities': [float(row['total_qntl']) if row['total_qntl'] else 0 for row in daily_data]
        }

        # ===== RATE TREND =====
        cursor.execute(f'''
            SELECT DATE(date) as purchase_date,
                   AVG(payable_amount / NULLIF(weight_quintal, 0)) as avg_rate
            FROM purchase_slips
            WHERE weight_quintal > 0 {date_filter}
            GROUP BY DATE(date)
            ORDER BY purchase_date
            LIMIT 30
        ''')
        rate_data = cursor.fetchall()
        rate_trend = {
            'dates': [row['purchase_date'].strftime('%Y-%m-%d') if row['purchase_date'] else '' for row in rate_data],
            'rates': [float(row['avg_rate']) if row['avg_rate'] else 0 for row in rate_data]
        }

        # ===== DEDUCTION BREAKDOWN =====
        cursor.execute(f'''
            SELECT
                SUM(moisture_ded) as moisture,
                SUM(quality_diff) as quality,
                SUM(dalali) as dalali,
                SUM(hammali) as hammali,
                SUM(bank_commission) as commission,
                SUM(freight) as freight
            FROM purchase_slips
            WHERE 1=1 {date_filter}
        ''')
        deduction_data = cursor.fetchone()
        deductions = {
            'labels': ['Moisture', 'Quality', 'Dalali', 'Hammali', 'Commission', 'Freight'],
            'amounts': [
                float(deduction_data['moisture']) if deduction_data['moisture'] else 0,
                float(deduction_data['quality']) if deduction_data['quality'] else 0,
                float(deduction_data['dalali']) if deduction_data['dalali'] else 0,
                float(deduction_data['hammali']) if deduction_data['hammali'] else 0,
                float(deduction_data['commission']) if deduction_data['commission'] else 0,
                float(deduction_data['freight']) if deduction_data['freight'] else 0
            ]
        }

        # ===== TOP SUPPLIERS =====
        cursor.execute(f'''
            SELECT party_name, SUM(weight_quintal) as total_qntl
            FROM purchase_slips
            WHERE party_name IS NOT NULL {date_filter}
            GROUP BY party_name
            ORDER BY total_qntl DESC
            LIMIT 10
        ''')
        supplier_data = cursor.fetchall()
        top_suppliers = {
            'names': [row['party_name'] for row in supplier_data],
            'quantities': [float(row['total_qntl']) if row['total_qntl'] else 0 for row in supplier_data]
        }

        # ===== OUTSTANDING AGEING =====
        cursor.execute(f'''
            SELECT
                SUM(CASE WHEN DATEDIFF(CURDATE(), date) <= 7 THEN (payable_amount -
                    (COALESCE(instalment_1_amount, 0) + COALESCE(instalment_2_amount, 0) +
                     COALESCE(instalment_3_amount, 0) + COALESCE(instalment_4_amount, 0) +
                     COALESCE(instalment_5_amount, 0))) ELSE 0 END) as age_0_7,
                SUM(CASE WHEN DATEDIFF(CURDATE(), date) > 7 AND DATEDIFF(CURDATE(), date) <= 30
                    THEN (payable_amount - (COALESCE(instalment_1_amount, 0) + COALESCE(instalment_2_amount, 0) +
                          COALESCE(instalment_3_amount, 0) + COALESCE(instalment_4_amount, 0) +
                          COALESCE(instalment_5_amount, 0))) ELSE 0 END) as age_7_30,
                SUM(CASE WHEN DATEDIFF(CURDATE(), date) > 30 AND DATEDIFF(CURDATE(), date) <= 60
                    THEN (payable_amount - (COALESCE(instalment_1_amount, 0) + COALESCE(instalment_2_amount, 0) +
                          COALESCE(instalment_3_amount, 0) + COALESCE(instalment_4_amount, 0) +
                          COALESCE(instalment_5_amount, 0))) ELSE 0 END) as age_30_60,
                SUM(CASE WHEN DATEDIFF(CURDATE(), date) > 60
                    THEN (payable_amount - (COALESCE(instalment_1_amount, 0) + COALESCE(instalment_2_amount, 0) +
                          COALESCE(instalment_3_amount, 0) + COALESCE(instalment_4_amount, 0) +
                          COALESCE(instalment_5_amount, 0))) ELSE 0 END) as age_60_plus
            FROM purchase_slips
            WHERE 1=1 {date_filter}
        ''')
        ageing_data = cursor.fetchone()
        ageing = {
            'amounts': [
                float(ageing_data['age_0_7']) if ageing_data['age_0_7'] else 0,
                float(ageing_data['age_7_30']) if ageing_data['age_7_30'] else 0,
                float(ageing_data['age_30_60']) if ageing_data['age_30_60'] else 0,
                float(ageing_data['age_60_plus']) if ageing_data['age_60_plus'] else 0
            ]
        }

        # ===== PAYMENT MODE SPLIT =====
        cursor.execute(f'''
            SELECT
                SUM(CASE WHEN instalment_1_payment_method = 'Cash' THEN instalment_1_amount ELSE 0 END +
                    CASE WHEN instalment_2_payment_method = 'Cash' THEN instalment_2_amount ELSE 0 END +
                    CASE WHEN instalment_3_payment_method = 'Cash' THEN instalment_3_amount ELSE 0 END +
                    CASE WHEN instalment_4_payment_method = 'Cash' THEN instalment_4_amount ELSE 0 END +
                    CASE WHEN instalment_5_payment_method = 'Cash' THEN instalment_5_amount ELSE 0 END) as cash_total,
                SUM(CASE WHEN instalment_1_payment_method = 'Online Transfer' THEN instalment_1_amount ELSE 0 END +
                    CASE WHEN instalment_2_payment_method = 'Online Transfer' THEN instalment_2_amount ELSE 0 END +
                    CASE WHEN instalment_3_payment_method = 'Online Transfer' THEN instalment_3_amount ELSE 0 END +
                    CASE WHEN instalment_4_payment_method = 'Online Transfer' THEN instalment_4_amount ELSE 0 END +
                    CASE WHEN instalment_5_payment_method = 'Online Transfer' THEN instalment_5_amount ELSE 0 END) as online_total,
                SUM(CASE WHEN instalment_1_payment_method = 'Cheque' THEN instalment_1_amount ELSE 0 END +
                    CASE WHEN instalment_2_payment_method = 'Cheque' THEN instalment_2_amount ELSE 0 END +
                    CASE WHEN instalment_3_payment_method = 'Cheque' THEN instalment_3_amount ELSE 0 END +
                    CASE WHEN instalment_4_payment_method = 'Cheque' THEN instalment_4_amount ELSE 0 END +
                    CASE WHEN instalment_5_payment_method = 'Cheque' THEN instalment_5_amount ELSE 0 END) as cheque_total
            FROM purchase_slips
            WHERE 1=1 {date_filter}
        ''')
        payment_mode_data = cursor.fetchone()
        payment_mode = {
            'modes': ['Cash', 'Online Transfer', 'Cheque'],
            'amounts': [
                float(payment_mode_data['cash_total']) if payment_mode_data['cash_total'] else 0,
                float(payment_mode_data['online_total']) if payment_mode_data['online_total'] else 0,
                float(payment_mode_data['cheque_total']) if payment_mode_data['cheque_total'] else 0
            ]
        }

        # ===== GODOWN STOCK =====
        cursor.execute(f'''
            SELECT
                COALESCE(paddy_unloading_godown, 'Unknown') as godown,
                SUM(weight_quintal) as total_stock
            FROM purchase_slips
            WHERE paddy_unloading_godown IS NOT NULL {date_filter}
            GROUP BY paddy_unloading_godown
            ORDER BY total_stock DESC
        ''')
        godown_data = cursor.fetchall()
        godown_stock = {
            'godowns': [row['godown'] for row in godown_data] if godown_data else ['No Data'],
            'quantities': [float(row['total_stock']) if row['total_stock'] else 0 for row in godown_data] if godown_data else [0]
        }

        # ===== OUTSTANDING BY FARMER =====
        cursor.execute(f'''
            SELECT
                party_name as farmerName,
                SUM(total_purchase_amount) as totalPurchase,
                SUM(COALESCE(instalment_1_amount, 0) + COALESCE(instalment_2_amount, 0) +
                    COALESCE(instalment_3_amount, 0) + COALESCE(instalment_4_amount, 0) +
                    COALESCE(instalment_5_amount, 0)) as totalPaid,
                SUM(payable_amount - (COALESCE(instalment_1_amount, 0) + COALESCE(instalment_2_amount, 0) +
                    COALESCE(instalment_3_amount, 0) + COALESCE(instalment_4_amount, 0) +
                    COALESCE(instalment_5_amount, 0))) as outstanding,
                MAX(GREATEST(
                    COALESCE(instalment_1_date, '1900-01-01'),
                    COALESCE(instalment_2_date, '1900-01-01'),
                    COALESCE(instalment_3_date, '1900-01-01'),
                    COALESCE(instalment_4_date, '1900-01-01'),
                    COALESCE(instalment_5_date, '1900-01-01')
                )) as lastPaymentDate,
                DATEDIFF(CURDATE(), MAX(date)) as daysOverdue
            FROM purchase_slips
            WHERE party_name IS NOT NULL {date_filter}
            GROUP BY party_name
            HAVING outstanding > 0
            ORDER BY outstanding DESC
            LIMIT 20
        ''')
        outstanding_farmers = cursor.fetchall()

        for farmer in outstanding_farmers:
            if farmer['lastPaymentDate']:
                last_date = farmer['lastPaymentDate']
                if isinstance(last_date, str):
                    if last_date != '1900-01-01':
                        farmer['lastPaymentDate'] = last_date
                    else:
                        farmer['lastPaymentDate'] = None
                else:
                    if str(last_date) != '1900-01-01':
                        farmer['lastPaymentDate'] = last_date.strftime('%Y-%m-%d')
                    else:
                        farmer['lastPaymentDate'] = None
            else:
                farmer['lastPaymentDate'] = None

        print(f"✅ Dashboard data retrieved successfully for period: {period}")

        return jsonify({
            'success': True,
            'metrics': metrics,
            'dailyPurchase': daily_purchase,
            'rateTrend': rate_trend,
            'deductions': deductions,
            'topSuppliers': top_suppliers,
            'ageing': ageing,
            'paymentMode': payment_mode,
            'godownStock': godown_stock,
            'outstanding': outstanding_farmers
        })

    except Exception as e:
        error_msg = f"Error fetching dashboard data: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': error_msg
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
