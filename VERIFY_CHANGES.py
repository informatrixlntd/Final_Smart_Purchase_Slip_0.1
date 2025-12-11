#!/usr/bin/env python
"""
Verification script to check if all code changes are properly implemented
"""

import os
import re

def check_file_contains(filepath, patterns, description):
    """Check if file contains all required patterns"""
    print(f"\nChecking: {description}")
    print(f"File: {filepath}")

    if not os.path.exists(filepath):
        print(f"  ❌ FILE NOT FOUND: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    all_found = True
    for pattern in patterns:
        if re.search(pattern, content, re.IGNORECASE):
            print(f"  ✓ Found: {pattern[:50]}...")
        else:
            print(f"  ❌ MISSING: {pattern[:50]}...")
            all_found = False

    return all_found

def main():
    print("="*70)
    print("SMART PURCHASE SLIP - CODE VERIFICATION")
    print("="*70)

    all_checks_passed = True

    # Check 1: Frontend Create Slip Form
    all_checks_passed &= check_file_contains(
        'frontend/index.html',
        [
            r'name="company_gst_no"',
            r'name="company_mobile_no"',
            r'name="moisture_percent"',
            r'name="moisture_kg"',
            r'name="moisture_ded_comment".*id="moisture_ded_comment"',
        ],
        "Frontend Create Slip Form - New Fields"
    )

    # Check 2: Desktop App Edit Modal
    all_checks_passed &= check_file_contains(
        'desktop/app.html',
        [
            r'id="edit_company_gst_no"',
            r'id="edit_company_mobile_no"',
            r'id="edit_avg_bag_weight"',
            r'id="edit_final_weight_kg"',
            r'id="edit_weight_quintal"',
            r'id="edit_weight_khandi"',
            r'id="edit_moisture_percent"',
            r'id="edit_moisture_kg"',
            r'id="edit_moisture_ded_comment"',
        ],
        "Desktop App Edit Modal - All Fields"
    )

    # Check 3: Desktop App View Modal
    all_checks_passed &= check_file_contains(
        'desktop/app.html',
        [
            r'Company GST No.*slip\.company_gst_no',
            r'Company Mobile No.*slip\.company_mobile_no',
            r'Moisture %.*slip\.moisture_percent',
            r'Moisture KG.*slip\.moisture_kg',
        ],
        "Desktop App View Modal - Display Fields"
    )

    # Check 4: Delete Confirmation Modal
    all_checks_passed &= check_file_contains(
        'desktop/app.html',
        [
            r'id="deleteConfirmModal"',
            r'id="deleteConfirmInput"',
            r'function confirmDelete\(\)',
            r'Type.*delete.*to confirm',
        ],
        "Desktop App - Delete Confirmation"
    )

    # Check 5: Backend Insert Query
    all_checks_passed &= check_file_contains(
        'backend/routes/slips.py',
        [
            r'company_gst_no.*company_mobile_no',
            r'moisture_percent.*moisture_kg',
            r"data\.get\('company_gst_no'",
            r"data\.get\('company_mobile_no'",
            r"data\.get\('moisture_percent'",
            r"data\.get\('moisture_kg'",
        ],
        "Backend API - Insert/Update Queries"
    )

    # Check 6: Database Schema
    all_checks_passed &= check_file_contains(
        'backend/database.py',
        [
            r"'moisture_percent'.*DOUBLE",
            r"'moisture_kg'.*DOUBLE",
            r"'company_gst_no'.*VARCHAR",
            r"'company_mobile_no'.*VARCHAR",
        ],
        "Backend Database - Schema Definition"
    )

    # Check 7: Print Template
    all_checks_passed &= check_file_contains(
        'backend/templates/print_template.html',
        [
            r'slip\.company_gst_no',
            r'slip\.company_mobile_no',
            r'slip\.moisture_percent',
            r'slip\.moisture_kg',
        ],
        "Print Template - New Fields Display"
    )

    # Check 8: WhatsApp Share
    all_checks_passed &= check_file_contains(
        'desktop/main.js',
        [
            r'PurchaseSlipWhatsApp',
            r'Documents.*PurchaseSlipWhatsApp',
        ],
        "WhatsApp Share - PDF Save Location"
    )

    # Check 9: Backup Directory
    all_checks_passed &= check_file_contains(
        'desktop/main.js',
        [
            r'smart_purchase_slip_backup',
            r'Documents.*smart_purchase_slip_backup',
        ],
        "Backup Flow - Save Directory"
    )

    # Check 10: Backup Module
    all_checks_passed &= check_file_contains(
        'desktop/backup.js',
        [
            r'smart_purchase_slip_backup',
            r'performBackupAndUpload',
        ],
        "Backup Module - Configuration"
    )

    print("\n" + "="*70)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED!")
        print("All code changes are properly implemented.")
    else:
        print("❌ SOME CHECKS FAILED!")
        print("Please review the missing items above and update the code.")
    print("="*70)

    print("\nNext steps:")
    print("1. Run database migration: python backend/database.py")
    print("2. Restart the application completely")
    print("3. Test all new features")
    print("\nFor detailed instructions, see SETUP_GUIDE.txt")

if __name__ == "__main__":
    main()
