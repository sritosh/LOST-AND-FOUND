-- ====================================================================
-- DATABASE SYSTEMS LAB PROJECT: CAMPUS LOST & FOUND SYSTEM
-- Team Members:
--   1. SRITOSH RATH (24BDS0001)
--   2. JAYANT SHARMA (24BAI0148)
--
-- File: queries.sql (Analytical & Operational SQL Queries for Lab Review)
-- ====================================================================

-- --------------------------------------------------------------------
-- 1. BASIC SELECTION & PROJECTION
-- --------------------------------------------------------------------

-- Q1.1: Retrieve all registered students in alphabetical order
SELECT student_id, name, email, phone, department 
FROM STUDENT 
ORDER BY name ASC;

-- Q1.2: Retrieve all items classified under 'Electronics' category
SELECT item_id, item_name, category, description, location 
FROM ITEM 
WHERE category = 'Electronics';

-- Q1.3: Search for items containing specific keyword (e.g. 'Card' or 'AirPods') using pattern matching
SELECT item_id, item_name, category, location 
FROM ITEM 
WHERE item_name LIKE '%Card%' OR description LIKE '%AirPods%';


-- --------------------------------------------------------------------
-- 2. MULTI-TABLE JOINS (INNER JOINS)
-- --------------------------------------------------------------------

-- Q2.1: List all currently pending lost items with the student's name, department and contact info
SELECT 
    l.lost_id,
    i.item_name,
    i.category,
    i.location AS lost_location,
    l.date_lost,
    l.status,
    s.student_id,
    s.name AS student_name,
    s.department,
    s.phone
FROM LOST_ITEM l
JOIN ITEM i ON l.item_id = i.item_id
JOIN STUDENT s ON l.student_id = s.student_id
WHERE l.status = 'Pending'
ORDER BY l.date_lost DESC;

-- Q2.2: List all found items along with finder information and physical storage desk
SELECT 
    f.found_id,
    i.item_name,
    i.category,
    i.location AS found_location,
    f.date_found,
    f.storage_location,
    f.status,
    s.name AS found_by_student,
    s.email AS finder_email
FROM FOUND_ITEM f
JOIN ITEM i ON f.item_id = i.item_id
JOIN STUDENT s ON f.student_id = s.student_id
ORDER BY f.date_found DESC;

-- Q2.3: List all claims submitted by students with item details and claim status
SELECT 
    c.claim_id,
    i.item_name,
    i.category,
    s.name AS claimant_name,
    s.student_id AS claimant_id,
    s.department,
    c.claim_date,
    c.claim_status,
    c.proof_description
FROM CLAIM c
JOIN ITEM i ON c.item_id = i.item_id
JOIN STUDENT s ON c.student_id = s.student_id
ORDER BY c.claim_date DESC;

-- Q2.4: List all successfully returned items with receiver student and verifying officer
SELECT 
    r.return_id,
    i.item_name,
    s.name AS owner_name,
    s.student_id AS owner_reg_no,
    r.return_date,
    r.verified_by,
    r.remarks
FROM RETURN_RECORD r
JOIN ITEM i ON r.item_id = i.item_id
JOIN STUDENT s ON r.student_id = s.student_id;


-- --------------------------------------------------------------------
-- 3. OUTER JOINS (LEFT / RIGHT JOINS)
-- --------------------------------------------------------------------

-- Q3.1: Find all items in the database that have NOT yet received any claims (LEFT JOIN + IS NULL)
SELECT 
    i.item_id,
    i.item_name,
    i.category,
    i.location
FROM ITEM i
LEFT JOIN CLAIM c ON i.item_id = c.item_id
WHERE c.claim_id IS NULL;

-- Q3.2: List all students and the number of items they have reported lost (including students with 0 reports)
SELECT 
    s.student_id,
    s.name,
    s.department,
    COUNT(l.lost_id) AS total_lost_reported
FROM STUDENT s
LEFT JOIN LOST_ITEM l ON s.student_id = l.student_id
GROUP BY s.student_id, s.name, s.department
ORDER BY total_lost_reported DESC;


-- --------------------------------------------------------------------
-- 4. AGGREGATE FUNCTIONS & GROUP BY / HAVING CLAUSES
-- --------------------------------------------------------------------

-- Q4.1: Count total items reported by category
SELECT 
    category, 
    COUNT(*) AS item_count 
FROM ITEM 
GROUP BY category 
ORDER BY item_count DESC;

-- Q4.2: Count of lost items grouped by current status
SELECT 
    status, 
    COUNT(*) AS count 
FROM LOST_ITEM 
GROUP BY status;

-- Q4.3: Departments where students have reported more than 1 item (HAVING clause)
SELECT 
    s.department,
    COUNT(i.item_id) AS total_items_involved
FROM STUDENT s
JOIN LOST_ITEM l ON s.student_id = l.student_id
JOIN ITEM i ON l.item_id = i.item_id
GROUP BY s.department
HAVING COUNT(i.item_id) >= 1;

-- Q4.4: Summary statistics KPI count query (Executive Dashboard metrics)
SELECT 
    (SELECT COUNT(*) FROM LOST_ITEM WHERE status = 'Pending') AS active_lost_items,
    (SELECT COUNT(*) FROM FOUND_ITEM WHERE status = 'Pending') AS active_found_items,
    (SELECT COUNT(*) FROM CLAIM WHERE claim_status = 'Pending') AS pending_claims,
    (SELECT COUNT(*) FROM RETURN_RECORD) AS total_returned_items;


-- --------------------------------------------------------------------
-- 5. SUBQUERIES (NESTED & CORRELATED QUERIES)
-- --------------------------------------------------------------------

-- Q5.1: Find students who have both reported a lost item AND reported a found item (IN Subquery)
SELECT student_id, name, email, department
FROM STUDENT
WHERE student_id IN (SELECT student_id FROM LOST_ITEM)
  AND student_id IN (SELECT student_id FROM FOUND_ITEM);

-- Q5.2: Find items that have been claimed and approved but not yet recorded in RETURN_RECORD (Subquery with NOT IN)
SELECT 
    c.claim_id,
    c.item_id,
    i.item_name,
    c.student_id,
    c.claim_date
FROM CLAIM c
JOIN ITEM i ON c.item_id = i.item_id
WHERE c.claim_status = 'Approved'
  AND c.item_id NOT IN (SELECT item_id FROM RETURN_RECORD);

-- Q5.3: Find students who have pending claims using EXISTS
SELECT s.student_id, s.name, s.email, s.phone
FROM STUDENT s
WHERE EXISTS (
    SELECT 1 FROM CLAIM c 
    WHERE c.student_id = s.student_id AND c.claim_status = 'Pending'
);


-- --------------------------------------------------------------------
-- 6. DATE RANGE & TEMPORAL QUERIES
-- --------------------------------------------------------------------

-- Q6.1: Items reported lost within a specified date window
SELECT 
    l.lost_id,
    i.item_name,
    l.date_lost,
    s.name AS reported_by
FROM LOST_ITEM l
JOIN ITEM i ON l.item_id = i.item_id
JOIN STUDENT s ON l.student_id = s.student_id
WHERE l.date_lost BETWEEN '2026-10-01' AND '2026-10-10'
ORDER BY l.date_lost DESC;


-- --------------------------------------------------------------------
-- 7. QUERIES USING DATABASE VIEWS
-- --------------------------------------------------------------------

-- Q7.1: View all active lost items from pre-defined view
SELECT * FROM vw_lost_items_detailed WHERE lost_status = 'Pending';

-- Q7.2: View all active found items from pre-defined view
SELECT * FROM vw_found_items_detailed WHERE found_status = 'Pending';

-- Q7.3: View claims overview
SELECT * FROM vw_claims_overview ORDER BY claim_date DESC;

-- Q7.4: View final returned items detailed view
SELECT * FROM vw_returns_detailed ORDER BY return_date DESC;


-- --------------------------------------------------------------------
-- 8. CAMPUS ANALYTICS & RECOVERY HOTSPOTS
-- --------------------------------------------------------------------

-- Q8.1: Campus Loss Hotspots - Locations with the highest reported missing items
SELECT 
    location,
    COUNT(*) AS total_lost_incidents,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ITEM), 2) AS percentage_of_campus_losses
FROM ITEM
GROUP BY location
ORDER BY total_lost_incidents DESC
LIMIT 5;

-- Q8.2: Campus Asset Recovery Rate (KPI Metric)
SELECT 
    (SELECT COUNT(*) FROM ITEM) AS total_campus_items,
    (SELECT COUNT(*) FROM RETURN_RECORD) AS total_returned_items,
    ROUND(
        ((SELECT COUNT(*) FROM RETURN_RECORD) * 100.0 / NULLIF((SELECT COUNT(*) FROM ITEM), 0)), 
        2
    ) AS campus_recovery_rate_pct;

-- Q8.3: Average settlement turnaround days between reporting and returning
SELECT 
    ROUND(AVG(JULIANDAY(r.return_date) - JULIANDAY(l.date_lost)), 1) AS avg_days_to_return
FROM RETURN_RECORD r
JOIN LOST_ITEM l ON r.item_id = l.item_id;


-- --------------------------------------------------------------------
-- 9. AUTOMATED SIMILARITY MATCHING (LOST <-> FOUND CORRELATION)
-- --------------------------------------------------------------------

-- Q9.1: Match Finder - Suggests potential found items for pending lost items
SELECT 
    l.lost_id,
    li.item_name AS lost_item,
    li.category,
    li.location AS lost_location,
    f.found_id,
    fi.item_name AS found_item,
    fi.location AS found_location,
    f.storage_location,
    CASE 
        WHEN li.category = fi.category AND li.location = fi.location THEN 'High Confidence (Category + Location)'
        WHEN li.category = fi.category THEN 'Medium Confidence (Category Match)'
        ELSE 'Low Confidence'
    END AS match_confidence
FROM LOST_ITEM l
JOIN ITEM li ON l.item_id = li.item_id
CROSS JOIN FOUND_ITEM f
JOIN ITEM fi ON f.item_id = fi.item_id
WHERE l.status = 'Pending' 
  AND f.status = 'Pending'
  AND li.category = fi.category
ORDER BY l.lost_id ASC;

