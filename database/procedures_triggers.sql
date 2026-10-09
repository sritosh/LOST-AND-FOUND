-- ====================================================================
-- DATABASE SYSTEMS LAB PROJECT: CAMPUS LOST & FOUND SYSTEM
-- Team Members:
--   1. SRITOSH RATH (24BDS0001)
--   2. JAYANT SHARMA (24BAI0148)
--
-- File: procedures_triggers.sql
-- Advanced Database Concepts: Stored Procedures & Triggers (MySQL)
-- ====================================================================

DELIMITER $$

-- --------------------------------------------------------------------
-- 1. STORED PROCEDURE: sp_report_lost_item
-- Atomically inserts an item into ITEM and links it in LOST_ITEM
-- --------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_report_lost_item$$
CREATE PROCEDURE sp_report_lost_item(
    IN p_student_id VARCHAR(20),
    IN p_item_name VARCHAR(150),
    IN p_category VARCHAR(50),
    IN p_description TEXT,
    IN p_location VARCHAR(150),
    IN p_date_lost DATE,
    OUT p_item_id INT,
    OUT p_lost_id INT
)
BEGIN
    -- Insert master item
    INSERT INTO ITEM (item_name, category, description, location)
    VALUES (p_item_name, p_category, p_description, p_location);
    
    SET p_item_id = LAST_INSERT_ID();
    
    -- Insert into LOST_ITEM
    INSERT INTO LOST_ITEM (student_id, item_id, date_lost, status)
    VALUES (p_student_id, p_item_id, p_date_lost, 'Pending');
    
    SET p_lost_id = LAST_INSERT_ID();
END$$


-- --------------------------------------------------------------------
-- 2. STORED PROCEDURE: sp_report_found_item
-- Atomically inserts an item into ITEM and links it in FOUND_ITEM
-- --------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_report_found_item$$
CREATE PROCEDURE sp_report_found_item(
    IN p_student_id VARCHAR(20),
    IN p_item_name VARCHAR(150),
    IN p_category VARCHAR(50),
    IN p_description TEXT,
    IN p_location VARCHAR(150),
    IN p_date_found DATE,
    IN p_storage_location VARCHAR(100),
    OUT p_item_id INT,
    OUT p_found_id INT
)
BEGIN
    INSERT INTO ITEM (item_name, category, description, location)
    VALUES (p_item_name, p_category, p_description, p_location);
    
    SET p_item_id = LAST_INSERT_ID();
    
    INSERT INTO FOUND_ITEM (student_id, item_id, date_found, status, storage_location)
    VALUES (p_student_id, p_item_id, p_date_found, 'Pending', p_storage_location);
    
    SET p_found_id = LAST_INSERT_ID();
END$$


-- --------------------------------------------------------------------
-- 3. STORED PROCEDURE: sp_process_claim_approval
-- Approves a claim and updates item status
-- --------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_process_claim_approval$$
CREATE PROCEDURE sp_process_claim_approval(
    IN p_claim_id INT,
    IN p_decision VARCHAR(20) -- 'Approved' or 'Rejected'
)
BEGIN
    DECLARE v_item_id INT;
    
    SELECT item_id INTO v_item_id FROM CLAIM WHERE claim_id = p_claim_id;
    
    -- Update claim status
    UPDATE CLAIM 
    SET claim_status = p_decision 
    WHERE claim_id = p_claim_id;
    
    IF p_decision = 'Approved' THEN
        -- Mark found item as Claimed
        UPDATE FOUND_ITEM 
        SET status = 'Claimed' 
        WHERE item_id = v_item_id;
        
        -- Reject other pending claims for the same item
        UPDATE CLAIM 
        SET claim_status = 'Rejected' 
        WHERE item_id = v_item_id AND claim_id != p_claim_id AND claim_status = 'Pending';
    END IF;
END$$


-- --------------------------------------------------------------------
-- 4. STORED PROCEDURE: sp_finalize_return
-- Creates return record and updates all statuses to 'Returned'
-- --------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_finalize_return$$
CREATE PROCEDURE sp_finalize_return(
    IN p_student_id VARCHAR(20),
    IN p_item_id INT,
    IN p_return_date DATE,
    IN p_verified_by VARCHAR(100),
    IN p_remarks TEXT
)
BEGIN
    -- 1. Insert Return Record
    INSERT INTO RETURN_RECORD (student_id, item_id, return_date, verified_by, remarks)
    VALUES (p_student_id, p_item_id, p_return_date, p_verified_by, p_remarks);
    
    -- 2. Update status in FOUND_ITEM if exists
    UPDATE FOUND_ITEM 
    SET status = 'Returned' 
    WHERE item_id = p_item_id;
    
    -- 3. Update status in LOST_ITEM if exists
    UPDATE LOST_ITEM 
    SET status = 'Returned' 
    WHERE item_id = p_item_id;
    
    -- 4. Update status in CLAIM table if approved
    UPDATE CLAIM 
    SET claim_status = 'Returned' 
    WHERE item_id = p_item_id AND claim_status = 'Approved';
END$$


-- --------------------------------------------------------------------
-- 5. TRIGGER: trg_prevent_duplicate_return
-- Ensures an item cannot be returned more than once
-- --------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_prevent_duplicate_return$$
CREATE TRIGGER trg_prevent_duplicate_return
BEFORE INSERT ON RETURN_RECORD
FOR EACH ROW
BEGIN
    DECLARE v_count INT;
    SELECT COUNT(*) INTO v_count FROM RETURN_RECORD WHERE item_id = NEW.item_id;
    IF v_count > 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Error: Item has already been returned and recorded.';
    END IF;
END$$

DELIMITER ;
