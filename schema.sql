-- Schema for the Lumora ICP Enrichment Engine.
-- This file was missing from the original package - db_operations.py
-- queries/updates a `leads` table that never had a corresponding CREATE TABLE
-- anywhere, so the app could not run against a fresh database.
--
-- Applied automatically on first container start via docker-compose
-- (mounted into /docker-entrypoint-initdb.d/). For a manual/local Postgres
-- install, run:  psql -U postgres -d lumora_icp -f schema.sql

CREATE TABLE IF NOT EXISTS leads (
    id                  SERIAL PRIMARY KEY,
    company_name        TEXT NOT NULL,
    website             TEXT,
    email               TEXT,
    phone               TEXT,
    employees           INTEGER,
    revenue             NUMERIC,
    location            TEXT,
    social_media        TEXT,

    -- Enrichment output fields written by database/db_operations.py
    industry             TEXT,
    business_model       TEXT,
    avg_customer_value   NUMERIC,
    growth_signals       JSONB,
    marketing_maturity   TEXT,
    current_ads          BOOLEAN DEFAULT FALSE,
    social_condition     TEXT,
    seo_condition         TEXT,
    enrichment_status    TEXT DEFAULT 'pending',
    processed_date       TIMESTAMP,

    created_date         TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Speeds up the "get unprocessed companies" query, which filters on industry
-- and orders by created_date.
CREATE INDEX IF NOT EXISTS idx_leads_industry ON leads (industry);
CREATE INDEX IF NOT EXISTS idx_leads_created_date ON leads (created_date);
CREATE INDEX IF NOT EXISTS idx_leads_enrichment_status ON leads (enrichment_status);

-- Seed a couple of rows so test_setup.py / a first run has something to do.
-- Safe to delete; guarded so re-running this file doesn't duplicate rows.
INSERT INTO leads (company_name, website, email, phone, employees, revenue, location, social_media)
SELECT * FROM (VALUES
    ('TechGrowth Solutions', 'techgrowth.com', 'ceo@techgrowth.com', '+1-555-123-4567', 150, 15000000, 'Austin, Texas', 'linkedin.com/techgrowth'),
    ('QuickBite Restaurant Group', 'quickbite.com', 'founder@quickbite.com', '+1-555-987-6543', 500, 50000000, 'Multiple Locations', 'facebook.com/quickbite')
) AS seed(company_name, website, email, phone, employees, revenue, location, social_media)
WHERE NOT EXISTS (SELECT 1 FROM leads);
