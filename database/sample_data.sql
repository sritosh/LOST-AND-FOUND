-- ====================================================================
-- DATABASE SYSTEMS LAB PROJECT: CAMPUS LOST & FOUND SYSTEM
-- Team Members:
--   1. SRITOSH RATH (24BDS0001)
--   2. JAYANT SHARMA (24BAI0148)
--
-- File: sample_data.sql (DML - Data Manipulation Language)
-- Target RDBMS: MySQL / MariaDB / SQLite
-- ====================================================================

-- --------------------------------------------------------------------
-- 1. INSERT STUDENTS
-- --------------------------------------------------------------------
INSERT INTO STUDENT (student_id, name, email, phone, department) VALUES
('24BDS0001', 'Sritosh Rath', 'sritosh.rath2024@vitstudent.ac.in', '9876543210', 'Data Science'),
('24BAI0148', 'Jayant Sharma', 'jayant.sharma2024@vitstudent.ac.in', '9876543211', 'Artificial Intelligence'),
('24BCS0032', 'Ananya Mishra', 'ananya.mishra2024@vitstudent.ac.in', '9812345678', 'Computer Science'),
('24BEC0105', 'Rahul Varma', 'rahul.varma2024@vitstudent.ac.in', '9823456789', 'Electronics & Comm'),
('24BME0054', 'Priya Sundaram', 'priya.s2024@vitstudent.ac.in', '9834567890', 'Mechanical Engg'),
('24BIT0089', 'Karthik Raja', 'karthik.raja2024@vitstudent.ac.in', '9845678901', 'Information Tech'),
('24BDS0045', 'Sneha Patel', 'sneha.patel2024@vitstudent.ac.in', '9856789012', 'Data Science'),
('24BAI0092', 'Aditya Nair', 'aditya.nair2024@vitstudent.ac.in', '9867890123', 'Artificial Intelligence');

-- --------------------------------------------------------------------
-- 2. INSERT ITEMS (Master item catalog)
-- --------------------------------------------------------------------
INSERT INTO ITEM (item_name, category, description, location) VALUES
-- Item 1: Lost by Sritosh
('Student ID Card', 'Documents / Cards', 'VIT Student ID card with lanyard, blue holder', 'Central Library 2nd Floor'),
-- Item 2: Lost by Ananya
('Apple AirPods Pro 2', 'Electronics', 'White charging case with small dragon sticker', 'Food Court 1 (Gazebo)'),
-- Item 3: Lost by Rahul
('Casio FX-991EX Calculator', 'Stationery / Academic', 'Scientific calculator with engraved name RV on back', 'Main Building Room 304'),
-- Item 4: Lost by Priya
('Titan Metal Watch', 'Accessories', 'Silver analog dial with brown leather strap', 'Sports Complex Badminton Court'),
-- Item 5: Lost by Karthik
('MacBook Charger (67W)', 'Electronics', 'USB-C white adapter with braided cable', 'Tech Tower Lab 5'),

-- Item 6: Found by Jayant
('Boat Rockerz 450 Headphones', 'Electronics', 'Matte Black over-ear wireless headphones', 'Block A Auditorium Lobby'),
-- Item 7: Found by Sneha
('Steel Water Bottle (Milton)', 'Personal Belongings', 'Blue 1-litre insulated flask with scratch near cap', 'Hexagon Canteen Area'),
-- Item 8: Found by Aditya
('Campus RFID Gate Pass & Keys', 'Keys / Cards', 'Set of 3 keys with red Marvel keychain and hostel tag', 'Main Gate Security Gate 2'),
-- Item 9: Found by Sritosh
('Data Structures Notebook', 'Books / Notes', 'Hardbound 200 pages spiral notebook with DBMS notes', 'Library Reading Hall 1'),
-- Item 10: Found by Rahul
('Fastrack Wayfarer Sunglasses', 'Accessories', 'Black frame sunglasses inside hard zip case', 'Outdoor Amphitheater');

-- --------------------------------------------------------------------
-- 3. INSERT LOST ITEMS
-- --------------------------------------------------------------------
INSERT INTO LOST_ITEM (student_id, item_id, date_lost, status) VALUES
('24BDS0001', 1, '2026-10-02', 'Pending'),
('24BCS0032', 2, '2026-10-04', 'Pending'),
('24BEC0105', 3, '2026-10-05', 'Claimed'),
('24BME0054', 4, '2026-10-06', 'Returned'),
('24BIT0089', 5, '2026-10-07', 'Pending');

-- --------------------------------------------------------------------
-- 4. INSERT FOUND ITEMS
-- --------------------------------------------------------------------
INSERT INTO FOUND_ITEM (student_id, item_id, date_found, status, storage_location) VALUES
('24BAI0148', 6, '2026-10-03', 'Pending', 'Admin Block Security Office (Cabinet 2)'),
('24BDS0045', 7, '2026-10-04', 'Pending', 'Lost & Found Center, Desk A'),
('24BAI0092', 8, '2026-10-05', 'Pending', 'Main Security Post, Key Locker'),
('24BDS0001', 9, '2026-10-06', 'Claimed', 'Central Library Reception Desk'),
('24BEC0105', 10, '2026-10-07', 'Returned', 'Student Welfare Office Room 102');

-- --------------------------------------------------------------------
-- 5. INSERT CLAIMS
-- --------------------------------------------------------------------
INSERT INTO CLAIM (student_id, item_id, claim_date, claim_status, proof_description) VALUES
('24BCS0032', 6, '2026-10-05', 'Pending', 'My Boat headphones serial number matches and phone Bluetooth paired history is saved.'),
('24BEC0105', 3, '2026-10-06', 'Approved', 'The calculator has my initials "RV" carved with a compass on the rear battery lid.'),
('24BIT0089', 9, '2026-10-07', 'Approved', 'The notebook contains my handwriting, assignment submissions, and registration number on page 1.'),
('24BDS0001', 8, '2026-10-08', 'Pending', 'Keys for room 412 in Men Hostel Block D with red Marvel tag.');

-- --------------------------------------------------------------------
-- 6. INSERT RETURN RECORDS
-- --------------------------------------------------------------------
INSERT INTO RETURN_RECORD (student_id, item_id, return_date, verified_by, remarks) VALUES
('24BME0054', 4, '2026-10-08', 'Officer K. Raman', 'Student provided purchase invoice and photo ID matching the item description.'),
('24BEC0105', 10, '2026-10-09', 'Security Supervisor Suresh', 'Claim verified via optical prescription sticker on the case and student ID.');
