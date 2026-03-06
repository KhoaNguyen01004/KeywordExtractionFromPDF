-- Supabase Database Schema for Logistics Data Extraction System
-- Run this SQL in your Supabase SQL Editor to create the required tables

-- Table for extraction sessions
CREATE TABLE IF NOT EXISTS extraction_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'IN_PROGRESS',
    notes TEXT
);

-- Table for file uploads
CREATE TABLE IF NOT EXISTS file_uploads (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES extraction_sessions(session_id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    document_type VARCHAR(100),
    file_path TEXT,
    file_size INTEGER,
    extracted_data JSONB,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for extraction records
CREATE TABLE IF NOT EXISTS extraction_records (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES file_uploads(id) ON DELETE CASCADE,
    doc_type VARCHAR(100),
    bl_no VARCHAR(255),
    invoice_no VARCHAR(255),
    shipper TEXT,
    consignee TEXT,
    vessel VARCHAR(255),
    total_weight DECIMAL(10,2) DEFAULT 0,
    total_packages INTEGER DEFAULT 0,
    containers JSONB,
    hs_codes JSONB,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for validation records
CREATE TABLE IF NOT EXISTS validation_records (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) REFERENCES extraction_sessions(session_id) ON DELETE CASCADE,
    check_type VARCHAR(100),
    field_name VARCHAR(255),
    severity VARCHAR(50),
    message TEXT,
    status VARCHAR(50),
    expected_value TEXT,
    actual_values JSONB,
    recommendation TEXT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_extraction_sessions_session_id ON extraction_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_extraction_sessions_created_at ON extraction_sessions(created_at);
CREATE INDEX IF NOT EXISTS idx_file_uploads_session_id ON file_uploads(session_id);
CREATE INDEX IF NOT EXISTS idx_validation_records_session_id ON validation_records(session_id);
CREATE INDEX IF NOT EXISTS idx_validation_records_severity ON validation_records(severity);

-- Enable Row Level Security (RLS) if needed for security
-- ALTER TABLE extraction_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE file_uploads ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE extraction_records ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE validation_records ENABLE ROW LEVEL SECURITY;