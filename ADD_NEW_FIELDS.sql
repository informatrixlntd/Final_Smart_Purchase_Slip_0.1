-- ============================================================================
-- SMART PURCHASE SLIP - DATABASE MIGRATION
-- Add new fields: moisture_percent, moisture_kg, company_gst_no, company_mobile_no
-- ============================================================================

-- Run this SQL file in your MySQL database to add the new columns

USE purchase_slips_db;

-- Add Moisture Percentage field
ALTER TABLE purchase_slips
ADD COLUMN IF NOT EXISTS moisture_percent DOUBLE DEFAULT 0
AFTER moisture_ded_comment;

-- Add Moisture KG field
ALTER TABLE purchase_slips
ADD COLUMN IF NOT EXISTS moisture_kg DOUBLE DEFAULT 0
AFTER moisture_percent;

-- Add Company GST Number field
ALTER TABLE purchase_slips
ADD COLUMN IF NOT EXISTS company_gst_no VARCHAR(255)
AFTER company_address;

-- Add Company Mobile Number field
ALTER TABLE purchase_slips
ADD COLUMN IF NOT EXISTS company_mobile_no VARCHAR(255)
AFTER company_gst_no;

-- Verify the columns were added successfully
SELECT 'Migration completed successfully!' AS Status;

-- Show all columns to verify
SHOW COLUMNS FROM purchase_slips;
