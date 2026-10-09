-- ====================================================================
-- DATABASE SYSTEMS LAB PROJECT: CAMPUS LOST & FOUND SYSTEM
-- Team Members:
--   1. SRITOSH RATH (24BDS0001)
--   2. JAYANT SHARMA (24BAI0148)
--
-- File: schema.sql (DDL - Data Definition Language)
-- Target RDBMS: MySQL 8.0+ / MariaDB / SQLite compatible
-- ====================================================================

-- 1. Create Database (for MySQL environments)
-- CREATE DATABASE IF NOT EXISTS campus_lost_found;
-- USE campus_lost_found;

-- Drop tables in reverse dependency order to avoid FK constraint errors
DROP TABLE IF EXISTS RETURN_RECORD;
DROP TABLE IF EXISTS CLAIM;
DROP TABLE IF EXISTS FOUND_ITEM;
DROP TABLE IF EXISTS LOST_ITEM;
DROP TABLE IF EXISTS ITEM;
DROP TABLE IF EXISTS STUDENT;

-- ====================================================================
-- 1. STUDENT TABLE
-- Stores profile and contact details of registered college students
-- ====================================================================
CREATE TABLE STUDENT (
    student_id VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(15) NOT NULL,
    department VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_student PRIMARY KEY (student_id)
);

-- ====================================================================
-- 2. ITEM TABLE
-- Master entity for items reported on campus
-- ====================================================================
CREATE TABLE ITEM (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    location VARCHAR(150) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- 3. LOST_ITEM TABLE
-- Links a student reporting their lost item with status tracking
-- Status: 'Pending', 'Claimed', 'Returned', 'Cancelled'
-- ====================================================================
CREATE TABLE LOST_ITEM (
    lost_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(20) NOT NULL,
    item_id INTEGER NOT NULL UNIQUE,
    date_lost DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Claimed', 'Returned', 'Cancelled')),
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lost_student FOREIGN KEY (student_id) 
        REFERENCES STUDENT (student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_lost_item FOREIGN KEY (item_id) 
        REFERENCES ITEM (item_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

-- ====================================================================
-- 4. FOUND_ITEM TABLE
-- Links a student (finder) who discovered and reported an item
-- Status: 'Pending', 'Claimed', 'Returned'
-- ====================================================================
CREATE TABLE FOUND_ITEM (
    found_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(20) NOT NULL,
    item_id INTEGER NOT NULL UNIQUE,
    date_found DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Claimed', 'Returned')),
    storage_location VARCHAR(100) DEFAULT 'Campus Security / Lost & Found Desk',
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_found_student FOREIGN KEY (student_id) 
        REFERENCES STUDENT (student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_found_item FOREIGN KEY (item_id) 
        REFERENCES ITEM (item_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

-- ====================================================================
-- 5. CLAIM TABLE
-- Records ownership claim attempts made by students on found items
-- Claim Status: 'Pending', 'Approved', 'Rejected', 'Returned'
-- ====================================================================
CREATE TABLE CLAIM (
    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(20) NOT NULL,
    item_id INTEGER NOT NULL,
    claim_date DATE NOT NULL,
    claim_status VARCHAR(20) DEFAULT 'Pending' CHECK (claim_status IN ('Pending', 'Approved', 'Rejected', 'Returned')),
    proof_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_claim_student FOREIGN KEY (student_id) 
        REFERENCES STUDENT (student_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE,
    CONSTRAINT fk_claim_item FOREIGN KEY (item_id) 
        REFERENCES ITEM (item_id) 
        ON DELETE CASCADE 
        ON UPDATE CASCADE
);

-- ====================================================================
-- 6. RETURN_RECORD TABLE
-- Final settlement record logging when an item is officially returned
-- ====================================================================
CREATE TABLE RETURN_RECORD (
    return_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id VARCHAR(20) NOT NULL,
    item_id INTEGER NOT NULL UNIQUE,
    return_date DATE NOT NULL,
    verified_by VARCHAR(100) DEFAULT 'Campus Security Officer',
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_return_student FOREIGN KEY (student_id) 
        REFERENCES STUDENT (student_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE,
    CONSTRAINT fk_return_item FOREIGN KEY (item_id) 
        REFERENCES ITEM (item_id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);

-- ====================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ====================================================================
CREATE INDEX idx_student_email ON STUDENT (email);
CREATE INDEX idx_item_category ON ITEM (category);
CREATE INDEX idx_item_location ON ITEM (location);
CREATE INDEX idx_lost_status ON LOST_ITEM (status);
CREATE INDEX idx_found_status ON FOUND_ITEM (status);
CREATE INDEX idx_claim_status ON CLAIM (claim_status);

-- ====================================================================
-- DATABASE VIEWS (FOR CONVENIENT REPORTING & QUERIES)
-- ====================================================================

-- View 1: Complete details of all lost items with student details
CREATE VIEW vw_lost_items_detailed AS
SELECT 
    l.lost_id,
    l.date_lost,
    l.status AS lost_status,
    l.reported_at,
    i.item_id,
    i.item_name,
    i.category,
    i.description,
    i.location AS location_lost,
    s.student_id,
    s.name AS student_name,
    s.email AS student_email,
    s.phone AS student_phone,
    s.department
FROM LOST_ITEM l
JOIN ITEM i ON l.item_id = i.item_id
JOIN STUDENT s ON l.student_id = s.student_id;

-- View 2: Complete details of all found items with finder student details
CREATE VIEW vw_found_items_detailed AS
SELECT 
    f.found_id,
    f.date_found,
    f.status AS found_status,
    f.storage_location,
    f.reported_at,
    i.item_id,
    i.item_name,
    i.category,
    i.description,
    i.location AS location_found,
    s.student_id AS finder_id,
    s.name AS finder_name,
    s.email AS finder_email,
    s.phone AS finder_phone,
    s.department AS finder_department
FROM FOUND_ITEM f
JOIN ITEM i ON f.item_id = i.item_id
JOIN STUDENT s ON f.student_id = s.student_id;

-- View 3: Overview of claims with claimant and item details
CREATE VIEW vw_claims_overview AS
SELECT 
    c.claim_id,
    c.claim_date,
    c.claim_status,
    c.proof_description,
    c.created_at,
    i.item_id,
    i.item_name,
    i.category,
    i.location,
    s.student_id AS claimant_id,
    s.name AS claimant_name,
    s.email AS claimant_email,
    s.phone AS claimant_phone,
    s.department AS claimant_department
FROM CLAIM c
JOIN ITEM i ON c.item_id = i.item_id
JOIN STUDENT s ON c.student_id = s.student_id;

-- View 4: Return records with owner and item details
CREATE VIEW vw_returns_detailed AS
SELECT 
    r.return_id,
    r.return_date,
    r.verified_by,
    r.remarks,
    r.created_at,
    i.item_id,
    i.item_name,
    i.category,
    s.student_id AS receiver_id,
    s.name AS receiver_name,
    s.email AS receiver_email,
    s.phone AS receiver_phone,
    s.department AS receiver_dept
FROM RETURN_RECORD r
JOIN ITEM i ON r.item_id = i.item_id
JOIN STUDENT s ON r.student_id = s.student_id;
